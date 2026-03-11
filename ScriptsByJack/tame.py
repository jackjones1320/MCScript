from minescript import *
import sys
import time
import math
import threading
import random

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

while (True):
    if math.floor(elapsed) != 0 & math.floor(elapsed) % 3 == 0:
        hotbar3()
    if math.floor(elapsed) != 0 & math.floor(elapsed) % 31 == 0:
        hotbar4()
        
    player_press_attack(True)
    player_press_attack(False)
    
    time.sleep(random_float_in_range(0.05, 0.1))
