import gobject
import dbus
if getattr(dbus, 'version', (0,0,0)) >= (0,41,0):
    import dbus.glib # for signal handlers

STATUS_AVAILABLE = 2
STATUS_AWAY = 5

class PresenceClient(object):
    def __init__(self):
        self.setup()

    def setup(self):
        self.bus = dbus.SessionBus()

        # create purple object
        obj = self.bus.get_object('im.pidgin.purple.PurpleService', '/im/pidgin/purple/PurpleObject')
        self.purple = dbus.Interface(obj, 'im.pidgin.purple.PurpleInterface')

        # create face recognition object and add a callback for presence changes
        obj = self.bus.get_object('net.jozilla.FoodBot.Presence.FaceDetectionDaemon', '/Daemon')
        self.face_recog = dbus.Interface(obj,
                                         'net.jozilla.FoodBot.Presence.FaceDetectionDaemonInterface')
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
    c = PresenceClient()    
    print 'Calling start.'
    c.start()
    print 'Go!'

    mainloop = gobject.MainLoop()
    mainloop.run()

