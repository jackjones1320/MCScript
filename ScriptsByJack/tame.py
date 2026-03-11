from minescript import *
import sys
import time
import math
import threading
import random


start_pov = player_orientation()
start_yaw = pov[0]
start_time = time.time()
elapsed = 0

    
def hotbar3():
    player_inventory_slot_to_hotbar(3)
    player_press_use(True)
    player_press_use(False)
    
def hotbar4():
    player_inventory_slot_to_hotbar(4)
    player_press_use(True)
    player_press_use(False)
    
def randomness(yaw):
    pov = player_orientation()
    pitch = pov[0]
    if pitch == 0:
        player_set_orientation(yaw,random_float_in_range(-1.0,1.0))
    else:
        player_set_orientation(yaw,0)

def hotbarmanagement():
    while (True):
        #Hotbar 3 every 3 seconds
        if math.floor(elapsed) != 0 and math.floor(elapsed) % 3 == 0:
            hotbar3()
            time.sleep(1)
            
        #Change yaw for randomness every 15 seconds
        if math.floor(elapsed) != 0 and math.floor(elapsed) % 15 == 0:
            randomness(start_yaw)
            time.sleep(1)
            
        #Hotbar 4 every 31 seconds
        if math.floor(elapsed) != 0 and (math.floor(elapsed) % 31 == 0 or elapsed > 31):
            hotbar4()
            time.sleep(1)
            elapsed = 0
        
        player_press_attack(True)
        player_press_attack(False)
        
        time.sleep(random_float_in_range(0.05, 0.1))
    
def movement():
    while (True):
        move = random_float_in_range(1.0,2.0)
        player_press_left(True)
        time.sleep(move)
        player_press_left(False)
        player_press_right(True)
        time.sleep(move)
        player_press_right(True)
        
        
t1 = threading.Thread(target=hotbarmanagement, args=(...,))
t2 = threading.Thread(target=movement, args=(...,))

t1.start()
t2.start()
t1.join()
t2.join()

