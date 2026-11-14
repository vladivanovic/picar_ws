"""Parsers for Wi-Fi link information. Pure functions, no ROS imports,
so they can be unit-tested with captured command output.

Primary source is ``iw dev <iface> link`` (the modern tool; iwconfig is
deprecated and not installed by default on current Ubuntu). Output looks
like:

    Connected to aa:bb:cc:dd:ee:ff (on wlan0)
        SSID: MyNetwork
        freq: 2437
        RX: 123456 bytes (1234 packets)
        TX: 12345 bytes (123 packets)
        signal: -52 dBm
        rx bitrate: 72.2 MBit/s
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class WifiLink:
    ssid: Optional[str] = None
    rssi_dbm: Optional[int] = None
    bssid: Optional[str] = None   # the specific AP radio we're associated with
    freq_mhz: Optional[int] = None

    @property
    def connected(self) -> bool:
        return self.ssid is not None


def parse_iw_link(output: str) -> WifiLink:
    """Parse ``iw dev <iface> link`` output."""
    if not output or 'Not connected' in output:
        return WifiLink()
    ssid = None
    rssi = None
    bssid = None
    freq = None
    first = re.search(r'Connected to ([0-9a-fA-F:]{17})', output)
    if first:
        bssid = first.group(1).lower()
    for line in output.splitlines():
        line = line.strip()
        if line.startswith('freq:'):
            m = re.search(r'(\d+)', line)
            if m:
                freq = int(m.group(1))
        elif line.startswith('SSID:'):
            ssid = line.split(':', 1)[1].strip() or None
        elif line.startswith('signal:'):
            match = re.search(r'(-?\d+)\s*dBm', line)
            if match:
                rssi = int(match.group(1))
    return WifiLink(ssid=ssid, rssi_dbm=rssi, bssid=bssid, freq_mhz=freq)


def parse_proc_wireless(output: str, interface: str = 'wlan0') -> WifiLink:
    """Fallback: parse /proc/net/wireless (link quality only, no SSID).

    Columns: interface | status | link quality | signal level (dBm) | noise.
    A signal level of 0 there means "unknown", reported as None.
    """
    for line in output.splitlines():
        if line.strip().startswith(interface + ':'):
            parts = line.replace(':', ' ', 1).split()
            # parts: [iface, status, quality., level., noise., ...]
            try:
                level = int(float(parts[3]))
            except (IndexError, ValueError):
                return WifiLink()
            return WifiLink(ssid=None, rssi_dbm=level if level != 0 else None)
    return WifiLink()
