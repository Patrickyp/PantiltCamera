# Run with PanTiltExample2GUI.ini
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
import time
import cv2
import datetime
from FPS import FPS
from WebcamVideoStream import WebcamVideoStream
import atexit

ser = serial.Serial('/dev/ttyACM0', 115200)
stepValues = [250,800,1200] # Step increments for move command on GUI
step = stepValues[0]*2 # Default stepValue
running = False # This value is set to False when user clicks Stop, will quit Run loop
vs = WebcamVideoStream(src=0).start()
vs1 = WebcamVideoStream(src=1).start()
        
class PanTiltApp(QtGui.QDialog, ui.Ui_Dialog):
    
    def __init__(self):
        # Explaining super is out of the scope of this article
        # So please google it if you're not familiar with it
        # Simple reason why we use it here is that it allows us to
        # access variables, methods etc in the design.py file
        super(self.__class__, self).__init__()
        self.setupUi(self)  # This is defined in design.py file automatically
                            # It sets up layout and widgets that are defined
                            
        # Define the method called when a button is pressed
        self.Run.clicked.connect(self.run_gui)
        self.Stop.clicked.connect(self.stop_gui)
        self.Step1.clicked.connect(self.step1)
        self.Step2.clicked.connect(self.step2)
        self.Step3.clicked.connect(self.step3)
        self.MoveRight.clicked.connect(self.moveRight)
        self.MoveLeft.clicked.connect(self.moveLeft)
        self.MoveUp.clicked.connect(self.moveUp)
        self.MoveDown.clicked.connect(self.moveDown)
        self.Twobythree.clicked.connect(self.twoByThree)
        # Set step button text
        self.Step1.setText("Step " + str(stepValues[0]))
        self.Step2.setText("Step " + str(stepValues[1]))
        self.Step3.setText("Step " + str(stepValues[2]))
        
        # Limit valid inputs of Time, Az, Zen using validator 
        myRegex = QtCore.QRegExp("(\d+)(,\s*\d+)*") # Format of {int1,int2...intn} using regex
        commaSeparatedIntValidator = QtGui.QRegExpValidator(myRegex) # Validator of only comma separated ints
        doubleValidator = QtGui.QDoubleValidator() # Validator of only doubles
        self.AzInput.setValidator(commaSeparatedIntValidator)
        self.ZenInput.setValidator(commaSeparatedIntValidator)
        self.TimeInput.setValidator(doubleValidator)
 
    def twoByThree(self):
        takeImageSix(self,50,80)
        
    def moveRight(self):
        updateStatus(self, "Moving Right...")
        # Motor # , direction, number of steps
        output = str(99) + "," + str(1) + "," + str(step)
        ser.write(output)
        status = ser.readline()
        updateStatus(self, "Idle")
    def moveLeft(self):
        updateStatus(self, "Moving Left...")
        output = str(99) + "," + str(0) + "," + str(step)
        ser.write(output)
        status = ser.readline()
        updateStatus(self, "Idle")
    def moveUp(self):
        updateStatus(self, "Moving Up...")
        output = str(98) + "," + str(1) + "," + str(step)
        ser.write(output)
        status = ser.readline()
        updateStatus(self, "Idle")
    def moveDown(self):
        updateStatus(self, "Moving Down...")
        output = str(98) + "," + str(0) + "," + str(step)
        ser.write(output)
        status = ser.readline()
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
         
    def stop_gui(self):
        global running
        running = False
    
    # Start the run routine.  
    def run_gui(self):
        
        global running
        
        # Flush serial port buffer.
        ser.flushInput()
        ser.flushOutput()
        
        # If not already running, start run, otherwise ignore button press
        if running == False:
            running = True
  
            # Read values from 3 text inputs, viewList contains all possible combinations of (az,zen).  
            (sleepDuration, AzList, ZenList) = processInput(self.TimeInput.text(),self.AzInput.text(),self.ZenInput.text())
            
            # Find total number of steps for full rotation and 
            stepsPerDegreePan, stepsPerDegreeTilt = findTotalSteps(self)
            
            viewIndex = 0 
            
            # For each iteration of this loop, find home, move through all views, take image, and sleep.  
            # Check for stop button press periodically with app.processEvents
            while True:
                viewIndex = 0
                # Tell pan motor(99) to find home.
                findHome(self, 99)
                
                #check stop button
                app.processEvents()
                if (running == False):
                    print "stopped!"
                    updateStatus(self,"Idle")
                    return
                
                # Outer loop goes through each Az angle, inner loop goes through each Zen angle.
                # I.e motor will go to each Az angle and go through all Zen angle while at each Az angle.
                for i in range(0, len(AzList)):
                    pointCamera(self, AzList[i], stepsPerDegreePan, 99)
                    # Update status message before each new Az
                    status = "Moving to Az " + str(AzList[i]) + " Zen " + str(ZenList[0]) 
                    updateStatus(self, status)
                    print AzList[i]
                    findHome(self,98)
                    for j in range(0, len(ZenList)):
                        viewIndex+=1
                        # Don't need to update for the first zen since status already updated for every new Az above
                        if (j != 0):
                            status = "Moving to Az " + str(AzList[i]) + " Zen " + str(ZenList[j]) 
                            updateStatus(self, status)
                        
                        pointCamera(self, ZenList[j], stepsPerDegreeTilt, 98)
                        print " ", ZenList[j]
                        # Update View/Az/Zen labels
                        self.ViewLabel.setText(str(viewIndex))
                        self.AzLabel.setText(str(AzList[i]))
                        self.ZenLabel.setText(str(ZenList[j]))
                        app.processEvents()
                        
                        #takeImage(self,4) 
                        
                        takeImageSix(self,str(AzList[i]), str(ZenList[j]))
                        #check stop button
                        app.processEvents()
                        if (running == False):
                            print "stopped!"
                            updateStatus(self,"Idle")
                            return
                            
                        sleep(self,sleepDuration)
                
# Flush serial port buffer.             
def flushSerial():
    ser.flushInput()
    ser.flushOutput()
    
# Move the motor specified by motorID to position(in degree).
# stepsPerDegree is how many steps the motor takes for 1 degree (~10).
def pointCamera(self,position,stepsPerDegree,motorID):
    # Calculate destination step location using position (degrees) and stepsPerDegree
    destination = int(round(position * stepsPerDegree)) 
    
    # Move pan motor to az position.  Convert degrees to steps.  Round to the nearest whole number, then call int to remove trailing .0
    command = str(motorID) + "," + str(-1) + "," + str(1) + "," + str(destination) #Motor #, command, direction, position
    ser.write(command)
    ser.readline()

# Tell motor to find home.
def findHome(self, motorNumber):
    #print "Finding home position."
    #updateStatus(self, "Finding home position.")
    command = str(motorNumber) + "," + str(-1) + "," + str(0)
    ser.write(command)
    message = ser.readline()
    #updateStatus(self, message.strip())  
     
# Tell motor to find total steps in full rotation, update global totalStepsPan variable and return number of steps per degree
def findTotalSteps(self):
    
    updateStatus(self,"Calculating total steps.")
    
    ####################################################################################################################
    ####### Tell PAN motor to find total steps.  99 means az motor, -1 means command, 2 means find total steps. ########
    command = str(99) + "," + str(-1) + "," + str(2)
    ser.write(command)
    
    # NOTE: Need to read 3 values back, 2 for findHome and 1 for findTotalSteps.  This is needed otherwise python will skip to next part without
    # waiting for motor operation to complete.
    
    # findHome
    message = ser.readline()
    print "[PAN]", message
    updateStatus(self, "[PAN]" + message.strip())
    
    # findTotalSteps
    message = ser.readline()
    message = message.strip()
    print "[PAN]",message
    updateStatus(self, "[PAN]Total steps:" + message)
    totalStepsPan = int(message)
    stepsPerDegreePan = totalStepsPan / 360
    
    #findHome
    message = ser.readline()
    print "[PAN]",message
    updateStatus(self, "[PAN]" + message.strip())
    
    ############################################################################################################################
    ####### Tell TILT motor to find total steps.  98 means tilt(zen) motor, -1 means command, 2 means find total steps. ########
    command = str(98) + "," + str(-1) + "," + str(2)
    ser.write(command)
    
    # findHome
    message = ser.readline()
    print "[TILT]",message
    updateStatus(self, "[TILT]" + message.strip())
    
    # findTotalSteps
    message = ser.readline()
    msg = message.strip()
    print "[TILT]",msg
    updateStatus(self, "[TILT]Total steps:" + msg)
    totalStepsTilt = int(msg)
    stepsPerDegreeTilt = 10.55555 # 1/(1.8/19)
    
    print " ZEN DONE!", stepsPerDegreePan
    return (stepsPerDegreePan, stepsPerDegreeTilt)

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
        
        # Change QString to String
        timeString = int(TimeQString)
        AzString = str(AzQString)
        ZenString = str(ZenQString)
    
        # Remove ending comma if nessesary 
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
    
def motorInit():
    # TODO
    print "Motor Initialized."

def takeImageSix(self,az,zen):
    updateStatus(self,"Taking 6 images.")
    # List to hold 6 frames.
    frames = []
    # List to hold filename for 6 frames.
    fileNames = []
    
    print("[INFO] sampling THREADED frames from webcam...")
    fps = FPS().start()
    t0 = time.time()
    while fps._numFrames < 3:
        # Make sure that we are grabbing new frames each time with freshFrame
        if vs.freshFrame == vs1.freshFrame == True:
            frame = vs.read()
            frames.append(frame)
            name = getTime()+"Az"+str(az)+"Zen"+str(zen)+"Lat99Lon99Height50C1.jpg"
            fileNames.append("images/"+name)
            
            frame1 = vs1.read()
            frames.append(frame1)
            name = getTime()+"Az"+str(az)+"Zen"+str(zen)+"Lat99Lon99Height50c2.jpg"
            fileNames.append("images/"+name)
            fps.update()
    
    t1 = time.time()
   
    total = t1-t0
    print "TIME: ", total
    #print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
    #print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
    
    for i in range(0,6):
        cv2.imwrite(fileNames[i],frames[i]) 
    
    updateStatus(self,"Idle.")
    
def getTime():
    dt = datetime.datetime.now()
    timeString = dt.strftime("%H-%M-%S-") + str(dt.microsecond)
    return timeString


def saveData():
    # TODO
    print "Saving Data..."
    
def sleep(self,duration):
    # TODO
    message = "Sleeping for " + str(duration) + " seconds."
    updateStatus(self,message)
    #self.StatusLabel.setText(message)
    #self.StatusLabel.repaint()
    #app.processEvents()
    time.sleep(duration)
    print "Sleeping for " + str(duration)

# Convert an Opencv image into a QImage
def convertImage(frame):
              
            #image = cv2.imread("/home/user1/Pictures/2.jpg")
            #image = convertImage(image)
            #self.MainImage.setPixmap(image)
    h,w = frame.shape[:2]
    img = QtGui.QImage(frame,w,h,QtGui.QImage.Format_RGB888)
    img = QtGui.QPixmap.fromImage(img)
    return img
def exitFunction():
    print "exiting..."
    vs.stop()
    vs1.stop()

#atexit.register(exitFunction)
app = QtGui.QApplication(sys.argv)  # A new instance of QApplication
form = PanTiltApp()                 # We set the form to be our PanTiltApp (design)
form.show()                         # Show the form
app.exec_()                         # and execute the app
exitFunction()
sys.exit()
# How to open a pop up, might need later...
  #def openPopup(self):
        #print "Opening a new popup window..."
        #self.w = MyPopup()
        #self.w.setGeometry(QRect(100, 100, 400, 200))
        #self.w.show()    
#class MyPopup(QWidget):
    #def __init__(self):
        #QWidget.__init__(self)

        #def paintEvent(self, e):
        #dc = QPainter(self)
        #dc.drawLine(0, 0, 100, 100)
        #dc.drawLine(100, 0, 0, 100)
              