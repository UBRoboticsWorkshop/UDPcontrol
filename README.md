# UDPcontrol

## Python Code

import socket
import time
import pygame
import sys
import array

def constrain(val, min_val, max_val):
    return min(max_val, max(min_val, val))

pygame.init()
display = pygame.display.set_mode((300,300))

UDP_IP = "192.168.137.133"
UDP_PORT = 100

class DATA:
    x = 0
    y = 0
    a = 0
    b = 0
    ch1 = 0
    ch2 = 0
    ch3 = 0
    ch4 = 0


sock = socket.socket(socket.AF_INET, # Internet 
                     socket.SOCK_DGRAM) # UDP
keys = pygame.key.get_pressed()

ArrDATA = array.array('b',[DATA.x, DATA.y, DATA.a, DATA.b, DATA.ch1, DATA.ch2, DATA.ch3, DATA.ch4])        
sock.sendto(ArrDATA, (UDP_IP, UDP_PORT))
lastTime = 0
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    
    keysPrev = keys
    keys = pygame.key.get_pressed() #The PyGame keys function is deranged, I'm sorry about the code that follows. Why can't it just return a string!

    if (keys != keysPrev):
        print("changed")
        DATA.x = 0
        DATA.y = 0
        keyPressed = False

        if keys[pygame.K_w]:
            DATA.x += 127
            DATA.y += 127
            keyPressed = True

        if keys[pygame.K_s]:
            DATA.x -= 127
            DATA.y -= 127
            keyPressed = True

        if keys[pygame.K_a]:
            DATA.x += 127
            DATA.y -= 127
            keyPressed = True

        if keys[pygame.K_d]:
            DATA.x -= 127
            DATA.y += 127
            keyPressed = True

        if keys[pygame.K_q]:
            #Add some servo stuff in empty channels
            keyPressed = True

        if keys[pygame.K_e]:
            #Add some servo stuff in empty channels
            keyPressed = True

        if not(keyPressed):
            DATA.x = 0
            DATA.y = 0
        DATA.x = constrain(DATA.x, -127, 127)
        DATA.y = constrain(DATA.y, -127, 127)
        

        
    if (time.time()-lastTime>0.5 or keys != keysPrev):
        lastTime=time.time()
        print(time.time())
        ArrDATA = array.array('b',[DATA.x, DATA.y, DATA.a, DATA.b, DATA.ch1, DATA.ch2, DATA.ch3, DATA.ch4])
        sock.sendto(ArrDATA, (UDP_IP, UDP_PORT))

## Arduino Code

cpp'''

#include <WiFi.h>  //A collection of objects and functions for using WiFi on the ESP32

WiFiUDP Udp;  //Set up an object that handles UDP

//Here we'll define variables for setting a static IP address. This way, there's no risk of your robot suddenly changing addresses.
IPAddress local_ip(192, 168, 137, 133);  //This is the static IP address that the ESP32 will try to use
IPAddress gateway(192, 168, 1, 1);
IPAddress subnet(255, 255, 0, 0);

byte packetBuffer[255];  //We'll store the bytes from the UDP packet here

unsigned int localPort = 100;  //Port number- make sure this is the same in both the python script and here

const char *ssid = "RUPUTER";        //The SSID of your hotspot, or network name
const char *password = "esp32time";  //The password of your network

class simpleMotor {     //This class can be used to drive a motor
private:                //Methods and variables placed here can't be accessed outside this class
  int resolution = 10;  //This is how many bits should be used for the duty cycle- 10 bits means (1<<10) = 2^10 = 1024 is full speed
  int frequency = 500;  //Frequency of the PWM- this number has a big effect on how your robot moves! I won't fully explain it here, but it's due to how the coils in your motor resist changes in current. Try adjusting this, and see how it reacts.
  int speed;            //The speed the motor is currently set to
  int PWMChannelF;      //The PWM generator to use for the forward signal- which one you use doesn't matter, since they're all the same, however make sure to use a different one for each channel
  int PWMChannelB;      //The PWM generator to use for the backward signal

public:  //Methods and variables here can be called from the main loop
  void setup(int _pinForward, int _pinBackward, int _PWMChannelF, int _PWMChannelB) {
    PWMChannelF = _PWMChannelF;  //_pinBackward only exists inside this function, and is deleted when it ends. Save the number to a variable that is attached to this object.
    PWMChannelB = _PWMChannelB;  //The underscore doesn't do anything- it's just a way to mark the variable as temporary to avoid confusion

    ledcSetup(_PWMChannelF, frequency, resolution);  //Set up the two PWM generators that we'll use to drive the motors.
    ledcSetup(_PWMChannelB, frequency, resolution);

    ledcAttachPin(_pinForward, _PWMChannelF);  //Connect the PWM generators to GPIO pins, as set by _pinForward. This means the number you set when you call this function will be the pin number that outputs this signal.
    ledcAttachPin(_pinBackward, _PWMChannelB);
  }

  void setSpeed(int speed) {  //This function sets the speed of the motor, and reverses it if it's negative. What does the commented out function do? I dunno, wrote it last week.
    speed = constrain(speed, -1<<resolution, 1<<resolution); //Limit speed to 100% on
    if (speed < 0) {
      speed *= -1;                    //The PWM can't make a negative duty wave, set it to positive and send it to the reverse pin
      ledcWrite(PWMChannelF, 0);      //Set the forward pin to zero- it's backward time
      ledcWrite(PWMChannelB, speed);  //Set the duty cycle for the backward pin to the desired speed
    } else if (speed > 0) {
      ledcWrite(PWMChannelB, 0);
      ledcWrite(PWMChannelF, speed);
    } else {
      ledcWrite(PWMChannelF, 0);  //If the speed is zero, turn both pins off. Yes, it could be replaced by simply putting either of the above to ">=" instead of ">"- but there's a reason I haven't
      ledcWrite(PWMChannelB, 0);
    }
    //else{ //You can only have one "else" statement- delete the above if you are using this one
    //  ledcWrite(PWMChannelF, 1<<resolution); //"<<" means bitshift: a<<b == a*(2^b). Here, 1<<resolution (resolution being 10) means 1024- or 100% duty
    //  ledcWrite(PWMChannelB, 1<<resolution);
    //}
  }
};

simpleMotor left;  //Make a motor object, to represent the left motor.
simpleMotor right;
int lastPrint;  //This records the last time the program printed the UDP data it got
int len; //number of bytes recieved 

void setup() {
  Serial.begin(115200);  //Start serial at 115200 baud. Make sure the number at the top right of your serial monitor is the same

  if (!WiFi.config(local_ip, gateway, subnet)) {                      //Try to configure a static IP address. If it doesn't work, print a helpful and informative error message
    Serial.println("Horrible turn of events, no static IP for you");  //TODO: replace with helpful and informative error message
  }

  WiFi.mode(WIFI_STA);         //Set WiFi mode. Station mode (WIFI_STA) means connected to a outside network, instead of broadcasting your own.
  WiFi.begin(ssid, password);  //Start WiFi, using the network name and password we set earlier

  while (WiFi.status() != WL_CONNECTED) {  //Run this code as long as WiFi isn't connected
    Serial.println("connecting");
    delay(500);
  }

  Udp.begin(localPort);            //Start listening on port "localPort", a port number we set earlier
  delay(200);                      //Wait a bit
  Serial.println(WiFi.localIP());  //Print out the IP address we're using

  if (WiFi.localIP() == local_ip) {  //Let's just double check that the whole static IP thing worked
    Serial.println("Static IP set");
  } else {
    Serial.println("Horrible turn of events, no static IP for you");
  }

  left.setup(22, 23, 0, 1);   //These numbers are: the pin for "forwards" on your motor driver, the pin for "backwards" on your motor driver, the channel to use for forward PWM and the channel to use for backward PWM
  right.setup(19, 18, 2, 3);  //The PWM signals will be created on the pins marked 19 and 18 for right motor
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {  //If the network disconnects, for any reason
    WiFi.begin(ssid, password);         //Start WiFi again

    while (WiFi.status() != WL_CONNECTED) {  //Until we've reconnected
      Serial.println("reconnecting");
      delay(500);
    }
    Serial.println(WiFi.localIP());  //Reprint the IP address
  }

  int packetSize = Udp.parsePacket();  //Grab the packet data. The actual data is stored inside the Udp object, but the function returns a number stored in packetSize that is bigger than zero if there is data

  if (packetSize) {                         //If packet size isn't zero, ie if there is data
    len = Udp.read(packetBuffer, 255);  //Take everything out of the packet, and put it in our buffe
    for (int i=0; i<packetSize; i++){
      //Serial.print((int8_t)packetBuffer[i]);
      //Serial.print(" ");
    }
    //Serial.println();
  }

  /* Here's a lil bit of code that will print the commands six times a second, or if there's an update. Handy.
  if (millis()-lastPrint>150 || packetSize){ //Millis() returns the number of milliseconds the program has run for. If this is more than 150 since the last time it ran, run it again. || is the symbol for "or"
    lastPrint = millis(); //Set the last time it ran to now, since it's running now
    Serial.println(packetBuffer);
  }
  */

  int speedLeft = 4*(int8_t)packetBuffer[0];
  int speedRight = 4*(int8_t)packetBuffer[0];
  left.setSpeed(speedLeft); //Off to the races
  right.setSpeed(speedRight);  //The packet is of datatype byte- this goes from 0-255. We want -127 to 128, so we'll use (int8_t) to convert it 



  delay(25);
}
'''
