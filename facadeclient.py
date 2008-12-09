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

import gobject
import dbus
if getattr(dbus, 'version', (0,0,0)) >= (0,41,0):
    import dbus.glib # for signal handlers

STATUS_AVAILABLE = 2
STATUS_AWAY = 5

class FacadeClient(object):
    def __init__(self):
        self.setup()

    def setup(self):
        self.bus = dbus.SessionBus()

        # create purple object
        obj = self.bus.get_object('im.pidgin.purple.PurpleService', '/im/pidgin/purple/PurpleObject')
        self.purple = dbus.Interface(obj, 'im.pidgin.purple.PurpleInterface')

        # create face recognition object and add a callback for presence changes
        obj = self.bus.get_object('net.jozilla.Facade.FaceDetectionDaemon', '/Daemon')
        self.face_recog = dbus.Interface(obj,
                                         'net.jozilla.Facade.FaceDetectionDaemonInterface')
        self.face_recog.connect_to_signal('presence_changed', self.presence_changed_handler)

        # create new statuses
        self.available = self.purple.PurpleSavedstatusNew('At desk', STATUS_AVAILABLE)
        self.away = self.purple.PurpleSavedstatusNew('Away from desk', STATUS_AWAY)
        # these statuses might have existed already
        if self.available == 0: 
            self.available = self.purple.PurpleSavedstatusFind('At desk')        
        if self.away == 0:
            self.away = self.purple.PurpleSavedstatusFind('Away from desk')
        
        # set appropriate messages
        self.purple.PurpleSavedstatusSetMessage(self.available, "I am at my desk")
        # TODO: set time since last detection as well!    
        self.purple.PurpleSavedstatusSetMessage(self.away, "I haven't been at my desk since")

    def start(self):
        self.face_recog.start()

    def presence_changed_handler(self, presence, last_update):
        if presence:
            print 'Setting status to available', self.available
            self.purple.PurpleSavedstatusActivate(self.available)
        else:
            print 'Setting status to away', self.away
            msg = "I haven't been at my desk since %s" % last_update
            self.purple.PurpleSavedstatusSetMessage(self.away, msg)
            self.purple.PurpleSavedstatusActivate(self.away)

if __name__ == '__main__':
    c = FacadeClient()    
    print 'Calling start.'
    c.start()
    print 'Go!'

    mainloop = gobject.MainLoop()
    mainloop.run()

