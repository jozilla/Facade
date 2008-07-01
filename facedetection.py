from CVtypes import cv

class FaceDetector:
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
        cv.SetCaptureProperty(capture, cv.CAP_PROP_FRAME_WIDTH, width)
        cv.SetCaptureProperty(capture, cv.CAP_PROP_FRAME_HEIGHT, height)

        # check if capture device is OK
        if not capture:
            print "Error opening capture device"

        self.capture = capture

        # load cascades
        self.face_cascade = cv.LoadHaarClassifierCascade('haarcascade_frontalface_alt.xml',
                                                         cv.Size(1,1))
        self.body_cascade = cv.LoadHaarClassifierCascade('haarcascade_upperbody.xml',
                                                         cv.Size(1,1))

        self.show_cam = show_cam
        if self.show_cam:
            cv.NamedWindow('Camera', cv.WINDOW_AUTOSIZE)

    def fetch_and_detect(self):
        frame = cv.QueryFrame(self.capture)
        
        if frame is None:
            print 'Could not get frame'
            return

        cv.Flip(frame, None, 1)

        # face detection
        tpl = self.detect(frame) # = (detected something?, is it a face?)

        # update webcam image
        if self.show_cam:
            cv.ShowImage('Camera', frame)

        return tpl 

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
                                     cv.Size(50, 50))

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
                                         cv.Size(125, 125))

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

        # release resources we don't need anymore
        cv.ReleaseImage(grayscale)
        cv.ReleaseMemStorage(storage)

        return (detected, is_face)

