# Run with PanTiltExample4GUI.ini
#
#
#
# NOTE: Boxes on GUI made using QFrames.
# Command to convert ui file to py: $ pyuic4 youfile.ui -o yourfile.py


from __future__ import division # Will cause / operation to output decimal values instead if integers.  Default in python 3 but we are using python 2.
from PyQt4 import QtGui
import ui
import sys
import serial 
from PyQt4.Qt import *
import PyQt4.QtCore as QtCore
import cv2
import datetime
from FPS import FPS #See FPS.py.
from WebcamVideoStream import WebcamVideoStream #See WebcamVideoStream.py
import time
from docutils.utils.math.math2html import Position


ser = serial.Serial('/dev/ttyACM0', 115200) # Start serial communication with Arduino, change baud rate and port here.
stepValues = [30,60,120] # Step increments for move command on GUI
step = stepValues[1] # Default stepValue
running = False # This value is set to False when user clicks Stop, will quit Run loop

lsi = 0
rsi = 1
wvi = 2

# Set webcam index here
vs = WebcamVideoStream(src=lsi)#.start()
vs1 = WebcamVideoStream(src=rsi)#.start() # Note that this stream will never be stopped.
vs2 = None
#vs2 = WebcamVideoStream(src=2)#.start()

# Initialize video writer objects.
out = None
out1 = None
out2 = None

# Keep track of which camera is currently being displayed.
# This variable is updated whenever a new camera is selected via radio button.
currentCamera = vs

# Keep track of whether to record frames from cameras
recordStatus = False


class PanTiltApp(QtGui.QDialog, ui.Ui_Dialog):
    
    def __init__(self):
        # Explaining super is out of the scope of this article
        # So please google it if you're not familiar with it
        # Simple reason why we use it here is that it allows us to
        # access variables, methods etc in the design.py file
        super(self.__class__, self).__init__()
        self.setupUi(self)  # This is defined in design.py file automatically
                            # It sets up layout and widgets that are defined
        vs.start()
	vs1.start()

        # Define the methods called when a button is pressed
        self.Run.clicked.connect(self.run_gui)
        self.Stop.clicked.connect(self.stop_gui)
        self.StepSmall.clicked.connect(self.step1)
        self.StepMedium.clicked.connect(self.step2)
        self.StepLarge.clicked.connect(self.step3)
        self.MoveRight.clicked.connect(self.moveRight)
        self.MoveLeft.clicked.connect(self.moveLeft)
        self.MoveUp.clicked.connect(self.moveUp)
        self.MoveDown.clicked.connect(self.moveDown)
        self.TakeImageSet.clicked.connect(self.takeImageSet)
        self.TakeCalibImages.clicked.connect(self.takeCalibImages)
        self.ShowWideView.clicked.connect(self.showWideView)
        self.ShowLStereo.clicked.connect(self.showLeftView)
        self.ShowRStereo.clicked.connect(self.showRightView)
        self.SaveVideo.clicked.connect(self.saveVideo)
        
        # Set step button text
        self.StepSmall.setText("Step " + str(stepValues[0]))
        self.StepMedium.setText("Step " + str(stepValues[1]))
        self.StepLarge.setText("Step " + str(stepValues[2]))
        
        # Limit valid inputs of Time, Az, Zen using validator 
        myRegex = QtCore.QRegExp("(\d+)(,\s*\d+)*") # Format of {int1,int2...intn} using regex
        commaSeparatedIntValidator = QtGui.QRegExpValidator(myRegex) # Validator of only comma separated ints
        doubleValidator = QtGui.QDoubleValidator() # Validator of only doubles
        self.AzInput.setValidator(commaSeparatedIntValidator)
        self.ZenInput.setValidator(commaSeparatedIntValidator)
        self.TimeInput.setValidator(doubleValidator)

        # Start a QTimer to constantly show camera feed on GUI.  
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self.showLiveFeed)
        self._timer.start(10) # call play every 10 msec
    
    # This function is called by QTimer above to display a frame on GUI every set interval.  Also reads a frame from all 3 cameras and save them
    # if the save video box is selected.
    def showLiveFeed(self):
        ###################################################################################################
        global recordStatus
        global out,out1,out2

        # If saveVideo function set recordStatus to True, start saving frames.
        if recordStatus == True:
            totalTime = time.time() - self.videoStartTime
            if totalTime > 60:
                print totalTime
                print "1 minute up!"
                recordStatus = False
                self.SaveVideo.setCheckState(Qt.Unchecked)
            else:
                frame ,_ = vs.read()
                frame1 ,_ = vs1.read()
                #frame2 ,_ = vs2.read()
		while ((out == None) or (out1 == None)):
			x = 1
		
                out.write(frame)
                out1.write(frame1) 
                #out2.write(frame2)
        ####################################################################################################
        global currentCamera
        
	while (currentCamera == None):
		x = 1
		print "Current Camera is None"
        # Tell the camera thread to send back a frame converted into a QPixmap. 
        frame = currentCamera.convertFrame()
        
        # Set frame display on center display.
        try:
            self.MainImage.setPixmap(frame)
            self.MainImage.setSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Ignored)
            self.MainImage.setScaledContents(True)
        except TypeError:
            print "No frame"
    
    # When save video box is selected run this function.
    def saveVideo(self):
        global recordStatus
        global out, out1#, out2
        # Box was selected before selection, user wants to stop recording.
        if recordStatus == True:
            print "finish recording!"
            recordStatus = False
        # Box was unselected before selection, user wants to start recording.
        else:
            self.videoStartTime = time.time()
            print"start timer!"
            # set recordStatus to 1 so that QTimer function above can start saving frames.
            recordStatus = True
            
            # Create file name for the 3 videos
            name1 = "videos/" + getTime() + "cam1.avi"
            name2 = "videos/" + getTime() + "cam2.avi"
            #name3 = "videos/" + getTime() + "cam3.avi"
            print "Creating videowriter object!"
            # initialize VideoWriter objects with file name.
            out = cv2.VideoWriter(name1,cv2.cv.CV_FOURCC('M','J','P','G'), 20.0, (1920,1080))
            out1 = cv2.VideoWriter(name2,cv2.cv.CV_FOURCC('M','J','P','G'), 20.0, (1920,1080))
            #out2 = cv2.VideoWriter(name3,cv2.cv.CV_FOURCC('M','J','P','G'), 20.0, (1920,1080))
        print "saving video!"
    
    # Show camera1 feed on GUI
    def showWideView(self):
        global currentCamera
	self.initializeWideCamera()
        currentCamera = vs2
        
    # Show camera2 feed on GUI   
    def showLeftView(self):
        global currentCamera
	self.initializeLeftStereoCamera()
        currentCamera = vs
    
    # Show camera3 feed on GUI
    def showRightView(self):
        global currentCamera
	#self.initializeLeftStereoCamera()
        currentCamera = vs1
        
    # Take 3 images for each camera (9 total).
    def takeImageSet(self):
        takeImages(self, 50, 80, False, 3)
    
    # Take 1 image for each camera and label as CALIB (3 total).
    def takeCalibImages(self):
        takeImages(self, 50, 80, True, 1)
        
    def moveRight(self):
        updateStatus(self, "Moving Right...")
        # Motor # , direction, number of steps
        output = str(1) + "," + str(1) + "," + str(step)
        ser.write(output)
        __ = ser.readline()
        updateStatus(self, "Idle")
        
    def moveLeft(self):
        updateStatus(self, "Moving Left...")
        output = str(1) + "," + str(-1) + "," + str(step)
        ser.write(output)
        __ = ser.readline()
        updateStatus(self, "Idle")
        
    def moveUp(self):
        updateStatus(self, "Moving Up...")
        output = str(2) + "," + str(1) + "," + str(step)
        ser.write(output)
        __ = ser.readline()
        updateStatus(self, "Idle")
        
    def moveDown(self):
        updateStatus(self, "Moving Down...")
        output = str(2) + "," + str(-1) + "," + str(step)
        ser.write(output)
        __ = ser.readline()
        updateStatus(self, "Idle")
        
    # Set step variable to first value in stepValues list.  Update GUI with current step.
    def step1(self):
        global step
        step = stepValues[0]
        self.CurrentStep.setText(str(step))   
    
    # Set step variable to second value in stepValues list.  Update GUI with current step.
    def step2(self):
        global step
        step = stepValues[1]
        self.CurrentStep.setText(str(step))  
        
    # Set step variable to third value in stepValues list.  Update GUI with current step.
    def step3(self):
        global step
        step = stepValues[2]
        self.CurrentStep.setText(str(step))
    
    # Called when user clicks stop.  Sets running to false.  Program checks the running variable throughout
    # run routine to see if stop was clicked.
    def stop_gui(self):
        global running
        running = False
        buttonEnabledState(self, True)
    
    # Start the run routine.  
    def run_gui(self):
        global running

        updateStatus(self,"Starting run...")
        # Flush serial port buffer.
        ser.flushInput()
        ser.flushOutput()        
    
        # If not already running, start run, otherwise ignore button press
        if running == False:
            running = True
              
            # Disable buttons.
            buttonEnabledState(self, False)
            # Read values from 3 text inputs, viewList contains all possible combinations of (az,zen).  
            (sleepDuration, AzList, ZenList) = processInput(self.TimeInput.text(),self.AzInput.text(),self.ZenInput.text())
              
          
            # For each iteration of this loop
            while True:
                # Keep track of Viewing Case.
                viewIndex = 0
                
                # Check for any GUI inputs from user i.e. stop pressed.
                app.processEvents()
                # Check running variable for false value (set false when user clicks stop).  Break loop to stop routine if false.
                if (running == False):
                    print "stopped!"
                    updateStatus(self,"Idle")
                    return
                  
                # Outer loop goes through each Az (Pan) angle, inner loop goes through each Zen angle.
                # I.e motor will go to each Az angle and go through all Zen angle while at each Az angle.
                for i in range(0, len(AzList)):
                    # Update status message before each new Az
                    status = "Moving to Az " + str(AzList[i]) + " Zen " + str(ZenList[0]) 
                    updateStatus(self, status)

                    self.moveToPosition(1, AzList[i])
                    #print AzList[i]

                    
                    for j in range(0, len(ZenList)):
                        viewIndex+=1
                        # Don't need to update for the first zen since status already updated for every new Az above
                        if (j != 0):
                            status = "Moving to Az " + str(AzList[i]) + " Zen " + str(ZenList[j]) 
                            updateStatus(self, status)
                          
                        self.moveToPosition(2, ZenList[j])
                        #print " ", ZenList[j]
                        # Update View/Az/Zen labels
                        self.ViewLabel.setText(str(viewIndex))
                        self.AzLabel.setText(str(AzList[i]))
                        self.ZenLabel.setText(str(ZenList[j]))
                        app.processEvents()
                          
                        # Take 3 images from each camera.
                        takeImages(self, str(AzList[i]), str(ZenList[j]), False, 3)
                          
                        #check stop button
                        app.processEvents()
                        if (running == False):
                            print "stopped!"
                            updateStatus(self,"Idle")
                            return
                          
                        # Sleep for delay as entered from GUI
                        sleep(self,sleepDuration)

                
    def moveToPosition(self, motorNumber, degree):
        command = str(motorNumber) + "," + str(0) + "," + str(degree)
        ser.write(command)
        result = ser.readline()
        print result
        
    def initializeLeftStereoCamera(self):
	global vs, vs1, vs2
	if (vs2 != None):
		vs2.stop()
		vs2 = None
		vs = WebcamVideoStream(src=lsi).start()
    
    def initializeWideCamera(self):
	global vs, vs1, vs2
	if (vs != None):
		vs.stop()
		vs = None
		vs2 = WebcamVideoStream(src=wvi).start()
		
# Enable or disable button during run because we don't want users to issue commands like Move Right while motor is doing its run routine.
# buttonState should be either True (to enable) or False (to disable).
def buttonEnabledState(self,buttonState):
    
    self.StepSmall.setEnabled(buttonState)
    self.StepMedium.setEnabled(buttonState)
    self.StepLarge.setEnabled(buttonState)
    self.MoveRight.setEnabled(buttonState)
    self.MoveLeft.setEnabled(buttonState)
    self.MoveUp.setEnabled(buttonState)
    self.MoveDown.setEnabled(buttonState)
    self.TakeImageSet.setEnabled(buttonState)
    self.TakeCalibImages.setEnabled(buttonState)
    self.ShowWideView.setEnabled(buttonState)
    self.ShowLStereo.setEnabled(buttonState)
    self.ShowRStereo.setEnabled(buttonState)
    self.SaveVideo.setEnabled(buttonState)
    self.Run.setEnabled(buttonState)
# Flush serial port buffer.             
def flushSerial():
    ser.flushInput()
    ser.flushOutput()

    

# Update the status label with given string
def updateStatus(self, string):
        self.StatusLabel.setText(string)
        self.StatusLabel.repaint()
        app.processEvents()
        
# Check 3 text inputs for valid inputs and process them.  Returns Time as int and the Az Zen values
# as 2 lists.
def processInput(TimeQString,AzQString,ZenQString):
        
        # Check for empty input
        if(len(AzQString) <= 0 or len(ZenQString) <= 0 or len(TimeQString) <= 0):
            print "Need at least 1 Az and Zen angle"
            return (-1,-1)
        
        # Change angle inputs from QString to String, change time input from QString to int.
        timeString = int(TimeQString)
        AzString = str(AzQString)
        ZenString = str(ZenQString)
    
        # Remove ending comma if necessary 
        if(AzString.endswith(',')):
            AzString = AzString[:-1]
        if(ZenString.endswith(',')):
            ZenString = ZenString[:-1]
            
        # Split both string by comma into lists
        AzList = AzString.split(',')
        ZenList = ZenString.split(',')
        
        # Turn both list into int lists.
        AzList = map(int, AzList);
        ZenList = map(int, ZenList);
        
        return (timeString,AzList,ZenList)

# Take imagePerCamera images from all 3 cameras.  If isCalib is True, 
# add a string in front of filename to indicate calibration.
def takeImages(self,az,zen,isCalib,imagePerCamera):
    updateStatus(self,"Taking images.")
    # List to hold 4 frames.
    frames = []
    # List to hold filename for 4 frames.
    fileNames = []
    
    calibString =""
    
    if (isCalib == True):
        calibString = "CALIBRATION_"
    
    # Get long/lat/alt average value from file
    content = [line.strip() for line in open('overall_average.txt')]
    stringContent = [str(i) for i in content]
    lon = stringContent[0]
    lat = stringContent[1]
    alt = stringContent[2]
    # Common info that's same on all 3 filename.
    statString = "Az"+str(az)+"Zen"+str(zen)+"Lat" + lat + "Lon" + lon + "Height" + alt
    
    print("[INFO] sampling THREADED frames from webcam...")
    fps = FPS().start()
    t0 = time.time()
    
    # Read frame from each camera.  Do this imagePerCamera number of times.
    while fps._numFrames < imagePerCamera:
        # Make sure that we are grabbing new frames each time with freshFrame
        if vs.freshFrame == vs1.freshFrame == True:#== vs2.freshFrame == True: # CHANGE HERE IF USING CAMERA 3!!!
            # Read a frame and the time of frame.
            frame, imageTime = vs.read()
            # Append frame to frames list.
            frames.append(frame)
            # Create filename string for image, append string to fileNames list.
            fileNames.append("images/" + calibString + imageTime + statString + "C1#"+str(fps._numFrames)+".jpg")

            frame1, imageTime1 = vs1.read()
            frames.append(frame1)
            fileNames.append("images/" + calibString + imageTime1 + statString + "c2#"+str(fps._numFrames)+".jpg")
             
#             frame2, imageTime2 = vs2.read()
#             frames.append(frame2)
#             fileNames.append("images/" + calibString + imageTime2 + statString + "C3#"+str(fps._numFrames)+".jpg")
#             
            fps.update()
    
    
    
    for i in range(0,imagePerCamera*2):
        cv2.imwrite(fileNames[i],frames[i]) 
    
    updateStatus(self,"Idle.")
# How to open a pop up, might need later...
def openPopup(self):
    print "Opening a new popup window..."
    self.w = MyPopup()
    self.w.setGeometry(QRect(100, 100, 400, 200))
    self.w.show()    
class MyPopup(QWidget):  
    def __init__(self):
        QWidget.__init__(self)

        def paintEvent(self, e):
            dc = QPainter(self)
            dc.drawLine(0, 0, 100, 100)
            dc.drawLine(100, 0, 0, 100) 
# Get current hour-minutes-seconds.  Used for creating filenames when user saves video.
def getTime():
    dt = datetime.datetime.now()
    timeString = dt.strftime("%H-%M-%S-") + str(dt.microsecond)
    return timeString


def saveData():
    # TODO
    print "Saving Data..."
    
# Sleep for duration seconds.  Used during run routine.
def sleep(self,duration):
    
    message = "Sleeping for " + str(duration) + " seconds."
    updateStatus(self,message)
    time.sleep(duration)
    print "Sleeping for " + str(duration)

# Convert an Opencv image into a QImage
def convertImage(frame):
    
    h,w = frame.shape[:2]
    img = QtGui.QImage(frame,w,h,QtGui.QImage.Format_RGB888)
    img = QtGui.QPixmap.fromImage(img)
    return img

# Do some clean up when gui exits.
def exitFunction():
    global vs,vs1,vs2,out,out1,out2

    if(vs != None):
	print "releasing vs"
    	vs.stop()
    if(vs1 != None):
   	print "releasing vs1"
    	vs1.stop()
    if(vs2 != None):
	print "releasing vs2"
    	vs2.stop()
    
    if out != None:
	print "releasing out"
        out.release()
    if out1 != None:
	print "releasing out1"
        out1.release()
    if out2 != None:
	print "releasing out2"
        out2.release()
    print "exiting..."

#******************************************************** Main method here ******************************************************************
app = QtGui.QApplication(sys.argv)  # A new instance of QApplication
form = PanTiltApp()                 # We set the form to be our PanTiltApp (design)
form.show()                         # Show the form
app.exec_()                         # and execute the app
exitFunction()
sys.exit()

              
