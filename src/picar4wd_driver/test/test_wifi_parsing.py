"""Unit tests for the Wi-Fi parsers (pure Python, no ROS).

Run locally without a ROS install:
    cd src/picar4wd_driver && python3 -m pytest test/test_wifi_parsing.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from picar4wd_driver.wifi_parsing import parse_iw_link, parse_proc_wireless  # noqa: E402

IW_CONNECTED = """Connected to aa:bb:cc:dd:ee:ff (on wlan0)
    SSID: MunakataHome
    freq: 2437
    RX: 123456 bytes (1234 packets)
    TX: 12345 bytes (123 packets)
    signal: -52 dBm
    rx bitrate: 72.2 MBit/s
"""

PROC_WIRELESS = """Inter-| sta-|   Quality        |   Discarded packets               | Missed | WE
 face | tus | link level noise |  nwid  crypt   frag  retry   misc | beacon | 22
 wlan0: 0000   70.  -35.  -256        0      0      0      0      0        0
"""


def test_iw_connected():
    link = parse_iw_link(IW_CONNECTED)
    assert link.connected
    assert link.ssid == 'MunakataHome'
    assert link.rssi_dbm == -52
    assert link.bssid == 'aa:bb:cc:dd:ee:ff'
    assert link.freq_mhz == 2437


def test_iw_not_connected():
    link = parse_iw_link('Not connected.\n')
    assert not link.connected
    assert link.ssid is None
    assert link.rssi_dbm is None


def test_iw_empty():
    assert not parse_iw_link('').connected


def test_proc_wireless():
    link = parse_proc_wireless(PROC_WIRELESS, 'wlan0')
    assert link.rssi_dbm == -35


def test_proc_wireless_missing_interface():
    assert parse_proc_wireless(PROC_WIRELESS, 'wlan9').rssi_dbm is None
