import ctypes
import pyads
from ctypes import Structure, sizeof, c_ubyte
from dataclasses import dataclass, field
from typing import List, Tuple, Callable, Generic, TypeVar
import platform
import asyncio
from collections import OrderedDict

T = TypeVar('T')

@dataclass
class EventNotificator(Generic[T]):
    connection: pyads.Connection
    model: T
    subscriber: Callable
    symbol: str

    def __post_init__(self):
        try:
            if isinstance(self.model, tuple):
                size_of_struct = pyads.size_of_structure(self.model)
                attr = pyads.NotificationAttrib(size_of_struct)
                attr.trans_mode = pyads.ADSTRANS_SERVERONCHA
                attr.max_delay = 2500
                attr.cycle_time = 2500
                @self.connection.notification(c_ubyte * size_of_struct)
                def callback(handle, name, timestamp, value):
                    self.subscriber(value)
                self.connection.add_device_notification(self.symbol,
                                            attr,
                                            callback)
            else:
                attr = pyads.NotificationAttrib(ctypes.sizeof(self.model))
                attr.trans_mode = pyads.ADSTRANS_SERVERONCHA
                attr.max_delay = 2500
                attr.cycle_time = 2500
                tags = {self.symbol : pyads.PLCTYPE_ULINT}

                def callback(notification, data):
                    data_type = tags[data]
                    handle, timestamp, value = self.connection.parse_notification(notification, data_type)
                    self.subscriber(value)

                self.connection.add_device_notification(self.symbol,
                                            attr,
                                            callback)
        except pyads.pyads_ex.ADSError:
            print(f"Symbol not found: {self.symbol}")

class RouterConfiguration:
    target_host: str = '192.168.1.10'
    target_pc_name: str = ''
    local_ams_id: str = '127.0.0.1.1.1'
    route_name: str = 'training-ngy8'
    login_user: str = 'Administrator'
    login_password: str = '1'


@dataclass
class AdsCommunication:
    ams_net_id: str = field(default='127.0.0.1.1.1')
    ads_port: int = field(default=851, init=True)
    event_notificators: List[EventNotificator] = field(default_factory=list, init=False)
    connection: pyads.Connection = field(default=None, init=False)
    symbols :List[pyads.symbol.AdsSymbol] = field(default_factory=list, init=False)

    def __post_init__(self):
        self.add_route()
        self.connection = pyads.Connection(self.ams_net_id, self.ads_port)
        self.connection.open()
        #self.symbols = self.connection.get_all_symbols()
        for symbol in self.symbols:
            print(symbol.name)

    def add_route(self):
        if platform.system() != 'Linux':
            return
        pyads.open_port()
        pyads.set_local_address(RouterConfiguration.local_ams_id)
        pyads.add_route_to_plc(RouterConfiguration.local_ams_id,
                               RouterConfiguration.target_pc_name,
                               RouterConfiguration.target_host,
                               RouterConfiguration.login_user,
                               RouterConfiguration.login_password,
                               route_name=RouterConfiguration.route_name)
        pyads.close_port()


    def reg_notification(self,symbol: str, model: tuple, subscriber: Callable):
        self.event_notificators.append(
            EventNotificator[tuple](
                connection=self.connection,
                model=model,
                subscriber=subscriber,
                symbol=symbol
            )
        )

    def write(self,symbol: str, value, type):
        self.connection.write_by_name(symbol, value, type)


@dataclass
class EventReporter:
    plc : AdsCommunication = field(default=None, init=True)
    mapping_structure : Tuple[Tuple] = field(default_factory=Tuple, init=True)
    mapping_symbol : str = field(default_factory=str, init=True)
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    last_data : OrderedDict = field(default=None)

    def __post_init__(self):
        # 監視したい変数とデータ構造を定義したtupleを登録
        self.plc.reg_notification(self.mapping_symbol, self.mapping_structure,  self.job_event_handler)

    def job_event_handler(self, value):

        data = pyads.dict_from_bytes(value, self.mapping_structure)
        self.queue.put_nowait(data)

