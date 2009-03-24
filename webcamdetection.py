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

from CVtypes import cv

class WebcamDetector:
    def __init__(self, resolution=(640,480), show_cam=False):
        self.setup(resolution, show_cam)

    def __del__(self):
        # release the capture device
        cv.ReleaseCapture(self.capture)
        if self.show_cam:
            # destroy the camera window
            cv.DestroyWindow('Camera')
        pass

    def setup(self, (width, height), show_cam):
        """Setup the webcam device and different windows."""
        device = 0 # assume we want the first device
        capture = cv.CreateCameraCapture(0)

        # set the width/height of the captured image
        # this won't work on Windows (*sigh*)
        cv.SetCaptureProperty(capture, cv.CAP_PROP_FRAME_WIDTH, width)
        cv.SetCaptureProperty(capture, cv.CAP_PROP_FRAME_HEIGHT, height)

        # get the width/height of the captured image
        # this won't work on Windows (*sigh*)
        self.width = cv.GetCaptureProperty(capture, cv.CAP_PROP_FRAME_WIDTH)
        self.height = cv.GetCaptureProperty(capture, cv.CAP_PROP_FRAME_HEIGHT)

        if self.width == 0 and self.height == 0: # Windows
            self.width, self.height = 320,240 # set to default

        # check if capture device is OK
        if not capture:
            print "Error opening capture device"

        self.capture = capture

        self.show_cam = show_cam
        if self.show_cam:
            cv.NamedWindow('Camera', cv.WINDOW_AUTOSIZE)

    def fetch_and_detect(self):
        frame = cv.QueryFrame(self.capture)
        
        if frame is None:
            print 'Could not get frame'
            return

        cv.Flip(frame, None, 1)

        # detection
        tpl = self.detect(frame) # = (detected something?)

        # update webcam image
        if self.show_cam:
            cv.ShowImage('Camera', frame)

        return tpl 

    def detect(self, image):
        pass

class FaceDetector(WebcamDetector):
    def __init__(self, resolution=(640,480), show_cam=False):
        self.setup(resolution, show_cam)

    def setup(self, (width, height), show_cam):
        """Setup the cascades."""
        WebcamDetector.setup(self, (width, height), show_cam)
        # set default face size and body size, according to the camera resolution.
        ratio = (640 / self.width)
        face_axis = int(50 / ratio)
        body_axis = int(125 / ratio)
        print (face_axis, body_axis)
        self.face_size = cv.Size(face_axis, face_axis)
        self.body_size = cv.Size(body_axis, body_axis)

        # load cascades
        self.face_cascade = cv.LoadHaarClassifierCascade('haarcascade_frontalface_alt.xml',
                                                         cv.Size(1,1))
        self.body_cascade = cv.LoadHaarClassifierCascade('haarcascade_upperbody.xml',
                                                         cv.Size(1,1))
    def detect(self, image):
        size = cv.GetSize(image)

        # create grayscale version
        grayscale = cv.CreateImage(size, 8, 1)
        cv.CvtColor(image, grayscale, cv.BGR2GRAY)

        # create and clear storage
        storage = cv.CreateMemStorage(0)
        cv.ClearMemStorage(storage)

        # equalize histogram
        cv.EqualizeHist(grayscale, grayscale)

        # detect faces
        faces = cv.HaarDetectObjects(grayscale, self.face_cascade, storage,
                                     1.2, 2,
                                     cv.HAAR_DO_CANNY_PRUNING,
                                     self.face_size)

        if faces:
            # faces detected
            for i in faces:
                cv.Rectangle(image, cv.Point( int(i.x), int(i.y)),
                             cv.Point(int(i.x + i.width), int(i.y + i.height)),
                             cv.RGB(0, 255, 0), 3, 8, 0)

            detected = True
            is_face = True
        else:
            # detect body
            bodies = cv.HaarDetectObjects(grayscale, self.body_cascade, storage,
                                         1.1, 3, 0,
                                         self.body_size)

            if bodies:
                # body detected
                for i in bodies:
                    cv.Rectangle(image, cv.Point( int(i.x), int(i.y)),
                                 cv.Point(int(i.x + i.width), int(i.y + i.height)),
                                 cv.RGB(0, 255, 0), 3, 8, 0)

                detected = True
                is_face = False
            else:
                detected = False
                is_face = False

        # release resources we don't need any more
        cv.ReleaseImage(grayscale)
        cv.ReleaseMemStorage(storage)

        return (detected, is_face)


