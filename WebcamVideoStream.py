# import the necessary packages
from threading import Thread
import cv2
import datetime
import numpy as np
from PyQt4 import QtGui, QtCore, Qt


class WebcamVideoStream:
	
	def __init__(self, src=0):
		# initialize the video camera stream and read the first frame
		# from the stream
		self.stream = cv2.VideoCapture(src)
		# default 1280 by 720
		self.stream.set(3,1920) 
		self.stream.set(4,1080)
		(self.grabbed, self.frame) = self.stream.read()
		self.freshFrame = False
		# initialize the variable used to indicate if the thread should
		# be stopped
		self.stopped = False
		self.frameTime = ""
		# Used for converting frame to QT image
		self.currentFrame = np.array([])
		
	def start(self):
		# start the thread to read frames from the video stream
		Thread(target=self.update, args=()).start()
		return self

	def update(self):
		# keep looping infinitely until the thread is stopped
		while True:
			# if the thread indicator variable is set, stop the thread
			if self.stopped:
				self.stream.release()
				return

			# otherwise, read the next frame from the stream
			(self.grabbed, self.frame) = self.stream.read()
			
			self.frameTime = datetime.datetime.now().strftime("%m-%d-%H-%M-%S-%f")

			# Set freshFrame to True after update above
			self.freshFrame = True
			
	# Same as read except returns a frame suitable for QT GUI
	def convertFrame(self):
		self.freshFrame = False
		
		self.currentFrame = cv2.cvtColor(self.frame,cv2.COLOR_BGR2RGB)
		try:
			height,width=self.currentFrame.shape[:2]
			img=QtGui.QImage(self.currentFrame,
							  width,
							  height,
							  QtGui.QImage.Format_RGB888)
			img=QtGui.QPixmap.fromImage(img)
			return img
		except:
			print "Error: No frame returned."
			return None

	def read(self):
		# If a frame is read, set freshFrame to False to know if frame is read already on the next read.
		self.freshFrame = False
		# return the frame most recently read
		return self.frame, self.frameTime

	def stop(self):
		# indicate that the thread should be stopped
		self.stopped = True
