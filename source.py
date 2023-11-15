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
