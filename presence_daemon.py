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

from facedetection import FaceDetector

class Daemon(dbus.service.Object):
    def __init__(self, bus_name, object_path="/Daemon"):
        dbus.service.Object.__init__(self, bus_name, object_path)
        self.setup()
        self.search_faces = False
        self.face_thread = None

    def setup(self):
        self.detector = FaceDetector(show_cam=True)

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.status_icon = gtk.StatusIcon()
        self.status_icon.set_from_file('available.png')
        self.status_icon.set_tooltip('Available')
        self.status_icon.set_visible(True)

        pynotify.init('Face detection daemon')

        self.status_toggle = True

    @dbus.service.method('net.jozilla.FoodBot.Presence.FaceDetectionDaemonInterface')
    def start(self):
        """Start the loop that keeps tracking the user's face."""
        if self.search_faces == False:
            self.search_faces = True

        # start a new thread to handle face detection
        self.face_thread = Thread(target=self.detect)
        self.face_thread.start()

    @dbus.service.method('net.jozilla.FoodBot.Presence.FaceDetectionDaemonInterface')
    def stop(self):
        self.search_faces = False

        # stop the face detection thread (if running)
        if self.face_thread != None:
            self.face_thread.join()
            self.face_thread = None

    def detect(self):
        # remember the number of seconds since we last detected a
        # face, and assume we detected one at the start        
        last_time = datetime.now() 

        # if we don't detect anything for 10 seconds, assume user is away
        away_treshold = timedelta(seconds=10)

        # eliminate false positives by requiring at least 25 detections
        # in a period of 5 seconds to allow the status to be changed
        # to available.
        fp_num = 25
        fp_duration = timedelta(seconds=5)
        fp_list = [last_time]
        fp_list[1:] = [datetime.fromtimestamp(0)] * (fp_num - 1)

        fi = 0
        at_desk = False
        while self.search_faces:
            # detect a face/body
            (detected, is_face) = self.detector.fetch_and_detect()
            if detected:
                fi = fi + 1
                last_time = datetime.now()
                fp_list[fi % fp_num] = last_time

                if not at_desk:
                    # possible switch to available
                    if fp_list[fi % fp_num] - fp_list[0] < fp_duration:
                        # we detected {fp_num} faces during the last 5 seconds
                        print '%s - %s < %s' % (fp_list[fp_num-1], fp_list[0], fp_duration)
                        at_desk = True
            else:
                if at_desk:
                    # possible switch to away
                    if datetime.now() - last_time > away_treshold:
                        at_desk = False

            if at_desk:
                print 'at desk'
            else:
                print 'away'
            
            self.show_presence(at_desk, last_time)

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
        name = dbus.service.BusName('net.jozilla.FoodBot.Presence.FaceDetectionDaemon',
                                    bus=session_bus)
        obj = Daemon(name)

        # run the mainloop
        mainloop = gobject.MainLoop()
        mainloop.run()
    except KeyboardInterrupt:
        obj.stop()
        sys.exit(1)
                    
            
