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

import dbus
import dbus.service
if getattr(dbus, 'version', (0,0,0)) >= (0,41,0):
    import dbus.glib # for signal handlers
import gobject

from datetime import datetime, timedelta
from threading import Thread
import sys

import pygtk
pygtk.require('2.0')
import gtk
import pynotify

from webcampresence import webcamPresence
from hookpresence import hookPresence

class FacadeDaemon(dbus.service.Object):
    def __init__(self, bus_name, object_path="/Daemon"):
        dbus.service.Object.__init__(self, bus_name, object_path)
        self.loop = False
        self.setup()

    def setup(self):
        self.webcam = webcamPresence()
        self.hook = hookPresence()
        self.devices = { 'mouse': False, 
                         'keyboard': False, 
                         'webcam': False }

        self.status_icon = gtk.StatusIcon()
        self.status_icon.set_from_file('available.png')
        self.status_icon.set_tooltip('Available')
        self.status_icon.set_visible(True)

        pynotify.init('Facade')

        self.status_toggle = True

    @dbus.service.method('net.jozilla.Facade.FaceDetectionDaemonInterface')
    def start(self):
        """Start the loop that keeps tracking the user's face."""

        # start a new thread to handle face detection
        self.webcam_thread = self.webcam.start()
        self.hook_thread = self.hook.start()

        self.loop = True 
        self.detect_thread = Thread(target=self.detect)
        self.detect_thread.start()

    @dbus.service.method('net.jozilla.Facade.FaceDetectionDaemonInterface')
    def stop(self):
        self.loop = False

        # stop the detection thread (if running)
        if self.detect_thread != None:
            self.detect_thread.join()
            self.detect_thread = None

    def detect(self):
        # If we don't detect anything for 10 seconds, assume the user
        # is away.
        last_time = datetime.now()
        away_treshold = timedelta(seconds=10)

        while self.loop:
            self.devices['keyboard'] = self.hook.keyboardPresent()
            self.devices['mouse'] = self.hook.mousePresent()
            self.devices['webcam'] = self.webcam.present

            if True in self.devices.values():
                last_time = datetime.now() 
                self.show_presence(True, last_time)
                print 'available >', self.devices
            else:
                if datetime.now() - last_time > away_treshold:
                    self.show_presence(False, last_time)

                print 'away for', (datetime.now() - last_time), '>', self.devices

    @dbus.service.signal('net.jozilla.FoodBot.Presence.FaceDetectionDaemonInterface')
    def presence_changed(self, presence, last_update):
        """This signal is emitted when the user's presence changes."""
        pass # the signal is emitted when this method exits

    def show_presence(self, available, last_time):
        strstatus = ''
        if available:
            self.status_icon.set_from_file('available.png')
            strstatus = 'available'
            self.status_icon.set_tooltip(strstatus.capitalize())            
        else:
            self.status_icon.set_from_file('away.png')
            strstatus = 'away'            
            self.status_icon.set_tooltip(strstatus.capitalize())

        if self.status_toggle != available:
            # switch occured
            title = 'Presence change'
            body = 'You are now <b>%s</b>.' % strstatus 
            note = pynotify.Notification(title, body)
            note.attach_to_status_icon(self.status_icon)
            note.set_urgency(pynotify.URGENCY_NORMAL)
            note.set_timeout(pynotify.EXPIRES_DEFAULT)
            note.show()

            # calculate relative time since last detection
            if last_time.day == datetime.now().day:
                last_time_str = last_time.strftime("%H:%M")
            elif last_time.day + timedelta(days=1) == datetime.now().day:
                last_time_str = last_time.strftime("yesterday at %H:%M")
            else:
                last_time_str = last_time.strftime("%A at %H:%M")

            # emit signal                
            self.presence_changed(available, last_time_str)
            
        self.status_toggle = available


if __name__ == "__main__":
    try:
        # needed to support thread
        gobject.threads_init()
        dbus.glib.init_threads()

        # setup the DBUS service
        session_bus = dbus.SessionBus()
        name = dbus.service.BusName('net.jozilla.Facade.FaceDetectionDaemon',
                                    bus=session_bus)
        obj = FacadeDaemon(name)

        # run the mainloop
        mainloop = gobject.MainLoop()
        mainloop.run()
    except KeyboardInterrupt:
        obj.stop()
        sys.exit(1)
                    
            
