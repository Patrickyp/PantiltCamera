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
int motorDelay = 300;

//current location of pan where 0 is home
int currentLocationPan = 0;
int currentLocationTilt = 0;

//total number of motor steps in a full rotation for pan
int totalStepsPan = 0;

int totalStepsTilt = 0;

//  Open serial port /////

void setup() {                
  Serial.begin(115200); // Turn the Serial Protocol ON

  pinMode(2, OUTPUT);   // this is motor 1 direction (pan)
  pinMode(3, OUTPUT);   // this is motor 1 step      
  pinMode(4, OUTPUT);   // this is motor 2 direction (tilt)
  pinMode(5, OUTPUT);   // this is motor 2 step     

  
  pinMode(6, OUTPUT);   // Used to supply the volt (pan).
  pinMode(7, INPUT);    // Used to check if switch is connected (pan).
  digitalWrite(6, HIGH);  // Set default volt (pan).
  pinMode(8, OUTPUT);   // Used to supply the volt (tilt).
  pinMode(9, INPUT);    // Used to check if switch is connected (tilt).
  digitalWrite(8, HIGH);  // Set default volt (tilt).
  
  digitalWrite(2, HIGH); // Set default direction (pan)
  digitalWrite(3, LOW);  // Change this to HIGH to take a step
  digitalWrite(4, HIGH); // Set default direction (tilt)
  digitalWrite(5, LOW);  // Change this to HIGH to take a step
}

// Move the motor specified number of steps, dir should be either HIGH or LOW.
void moveStep(int motor, int steps, int dir){
  int motorDirection, motorStep;
  if (motor == 99){
    motorDirection = 2;
    motorStep = 3;
  } 
  else if (motor == 98) {
    motorDirection = 4;
    motorStep = 5;
  }
  
  digitalWrite(motorDirection, dir); 

  for (int count = 0; count < steps; count++){
    digitalWrite(motorStep, HIGH);  // take a motor step
    delayMicroseconds(motorDelay);          
    digitalWrite(motorStep, LOW);    // take a motor step 
    delayMicroseconds(motorDelay);
  }
}

void findTotalStepsTilt(){
  // 1 is toward home, 0 away
  //findHomeTilt();  //make sure tilt is at home
  totalStepsTilt = 0;
  delay(500);
  int val = digitalRead(9);
//
//  if (val == HIGH){
//    Serial.println("HIGH");
//  } else {
//    Serial.println("LOW");
//  }

  while (val != LOW){
    moveStep(98,50,LOW);
    val = digitalRead(9);
  }
  totalStepsTilt+=50;
  val = digitalRead(9);
//  if (val == HIGH){
//    Serial.println("HIGH");
//  } else {
//    Serial.println("LOW");
//  }
  while (val == LOW){
    moveStep(98,1,LOW);
    val = digitalRead(9);
    totalStepsTilt++;
  }
  Serial.println(totalStepsTilt);
  
}

// Find the total number of steps for a full rotation
void findTotalStepsPan(){
  //findHomePan();  //uncomment this if you will be calling this function when position is not initially home
  totalStepsPan = 0;
  delay(500);
  int val = digitalRead(7);
  // 
  while (val == HIGH){
    //Serial.println("Value high");
    moveStep(99,1,HIGH);
    val = digitalRead(7);
    totalStepsPan++;
  }
  // val should be LOW now
  while (val != HIGH){
    //Serial.println("Value high");
    moveStep(99,1,HIGH);
    val = digitalRead(7);
    totalStepsPan++;
  }
  //Move back so that findHomePan can be called again to avoid tangled wires.
  moveStep(99,200,LOW);
  //Serial.print("Total steps:");
  Serial.println(totalStepsPan);
}


void findHomeTilt(){
  // 1 is toward home, 0 away
  int val = digitalRead(9);
  // If switch is currently connected (at the end switch), move it until it's not connected.
  if (val == HIGH){
    while (val != LOW){
      moveStep(98,1,HIGH);
      val = digitalRead(9);
    }
    //Move an ADDITIONAL 20 steps just to be sure switch is not connected
    moveStep(98,20,HIGH);
  }
  // Move tilt until it's connected to home switch.
  val = digitalRead(9);
  while (val != HIGH){
    moveStep(98,1,HIGH);
    val = digitalRead(9);
  }

  currentLocationTilt = 0;
  Serial.print("Moved to home.\n");
}


// Find home location (when the switch first becomes connected).
void findHomePan(){
  int val = digitalRead(7);
  // If switch is currently not connected, move it until it's connected
  if (val == LOW){
    while (val != HIGH ){   
      moveStep(99,1,LOW);  // move 1 step
      val = digitalRead(7);  //update val
    }
    moveStep(99,20,LOW); // Move 20 more steps to make sure it really is HIGH territory.
  }

  // Move motor until switch isn't connected, then stop.
  val = digitalRead(7);
  while(val != LOW){  
    moveStep(99,1,LOW);  // move 1 step
    val = digitalRead(7);
  }
  
  // Move motor an ADDITIONAL 200 steps past home
  moveStep(99,200,LOW);
  delay(200);
  // Move motor back to home
  while (val != HIGH ){   
      moveStep(99,1,HIGH);  // move 1 step
      val = digitalRead(7);  //update val
  }

  currentLocationPan = 0;
  Serial.print("Moved to home.\n");
}

// Move to location steps from home.  Make sure currentLocationPan value is accurate before calling.
void moveToPan(int location){
  while (currentLocationPan < location){
    moveStep(99,1,HIGH);
    currentLocationPan++;
  }
}

void moveToTilt(int location){
  while (currentLocationTilt < location){
    moveStep(98,1,LOW);
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
      
      // Zen motor
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
          moveStep(98,Steps, Direction);
          Serial.println("movementDone");        // send a one back to computer when motor movement is done
        }
      }
      
      // Az motor?
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
          moveStep(99,Steps, Direction);
          Serial.println("movementDone");        // send a one back to computer when motor movement is done
        }
        
      }
      
  }
}

 


