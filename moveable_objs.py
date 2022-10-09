import numpy as np
import pandas as pd
import copy as cp
from core_fns import absval, cart2pol, pol2cart, vec_comp, orth_vec, line_intersection, intersection, orth_vec

#obj class
class obj_moveable:
    def __init__(self, pos, vel, mass, geom):
        self.screen_pos = np.zeros(2)        
        self.pos = pos
        self.vel = vel
        self.mass = mass
        self.geom = geom
        #forces
        self.g_force = np.zeros(2)
        self.m_force = np.zeros(2)
        self.h_force = np.zeros(2)
        self.force = np.zeros(2)
        self.n_force = np.zeros(2)
        #speed
        self.m_speed = 0.0
        self.h_speed = 0.0
        #speed vals
        self.max_speed = 1.8
        self.speed_step = self.max_speed/3
        #down front vectors
        self.down = np.array([0.0,1.0])
        #contact flag
        self.contact_flag = 0
        self.contact_flag_obj = None
        self.move_flag = 0
        self.water_contact_flag = 0
        #grav flag 
        self.grav_flag = 1
        #move_keys
        self.move_keys = [0,0,0,0]
        self.prev_move_keys = [0,0,0,0]
        #action keys: action, dive, 
        self.action_keys = [0,0,0,0]
        self.aim_keys = [0,0,0]
        #------------------intersect_point 
        self.intersect_point = np.zeros(2)
        #attacking/projectile flag 
        self.projectile = False
        
        self.jump_force = 0.0
        self.max_jump_force = 30.0
        
        self.TEST_move_flags_list = []

    def move_force(self):
        self.move_flag = 0
        if self.move_keys[0] == 1:
            if self.m_speed > -self.max_speed:
                self.m_speed += -self.speed_step
                self.move_flag = 1
        if self.move_keys[1] == 1:
            if self.m_speed < self.max_speed:
                self.m_speed += self.speed_step
                self.move_flag = 1                           
        if self.move_keys[2] == 1:
            if self.prev_move_keys[2] == 0:
                self.jump_force += 0.3*self.max_jump_force
            elif self.jump_force < self.max_jump_force:
                self.jump_force += 0.01
            #self.vel = -10*self.down + 1.5*self.m_speed*(orth_vec(self.down))
        if self.prev_move_keys[2] == 1 and self.move_keys[2] == 0:
            self.vel = -1*self.jump_force*self.down# + self.m_speed*(orth_vec(self.down)) 
            self.jump_force = 0.0
        #water dive force
        #print('move keys ',self.move_keys)
        if self.water_contact_flag == 1:
            if self.action_keys[2] == -1 and self.move_keys[2] == 1:
                self.vel = 0.5*self.jump_force*self.down
            
        #self.TEST_move_flags_list.append(self.move_keys.copy())
        #if len(self.TEST_move_flags_list)>32:
        #    self.TEST_move_flags_list = self.TEST_move_flags_list[-30]
        #self.prev_move_keys =self.move_keys.copy()

    def NPC_step(self):
        #run npc loop in here 
        pass
          
    def action_fn(self, planet_list):
        pass
    #     if self.action_keys[1] == 1:
    #         self.contact_flag_obj.force += 0.1*self.down
            
    #     #general action   
    #     if self.action_keys[0] == 1:
    #         #get distance from planet 
    #         rel_dist = self.pos - self.contact_flag_obj.pos
    #         rel_pol_dist = cart2pol(rel_dist[0],rel_dist[1])
    #         #get the action
    #         # for planet_obj in self.contact_flag_obj.planet_obj_list:
    #         #     if (-0.1*np.pi + planet_obj.rel_pos[1] <= rel_pol_dist[1] <= 0.1*np.pi + planet_obj.rel_pos[1] 
    #         #     and rel_pol_dist[0] >= 0.8*planet_obj.rel_pos[0] and rel_pol_dist[0] <= planet_obj.rel_pos[0] + planet_obj.height):                 
    #         #         if planet_obj.obj_type != 'ladder':                        
    #         #             planet_obj.state = 1
    #         #             print('state', planet_obj.state) 
    #         #         else:
    #         #             print('test')
                        
    #     #ladder climb action 
    #     if self.action_keys[0] == 1:
    #         #get distance from planet 
    #         rel_dist = self.pos - self.contact_flag_obj.pos
    #         rel_pol_dist = cart2pol(rel_dist[0],rel_dist[1])
    #         #get the action
    #         # for planet_obj in self.contact_flag_obj.planet_obj_list:
    #         #     if planet_obj.obj_type == 'ladder':
    #         #         if (-0.1*np.pi + planet_obj.rel_pos[1] <= rel_pol_dist[1] <= 0.1*np.pi + planet_obj.rel_pos[1] 
    #         #         and rel_pol_dist[0] >= 0.8*planet_obj.rel_pos[0] and rel_pol_dist[0] <= planet_obj.rel_pos[0] + planet_obj.height):                 
    #         #             self.pos += 5*rel_dist/absval(rel_dist)     

#npc class
class NPC(obj_moveable):
    def __init__(self, pos, vel, mass, geom, state, inventory):
        super().__init__(pos, vel, mass, geom)
        self.inventory = inventory
        self.prev_action_keys = [0,0,0,0]
        self.close_planet_obs_list = []
        self.close_planet_obs_list_2 = []
        
        self.inside_flag = 0
        self.outside_pos = None
        self.indide_room = None
        self.prev_inside_flag = 0
        
        self.action_state = 0
        
    def action_fn(self, planet_list):
        if self.action_keys[1] == 1:
            self.contact_flag_obj.force += 0.1*self.down
            #add force to linked planets
            for other_planet in self.contact_flag_obj.planet_linked_list:
                other_planet.force += 0.1*self.down
            
        #general action   
        if self.action_keys[0] == 1 and self.prev_action_keys[0] != 1:
            print('q')
            #get distance from planet 
            rel_dist = self.pos - self.contact_flag_obj.pos
            rel_pol_dist = cart2pol(rel_dist[0],rel_dist[1])
            
            #get case if inside room then exit 
            if self.inside_flag == 1:
                self.inside_room = None
                self.inside_flag = 0
                self.pos = cp.deepcopy(self.outside_pos)
                self.prev_inside_flag = 1
                #reset inside flags 
                for planet_obj in self.contact_flag_obj.planet_obj_list:
                    planet_obj.state = 0
                
            #get the action
            for planet_obj in self.contact_flag_obj.planet_obj_list:
                #get if close to object 
                if (-0.1*np.pi + planet_obj.rel_pos[1] <= rel_pol_dist[1] <= 0.1*np.pi + planet_obj.rel_pos[1] 
                and rel_pol_dist[0] >= 0.8*planet_obj.rel_pos[0] and rel_pol_dist[0] <= planet_obj.rel_pos[0] + planet_obj.height):                 
                    
                    #anchor aim 
                    if planet_obj.obj_type == 'anchor':
                        #enter aiming state
                        if planet_obj.state == 0:
                            self.action_state = 1
                            planet_obj.state = 1
                        #fire 
                        if planet_obj.state == 1:                                                       
                            if self.aim_keys[2] == 1: 
                                planet_obj.state = 2
                                planet_obj.anchor_fire(planet_list)
                        #recall                       
                        if planet_obj.state >= 1:
                            if self.aim_keys[2] == -1:
                                planet_obj.state = 1
                                planet_obj.anchor_reset()
                            
                    #cannon load and fire
                    elif planet_obj.obj_type == 'cannon': 
                        if planet_obj.state == 0:
                            #print('inventory ',self.inventory)
                            #will need to rework to change what 
                            if self.inventory != []:
                                self.inventory.pop(0)
                                planet_obj.state = 1
                        elif planet_obj.state == 1 and self.prev_action_keys[0] == 0: 
                            #signals to fire in main loop 
                            planet_obj.state = 2  
                    #ladder 
                    elif planet_obj.obj_type == 'ladder':
                        if planet_obj not in self.close_planet_obs_list:
                            self.close_planet_obs_list.append(planet_obj)
                            
                    #room handling
                    elif planet_obj.obj_type == 'room':
                        planet_obj.state = 1 
                        #planet_obj.state = planet_obj.state % 2
                        self.inside_flag = planet_obj.state
                        if self.inside_flag == 1 and self.prev_inside_flag == 0:
                            self.outside_pos = self.pos.copy()
                        print('inside flag A ',self.inside_flag)
                        if planet_obj.state == 1:
                            self.inside_room = planet_obj.room_index
                        else:
                            self.inside_room = None 
                    else:  
                        planet_obj.state = 1
                        print('state', planet_obj.state) 
        
        #aim anchor 
        if self.aim_keys[0] == 1 or self.aim_keys[1] == 1 or self.aim_keys[2] == 1 or self.aim_keys[2] == -1:
            for planet_obj in self.contact_flag_obj.planet_obj_list:
                #get distance from planet 
                rel_dist = self.pos - self.contact_flag_obj.pos
                rel_pol_dist = cart2pol(rel_dist[0],rel_dist[1])
                
                if planet_obj.obj_type == 'anchor':
                    #enter aiming state
                    if planet_obj.state == 1:
                        #get if close to object 
                        if (-0.1*np.pi + planet_obj.rel_pos[1] <= rel_pol_dist[1] <= 0.1*np.pi + planet_obj.rel_pos[1] 
                        and rel_pol_dist[0] >= 0.8*planet_obj.rel_pos[0] and rel_pol_dist[0] <= planet_obj.rel_pos[0] + planet_obj.height):                 
                            if self.aim_keys[0] == 1:
                                planet_obj.aim_angle += -1*planet_obj.aim_step
                            if self.aim_keys[1] == 1:
                                planet_obj.aim_angle += planet_obj.aim_step                                                        
                            if self.aim_keys[2] == 1: 
                                planet_obj.state = 2
                    if self.aim_keys[2] == -1:
                        planet_obj.state = 1
                        planet_obj.anchor_reset()
        #anchor fire
        for planet_obj in self.contact_flag_obj.planet_obj_list:        
            if planet_obj.obj_type == 'anchor':
                if planet_obj.state == 2:
                    planet_obj.anchor_fire(self.contact_flag_obj, planet_list)                           
            
        #climb option
        if self.action_keys[2] == 1:
            #get distance from planet 
            rel_dist = self.pos - self.contact_flag_obj.pos
            rel_pol_dist = cart2pol(rel_dist[0],rel_dist[1])
            #get the action
            for planet_obj in self.contact_flag_obj.planet_obj_list:
                if planet_obj.obj_type == 'ladder':
                    if (-0.1*np.pi + planet_obj.rel_pos[1] <= rel_pol_dist[1] <= 0.1*np.pi + planet_obj.rel_pos[1] 
                    and rel_pol_dist[0] >= 0.8*planet_obj.rel_pos[0] and rel_pol_dist[0] <= planet_obj.rel_pos[0] + planet_obj.height):                 
                        if planet_obj not in self.close_planet_obs_list:
                            self.close_planet_obs_list.append([planet_obj,self.contact_flag_obj])       
                            self.close_planet_obs_list_2.append(self.contact_flag_obj)
        
        #print('111111----- ',self.close_planet_obs_list)
        for planet_obj_entry in self.close_planet_obs_list:
            #print('pp ',planet_obj_entry)
            #print(t)
            planet_obj = planet_obj_entry[0]
            planet = planet_obj_entry[1]
            if self.action_keys[2] == 1:
                print(self.action_keys)
            if planet_obj.obj_type == 'ladder':
                #get distance from planet 
                rel_dist = self.pos - self.contact_flag_obj.pos
                rel_pol_dist = cart2pol(rel_dist[0],rel_dist[1])
                if (-0.008*np.pi + planet_obj.rel_pos[1] <= rel_pol_dist[1] <= 0.008*np.pi + planet_obj.rel_pos[1] 
                and rel_pol_dist[0] >= 0.8*planet_obj.rel_pos[0] and rel_pol_dist[0] <= planet_obj.rel_pos[0] + planet_obj.height):                 
                #     print(self.force, self.force + self.m_force, self.m_force)
                #     print('force 2', self.force/absval(self.force), self.m_force/absval(self.m_force), self.down)
                    if self.action_keys[2] == 1:    
                         self.force = np.zeros(2)
                         self.force += planet.force
                         self.force += self.down*(-1.2) 
                         self.force += self.m_force
                         self.vel = np.zeros(2)
                         self.contact_flag = 1 
                    elif self.action_keys[2] == -1: 
                         self.force = np.zeros(2)
                         self.force += planet.force
                         self.force += self.down*(1.2) 
                         self.vel = np.zeros(2)
                         self.contact_flag = 1
                    elif rel_pol_dist[0] >= planet_obj.rel_pos[0] + 0.1:
                         self.force = np.zeros(2)
                         self.force += planet.force
                         self.force += self.m_force
                         self.vel = np.zeros(2)
                         self.contact_flag = 1
                    if self.move_keys[1] == 0 and self.move_keys[0] == 0:
                        self.m_speed = 0.0
                        
        #update prev action keys
        self.prev_action_keys = self.action_keys.copy()     
        #reset aim keys 
        self.aim_keys = [0,0,0]
        
    def npc_step(self): 
        pass

#player class 
class player(NPC):
    def __init__(self, pos, vel, mass, geom, state, inventory):
        super().__init__(pos, vel, mass, geom, state, inventory)
        self.inventory = inventory
        #move_keys        
        #print('move keys 1',self.move_keys)
      
    def action_fn(self, planet_list):
        super().action_fn(planet_list)