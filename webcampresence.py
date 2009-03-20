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

from datetime import datetime, timedelta
import time
from threading import Thread
import sys

import pygtk
pygtk.require('2.0')
import gtk
import gobject

from facedetection import FaceDetector

class webcamPresence(Thread):
    def __init__(self):
        self.setup()
        Thread.__init__(self)
        self.search_faces = False
        self.face_thread = None

    def setup(self):
        self.detector = FaceDetector(show_cam=False)
        self.present = True

    def run (self):
        """Start the loop that keeps tracking the user's face."""
        if self.search_faces == False:
            self.search_faces = True

        self.detect()

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

        # if we don't detect anything for 1 seconds, assume user is away
        away_treshold = timedelta(seconds=1)

        # eliminate false positives by requiring at least 15 detections
        # in a period of 5 seconds to allow the status to be changed
        # to available.
        fp_num = 15
        fp_duration = timedelta(seconds=5)
        fp_list = [last_time]
        fp_list[1:] = [datetime.fromtimestamp(0)] * (fp_num - 1)

        fi = 0
        self.present = False
        while self.search_faces:
            # detect a face/body
            (detected, is_face) = self.detector.fetch_and_detect()
            if detected:
                fi = fi + 1
                last_time = datetime.now()
                fp_list[fi % fp_num] = last_time

                if not self.present:
                    # possible switch to available
                    if fp_list[fi % fp_num] - fp_list[0] < fp_duration:
                        # we detected {fp_num} faces during the last 5 seconds
                        #print '%s - %s < %s' % (fp_list[fp_num-1], fp_list[0], fp_duration)
                        self.present = True
            else:
                if self.present:
                    # possible switch to away
                    if datetime.now() - last_time > away_treshold:
                        self.present = False

if __name__ == '__main__':
    
    bt = webcamPresence()   
    bt.start()

