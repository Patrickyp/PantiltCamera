////////////////////////////////////////////////
// Program to control the stepper motor using 
// serial communication from a computer. 
////////////////////////////////////////////// 
// Arduino and Pololu Board with DREV8825 driver chip.
//      Wiring Configuration  
// Arduino          Driver_Board             Stepper_Motor                    Limit_Switch
//                  (both board)
//
//   5V             Reset + Sleep
//  GND             GND  (next to Fault)         
//  DigOut 2        DIR  (board 1 pan)
//  DigOut 3        STEP (board 1 pan)
//  DigOut 4        DIR  (board 2 tilt)
//  DigOut 5        STEP (board 2 tilt)
//                  A2                     98,-1,2   Motor Red wire
//                  A1                        Motor Blue wire 
//                  B1                        Motor Green wire
//                  B2                        Motor Black wire 
//  DigOut 6                                                                  Output for limit switch (pan)
//  DigOut 7                                                                  Input for limit switch  (pan)
//  DigOut 8                                                                  Output for limit switch (tilt)
//  DigOut 9                                                                  Input for limit switch  (tilt)
////    Both motors use the same wire connections
//////////////////////////////////////////////////


int DelayTime = 325;    // microseconds
int delayTime = 100;
int motorDelay = 500;   // control speed of motor movements

//current location of pan where 0 is home
int currentLocationPan = 0;
int currentLocationTilt = 0;

//variable to store total number of motor steps in a full rotation for pan
int totalStepsPan = 0;

//variable to store total number of motor steps in a full rotation for tilt
int totalStepsTilt = 0;

// Pin numbers for motor movement and limit switch
int panDir = 2;
int panStep = 3;
int panSwitch = 8; 

int tiltDir = 4;
int tiltStep = 5;
int tiltSwitch = 9;


void setup() {                
  Serial.begin(115200); // Turn the Serial Protocol ON

  pinMode(panDir, OUTPUT);   // this is motor 1 direction (pan)
  pinMode(panStep, OUTPUT);   // this is motor 1 step      
  pinMode(tiltDir, OUTPUT);   // this is motor 2 direction (tilt)
  pinMode(tiltStep, OUTPUT);   // this is motor 2 step     

  
  // pinMode(6, OUTPUT);   // Used to supply the volt (pan).
  pinMode(panSwitch, INPUT);    // Used to check if switch is connected (pan).
  //digitalWrite(6, HIGH);  // Set default volt (pan).
  //pinMode(8, OUTPUT);   // Used to supply the volt (tilt).
  pinMode(tiltSwitch, INPUT);    // Used to check if switch is connected (tilt).
  //digitalWrite(8, HIGH);  // Set default volt (tilt).
  
  digitalWrite(panDir, HIGH); // Set default direction (pan)
  digitalWrite(panStep, LOW);  // Change this to HIGH to take a step
  digitalWrite(tiltDir, HIGH); // Set default direction (tilt)
  digitalWrite(tiltStep, LOW);  // Change this to HIGH to take a step
}

// Move the motor specified number of steps, dir should be either 1 or 0.
void moveStep(int motor, int dir, int steps){
  int motorDirectionPin, motorStepPin;
  // set step and direction based on motor
  if (motor == 99){
    motorDirectionPin = panDir;
    motorStepPin = panStep;
  } 
  else if (motor == 98) {
    motorDirectionPin = tiltDir;
    motorStepPin = tiltStep;
  }
  else {
    Serial.println("Invalid motor index.");
    return;
  }
  
  digitalWrite(motorDirectionPin, dir); 
  // loop the given number of steps
  for (int count = 0; count < steps; count++){
    digitalWrite(motorStepPin, HIGH);  // take a motor step
    delayMicroseconds(motorDelay);          
    digitalWrite(motorStepPin, LOW);    // take a motor step 
    delayMicroseconds(motorDelay);
  }
}

// Find the total steps for a tilt rotation, print value to serial port.
void findTotalStepsTilt(){
  // 1 is toward home, 0 away
  totalStepsTilt = 0;
  delay(500);
  
  int val = digitalRead(tiltSwitch);
  // If switch connected move away from home 50 steps and record that.
  while (val == LOW){
    Serial.println("Tilt switch error: VAL = HIGH");
    moveStep(98,0,1);
    val = digitalRead(tiltSwitch);
    totalStepsTilt++;
  }
  //totalStepsTilt+=50;
  val = digitalRead(tiltSwitch);
  // Continue to move away from home until hit the other switch.  Record steps.
  while (val == HIGH){
    //Serial.println("VAL = LOW");
    moveStep(98,0,1);
    val = digitalRead(tiltSwitch);
    totalStepsTilt++;
  }
  Serial.println(totalStepsTilt);
  
}

// Find the total number of steps for a full rotation.
void findTotalStepsPan(){
  //findHomePan();  //uncomment this if you will be calling this function when position is not initially home
  totalStepsPan = 0;
  delay(500);
  int val = digitalRead(panSwitch);
  // Move until switch is no longer connected.
  while (val == LOW){
    //Serial.println("Error:Value high");
    moveStep(99,HIGH,1);
    val = digitalRead(panSwitch);
    totalStepsPan++;
  }
//  moveStep(99,1,100);
//  totalStepsPan += 100;
  // val should be LOW now
  while (val == HIGH){
    //Serial.println("Value high");
    moveStep(99,HIGH,1);
    val = digitalRead(panSwitch);
    totalStepsPan++;
  }
  //Move back so that findHomePan can be called again to avoid tangled wires.
  moveStep(99,LOW,200);
  //Serial.print("Total steps:");
  Serial.println(totalStepsPan);
}

// Find the home switch for tilt.
// If currently on the opposite switch, move 200 steps to become from HIGH to LOW, keep moving until HIGH.
void findHomeTilt(){
  // 1 is toward home, 0 away
  int val = digitalRead(tiltSwitch);
  // If switch is currently connected (at the end switch, only during run), move it until it's not connected.
  if (val == LOW){
//    while (val != LOW){
//      moveStep(98,HIGH,1);
//      val = digitalRead(9);
//    }
    //Move 200 steps until switch is not connected
    moveStep(98,HIGH,200);
  }
  // Move tilt until it's connected to home switch.
  val = digitalRead(tiltSwitch);
  while (val != LOW){
    moveStep(98,HIGH,1);
    val = digitalRead(tiltSwitch);
  }
  //Move 50 steps past home
  moveStep(98,HIGH,80);

  //Move back to home
  while (val != HIGH){
    moveStep(98,LOW,1);
    val = digitalRead(tiltSwitch);
  }
  

  currentLocationTilt = 0;
  Serial.print("Moved to home.\n");
}


// Find home location (when the switch first becomes connected).
void findHomePan(){
  int val = digitalRead(panSwitch);
  // If switch is currently not connected, move it until it's connected
  if (val == HIGH){
    while (val != LOW ){   
      moveStep(99,LOW,1);  // move 1 step
      val = digitalRead(panSwitch);  //update val
    }
    //moveStep(99,LOW,20); // Move 20 more steps to make sure it really is HIGH territory.
  }

  // Move motor until switch isn't connected, then stop.
  val = digitalRead(panSwitch);
  while(val != HIGH){  
    moveStep(99,LOW,1);  // move 1 step
    val = digitalRead(panSwitch);
  }
  
  // Move motor an ADDITIONAL 200 steps past home
  moveStep(99,LOW,200);
  delay(200);
  
  // Move motor back to home
  while (val != LOW ){   
      moveStep(99,HIGH,1);  // move 1 step
      val = digitalRead(panSwitch);  //update val
  }

  currentLocationPan = 0;
  Serial.print("Moved to home.\n");
}

// Move to location steps from home.  Make sure currentLocationPan value is accurate before calling.
void moveToPan(int location){
  while (currentLocationPan < location){
    moveStep(99,HIGH,1);
    currentLocationPan++;
  }
}

void moveToTilt(int location){
  while (currentLocationTilt < location){
    moveStep(98,LOW,1);
    currentLocationTilt++;
  }
}



void loop() {
  
  if (Serial.available()) {
      // Reads 3 ints from serial port.  First int is either 98 or 99 to specify motor.  2nd int 
      // should be 0 or 1 for moving motor in which Steps would be number of steps to move or -1 to pass it a command
      // where Steps would be that command.
      
      int motor = Serial.parseInt();    // Should be 98 or 99
      int Direction = Serial.parseInt();   // Should be a 0, 1 or -1
      int Steps = Serial.parseInt();  // Should be a positive integer

      // Tilt(Zen) motor
      if (motor == 98){
        if (Direction == -1){
          if (Steps == 0) {
            findHomeTilt();
            delay(500);
          }

          if (Steps == 1){
            int stepCount = Serial.parseInt();
            moveToTilt(stepCount);
            Serial.println(currentLocationTilt);
          }
          if (Steps == 2){
            findHomeTilt();
            findTotalStepsTilt();
            //findHomeTilt();
          }
        }
        else{
          delayMicroseconds(DelayTime);
          moveStep(98,Direction,Steps);
          Serial.println("movementDone");        // send a one back to computer when motor movement is done
        }
      }
      
      // Pan(Az) motor
      if (motor == 99){
        if (Direction == -1){
          
          // 0 means find home
          if (Steps == 0){
            findHomePan();
            delay(500);
          } 

          // 2 means find total steps
          if (Steps == 2){
            findHomePan();
            findTotalStepsPan();
            findHomePan();
          }
          
          // 1 means move motor specific step location.  currentLocationPan must be up to date before calling this.
          if (Steps == 1){
            int stepCount = Serial.parseInt();
            moveToPan(stepCount);
            Serial.println(currentLocationPan);
          }
        } else {
          // Move the motor Steps number of steps in Direction direction
          delayMicroseconds(DelayTime);
          moveStep(99,Direction,Steps);
          Serial.println("movementDone");        // send a one back to computer when motor movement is done
        }
        
      }
      
  }
}

 


