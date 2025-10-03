#!/usr/bin/env python3

from pydbus.generic import signal
from pydbus import SessionBus
from gi.repository import GLib
loop = GLib.MainLoop()
dbus_filter = "/com/example/MyService"
bus = SessionBus()

def cb_server_signal_emission(*args):
    """
    Callback on emitting signal from server
    """
    print("Message: ", args)
    print("Data: ", str(args[4][0]))

if __name__=="__main__":
    # Subscribe to bus to monitor for server signal emissions
    bus.subscribe(object = dbus_filter, signal_fired = cb_server_signal_emission)
    loop.run()
 
