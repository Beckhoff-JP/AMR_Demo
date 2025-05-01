import asyncio
from dataclasses import dataclass, field
from ads_communication import AdsCommunication, EventReporter
from datetime import datetime
import time
from model import alarm_structure
from typing import Callable, Tuple
import numpy as np
from pydub import AudioSegment
import sounddevice as sd

#fs = 44100 #普通41000Hzか48000Hz
#sd.default.samplerate = fs

class TwinCATTime:
    EPOCH_AS_FILETIME = 116444736000000000  # January 1, 1970 as MS file time
    DC_BASETIME = datetime(year=2000,month=1,day=1,hour=0,minute=0,second=0)
    EPOCH_AS_DCTIME = 0 - (int(time.mktime(DC_BASETIME.timetuple()) * 1000) + int(DC_BASETIME.microsecond / 1000))  * 10000000 # January 1, 1970 as DC time(ns)
    HUNDREDS_OF_NANOSECONDS = 10000000
    NANOSECONDS = 1000000000


    @classmethod
    def get_dc_time_h32(cls) -> int:
        now = datetime.now()
        ns_now = (int(time.mktime(now.timetuple()) * 1000) + int(now.microsecond / 1000))  * 10000000
        dctime_now = ns_now - cls.EPOCH_AS_DCTIME
        h_32bit = dctime_now & 0xffffffff00000000
        return h_32bit



    @classmethod
    def filetime_to_dt(cls, ft):
        """Converts a Microsoft filetime number to a Python datetime. The new datetime object is time zone-naive but is equivalent to tzinfo=utc.

        >>> filetime_to_dt(116444736000000000)
        datetime.datetime(1970, 1, 1, 0, 0)
        """
        # Get seconds and remainder in terms of Unix epoch
        (s, ns100) = divmod(ft - cls.EPOCH_AS_FILETIME, cls.HUNDREDS_OF_NANOSECONDS)
        # Convert to datetime object
        dt = datetime.utcfromtimestamp(s)
        # Add remainder in as microseconds. Python 3.2 requires an integer
        dt = dt.replace(microsecond=(ns100 // 10))
        return dt

    @classmethod
    def dctime_to_dt(cls, ft):
        # Get seconds and remainder in terms of Unix epoch
        (s, ns) = divmod(ft - cls.EPOCH_AS_DCTIME, cls.NANOSECONDS)
        # Convert to datetime object
        dt = datetime.utcfromtimestamp(s)
        # Add remainder in as microseconds. Python 3.2 requires an integer
        dt = dt.replace(microsecond=(ns // 1000))
        return dt

@dataclass
class TwinCATObserver:
    observer_method : Callable
    connection: AdsCommunication
    model : Tuple[Tuple]
    symbol : str
    task_wait_time : float = field(default=0, init=True)

    def __post_init__(self):
        self.event_handler = EventReporter(plc=self.connection,
                                         mapping_structure=self.model,
                                         mapping_symbol=self.symbol)

    async def listener(self):
        while True:
            if self.event_handler.queue.qsize() > 0:
                data = await self.event_handler.queue.get()
                self.observer_method(data)
            elif self.task_wait_time > 0:
                await asyncio.sleep(self.task_wait_time)


@dataclass
class application:
    subscriber_task : TwinCATObserver = field(default=None)

    def __post_init__(self):
        self.subscribe()

    def _sing_from_mp3(self, file):
        print(file)
        song = AudioSegment.from_mp3(file)
        song_array = np.array(song.get_array_of_samples())
        sd.play(song_array,  song.frame_rate)
        sd.wait()

    def alarm_event_subscriber(self, data):
        print(data)
        self._sing_from_mp3('sound/jingle.mp3') 
        self._sing_from_mp3(f"sound/{data['nEventId']}.mp3")



    def subscribe(self):
        plc_connector = AdsCommunication(ams_net_id='127.0.0.1.1.1', ads_port=851)

        self.subscriber_task = TwinCATObserver(observer_method=self.alarm_event_subscriber,
                                                          connection=plc_connector,
                                                          model=alarm_structure,
                                                          symbol='AlarmManager.event_iot_exporter.export_event',
                                                          task_wait_time=0.1
                                                          )





if __name__ == '__main__':
    app = application()
    asyncio.run(app.subscriber_task.listener())

