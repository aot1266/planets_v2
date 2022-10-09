import pygame as pg
import numpy as np
from Game_core_v1 import game 
from moveable_objs import player

#control game -------------------------------------------
pg.init()
#define the screen 
screen = pg.display.set_mode((800,600))#control game -------------------------------------------
pg.init()

player_main = player(np.array([0.0,0.0]), np.array([0.0,0.0]), 2.0, [np.array([0.0,0.1])], [], [1,1,1])
#game_main = game(player_main, "input_data_7_2.json", "stars_data.json", screen)
game_main = game(player_main, "input_data_demo.json", "stars_data.json", screen)
#game_main.water_surface = pg.Surface((800,600))
#game_main.water_surface.set_alpha(0.2)

# Run until the user asks to quit
running = True
while running:

    # Did the user click the window close button?
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False

    # Fill the background with white
    game_main.screen.fill((0, 0, 0))

    #player movement and actions
    keys = pg.key.get_pressed()
    if game_main.player.contact_flag == 1 or game_main.player.water_contact_flag == 1:
        events = pg.event.get()
        if keys[pg.K_LEFT]: # We can check if a key is pressed like this
            game_main.player.move_keys[0] = 1
        else:
            game_main.player.move_keys[0] = 0
        if keys[pg.K_RIGHT]:
            game_main.player.move_keys[1] = 1
        else:
            game_main.player.move_keys[1] = 0
        if keys[pg.K_SPACE]:
            game_main.player.move_keys[2] = 1
        else:
            game_main.player.move_keys[2] = 0     
        #action for moving planet
        if keys[pg.K_w]:
            game_main.player.action_keys[1] = 1
        else:   
            game_main.player.action_keys[1] = 0
    else:
        game_main.player.move_keys = [0,0,0,0]

    #general action 
    if keys[pg.K_q]:
        game_main.player.action_keys[0] = 1
    else:
        game_main.player.action_keys[0] = 0
    #climb action 
    if keys[pg.K_UP]:
        game_main.player.action_keys[2] = 1
    elif keys[pg.K_DOWN]:
        game_main.player.action_keys[2] = -1
    else:
        game_main.player.action_keys[2] = 0    
    #action for zooming 
    if keys[pg.K_z]:
        game_main.window_scale_val -= 0.01
    if keys[pg.K_x]:
        game_main.window_scale_val += 0.01
    #action for aiming
    if keys[pg.K_a]:
        game_main.player.aim_keys[0] = 1
    if keys[pg.K_d]:
        game_main.player.aim_keys[1] = 1   
    if keys[pg.K_s]:
        game_main.player.aim_keys[2] = 1   
    if keys[pg.K_f]:
        game_main.player.aim_keys[2] = -1   
                
    #main game step 
    game_main.load_step()
    # for planet in game_main.planet_list:
    #     print(planet.pos, type(planet.pos))
    game_main.step()
    game_main.screen_step()
    # Flip the display
    pg.display.flip()

# Done! Time to quit.
pg.quit()            