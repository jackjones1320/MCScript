from minescript import *
import sys
import time
import math

#Important information

#player_press_left decreases z, player_press_right increases z



#Continus loop
while True:
    pos = player_position()
    x = pos[0]
    y = pos[1]
    z = pos[2]

    player_press_attack(True)
    player_press_forward(True)
    # Walk right
    if math.floor(z) == 239:
        player_press_right(False)
        # Finish and warp
        if math.ceil(x) == -55:
            chat("/warp garden")
        else:
            player_press_left(True)

    # Walk left
    if math.ceil(z) == -239:
        player_press_left(False)
        player_press_right(True)

    time.sleep(0.05)
