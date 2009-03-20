#! /usr/bin/env python
#
# Facade -- Detect presence automatically with a webcam.
# Copyright (C) 2008  Jo Vermeulen
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#
# Author: Kristof Bamps <kristof.bamps@student.uhasselt.be>

import time
import threading
from datetime import datetime, timedelta

from Xlib import X, display
from Xlib.ext import record
from Xlib.protocol import rq

class hookPresence(threading.Thread):

    def __init__(self):
        self.keyboardLastUsed =  datetime.now()
        self.mouseLastUsed = datetime.now()
        threading.Thread.__init__(self)       
        self.contextEventMask = [0,2]
        
        # Hook to our display.
        self.record = display.Display()
        # Hook the devices we want to use
        self.HookKeyboard()
        self.HookMouse()
        
    def run(self):
        # Create a recording context; we only want key and mouse events
        self.ctx = self.record.record_create_context(
                0,
                [record.AllClients],
                [{
                        'core_requests': (0, 0),
                        'core_replies': (0, 0),
                        'ext_requests': (0, 0, 0, 0),
                        'ext_replies': (0, 0, 0, 0),
                        'delivered_events': (0, 0),
                        'device_events': tuple(self.contextEventMask), #(X.KeyPress, X.ButtonPress),
                        'errors': (0, 0),
                        'client_started': False,
                        'client_died': False,
                }])

        self.record.record_enable_context(self.ctx, self.processevents)
        self.record.record_free_context(self.ctx)

    def HookKeyboard(self):
        self.contextEventMask[0] = X.KeyPress
    
    def HookMouse(self):
        self.contextEventMask[1] = X.MotionNotify
    
    def processevents(self, reply):
        if reply.category != record.FromServer:
            return
        if reply.client_swapped:
            return
        if not len(reply.data) or ord(reply.data[0]) < 2:
            # not an event
            return
        data = reply.data
        while len(data) != 0:
            event, data = rq.EventField(None).parse_binary_value(data, self.record.display, None, None)
            if event.type == X.KeyPress:
                hookevent = self.keyboardUsed()
            elif event.type == X.ButtonPress:
                hookevent = self.mouseUsed()
            elif event.type == X.MotionNotify:
                hookevent = self.mouseUsed()
    def keyboardUsed(self):
        self.keyboardLastUsed =  datetime.now()

    def mouseUsed(self):
        self.mouseLastUsed =  datetime.now()

    def mousePresent(self):
        if  datetime.now() - self.mouseLastUsed< timedelta(seconds=1):
            return True
        else:
            return False
    def keyboardPresent(self):
        if  datetime.now() - self.keyboardLastUsed< timedelta(seconds=1):
            return True
        else:
            return False
    
if __name__ == '__main__':
    hm = hookPresence()
    hm.HookKeyboard()
    hm.HookMouse()
    hm.start()
