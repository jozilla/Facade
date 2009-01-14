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

import sys
from CVtypes import cv
from facedetection import FaceDetector

d = FaceDetector(show_cam=True)
key = 0
escape = 27

while key != escape: 
    (present, is_face) = d.fetch_and_detect()
    if present:
        print "Available"
    else:
        print "Away"

    key = cv.WaitKey(1) # needed for event loop

print 'Cleaning up resources ...'
del d
print 'Done, exiting now ...'
sys.exit(0)
