# import the necessary packages
from threading import Thread
import cv2
 
class WebcamVideoStream:
	
	def __init__(self, src=0):
		# initialize the video camera stream and read the first frame
		# from the stream
		self.stream = cv2.VideoCapture(src)
		self.stream.set(3,2048)
		self.stream.set(4,1536)
		(self.grabbed, self.frame) = self.stream.read()
		self.freshFrame = True
		# initialize the variable used to indicate if the thread should
		# be stopped
		self.stopped = False
	def start(self):
		# start the thread to read frames from the video stream
		Thread(target=self.update, args=()).start()
		return self
 
	def update(self):
		# keep looping infinitely until the thread is stopped
		while True:
			# if the thread indicator variable is set, stop the thread
			if self.stopped:
				return
 
			# otherwise, read the next frame from the stream
			(self.grabbed, self.frame) = self.stream.read()
			# Set freshFrame to True after update above
			self.freshFrame = True
 
	def read(self):
		# If a frame is read, set freshFrame to False to know if frame is read already on the next read.
		self.freshFrame = False
		# return the frame most recently read
		return self.frame
 
	def stop(self):
		# indicate that the thread should be stopped
		self.stopped = True
