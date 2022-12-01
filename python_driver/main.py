from scapy.layers.inet import ICMPEcho_am

from scapy.all import *
if __name__ == "__main__":
    t = TunTapInterface('tun0')
    am = t.am(ICMPEcho_am)
    am()
