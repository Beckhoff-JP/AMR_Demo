# AMR demo

このプロジェクトはTwinCAT 3.1 build 4026に対応したAMRデモです。次の特徴があります。

## 安全対応

* TwinSAFE/SCで収集した外部エンコーダの値とモータの内臓エンコーダを冗長監視する事で、安全エンコーダ無しにPLdを実現します。
* SafeMotionを備えたEL7211のSLSにより、LiDARの近接センサによるオーバライド速度設定を低速に制御します。
* ただし、付属するモータは安全エンコーダではないため、オーバライド速度の指令は非安全コントローラによる制御です。
* 代わりに上記冗長エンコーダによって指令速度異常を検出するとSTOが働き安全状態を確保します。

## TwinCAT/BSDとLinuxによるナビゲーション

AMRのナビゲーションで良く用いられるROS等が搭載可能なLinuxをゲストOSとしてbehyveハイパーバイザーを搭載したTwinCAT/BSD上で動作します。

HMIはTwinCAT/BSD上のnginxがホストするTF1810（PLC HMI Web）により提供され、X.orgとxfceウィンドウシステム上で稼働するブラウザによって画面表示を提供します。詳しくは下記をご覧ください。

* [テクニカルノート TwinCAT BSDのセットアップ手順](https://beckhoff-jp.github.io/TwinCATHowTo/tcbsd/index.html)

## Pythonによる音声ガイダンス機能

pyadsによりTwinCAT内のPLCの変数の値変化をNotificationにより受信し、[pydub](https://pypi.org/project/pydub/) によりMP3ファイルをnumpy配列へ変換し、 [sounddevice](https://pypi.org/project/sounddevice/) により音声を再生します。
前述の [テクニカルノート TwinCAT BSDのセットアップ手順](https://beckhoff-jp.github.io/TwinCATHowTo/tcbsd/index.html) により設定されたxfce上のサウンド設定によって音量調整が可能です。

このスクリプトは、 [TwinCATのEvent loggerを用いたライブラリ](https://github.com/Beckhoff-JP/MachineAlarmManagement) を使って、イベントを発行するたびにEventIDに応じたmp3音声ファイルを再生するPythonスクリプトを同梱しています。

"""
python_sound/twincatsound/tc_alarm_sound.py
"""

このスクリプトは、TwinCAT/BSD上からその上位ディレクトリにある twincatsound.sh を実行する事で起動します。

