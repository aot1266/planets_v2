import numpy as np
import pandas as pd
import copy as cp
from core_fns import absval, cart2pol, pol2cart, vec_comp, orth_vec, line_intersection, intersection, orth_vec
from npc_control import conv_step, emotion_step, physical_step, heuristic_step

#obj class
class obj_moveable:
    def __init__(self, obj_id, obj_type, pos, vel, mass, geom):
        self.screen_pos = np.zeros(2)        
        self.pos = pos
        self.vel = vel
        self.mass = mass
        self.geom = geom
        self.obj_id = obj_id
        self.obj_type = obj_type
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
                self.jump_force += 0.4
                print('jf ',self.jump_force)
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

    # def NPC_step(self):
    #     #run npc loop in here 
    #     pass
          
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
    def __init__(self, obj_id, obj_type, pos, vel, mass, geom, state, inventory):
        super().__init__(obj_id, obj_type, pos, vel, mass, geom)
        self.inventory = inventory
        self.prev_action_keys = [0,0,0,0]
        self.close_planet_obs_list = []
        self.close_planet_obs_list_2 = []
        
        self.inside_flag = 0
        self.outside_pos = None
        self.indide_room = None
        self.prev_inside_flag = 0
        
        self.action_state = 0
        
        #internal state
        #type of behaviour setup 0- heuristic 
        self.behaviour_type = 0
        #home and work locations - planet, object list 
        self.home_planet = None
        self.home = None
        self.work = None
        self.work_planet = None
        self.work_location = None
        #personality params intelligence impulse anger  
        self.personal_params = np.array([0.0,0.0,0.0])
        #emotional state happy/sad calm/angry love/hate interest/bored
        self.emotion_state = np.array([0.0,0.0,0.0,0.0])
        #physical_state tired hunger amusement 
        self.physical_state = np.array([0.0,0.0,0.0])
        # null 0 sleep 1 rest 2 eat 3 work 4
        self.activity_flag = 0
        self.prev_activity_flag = 0
        self.change_action_prob = None
        self.end_action_prob = None 
        
        #conv params 
        self.conv_flag = 0
        self.conv_keys = [0,0,0,0,0]
        self.prev_conv_keys = [0,0,0,0,0]
        self.conv_npc = None
        self.conv_text_options = None
        self.conv_phrase = None
        self.conv_input_phrase = None
        
    #def heuristic_step()
        
    def action_fn(self, planet_list):
        if self.action_keys[1] == 1:
            self.contact_flag_obj.force += 0.1*self.down
            #add force to linked planets
            for other_planet in self.contact_flag_obj.planet_linked_list:
                other_planet.force += 0.1*self.down
            
        #general action   
        if self.action_keys[0] == 1 and self.prev_action_keys[0] != 1:
            inside_change_flag = 0
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
                inside_change_flag = 1
                
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
                        if self.inside_flag == 0 and inside_change_flag == 0:
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
        #update prev inside flag
        #self.prev_inside_flag = self.inside_flag
        #reset aim keys 
        self.aim_keys = [0,0,0]
        
    def npc_step(self): 
        physical_step(self)
        emotion_step(self)
        heuristic_step(self)
    
    def get_conv_options(self):
        return [['Hello',0],['Screw you',-0.5],['The answer is ten',0],['the bread is made fresh',0],['the bread is excellent asshole', -0.2]]
        
    def reset_conv(self):
        self.conv_flag = 0
        self.conv_npc = None     
    
    def npc_conv(self, object_list, conv_rad):
        #set for conversation 
        for obj in object_list:
            if obj.obj_type in ['npc', 'player']:
                if obj.obj_id != self.obj_id:
                    #set the conv flag
                    if ((self.conv_keys[0] == 1 or obj.conv_keys[0] == 1)
                    and absval(self.pos - obj.pos) < conv_rad):
                        self.conv_flag = 1
                        obj.conv_flag = 1
                        self.conv_npc = obj.obj_id
                        obj.conv_npc = self.obj_id
                    #reset conv flag
                    elif ((self.conv_keys[0] == 0 and obj.conv_keys[0] == 0) 
                    or absval(self.pos - obj.pos) < 1.5*conv_rad):
                        self.reset_conv()
                        obj.reset_conv()
                        if absval(self.pos - obj.pos) < 1.5*conv_rad:
                            self.conv_keys[0] = 0
                            obj.conv_keys[0] = 0
                    #set the conv phrase
                    if self.conv_flag == 1 and self.obj_type == 'npc':
                        if obj.conv_phrase != None:
                            self.conv_input_phrase = obj.conv_phrase
                            #get response
                            self.conv_phrase = conv_step(self)
                            print(self.conv_phrase)

    
#player class 
class player(NPC):
    def __init__(self, obj_id, obj_type, pos, vel, mass, geom, state, inventory):
        super().__init__(obj_id, obj_type, pos, vel, mass, geom, state, inventory)
        self.inventory = inventory
        #move_keys        
        #print('move keys 1',self.move_keys)
      
    def action_fn(self, planet_list):
        super().action_fn(planet_list)
       
    def get_conv_options(self):
        return ['Hello','Fuck Off','Question','Tell me about the bread','Is your bread any good or is it as shit as it looks']
    
    def reset_conv(self):
        super().reset_conv()
        self.conv_phrase = None
        self.conv_text_options = None
        
    def npc_conv(self, object_list, conv_rad):
        super().npc_conv(object_list, conv_rad)
        if self.conv_flag == 1:
            self.conv_text_options = self.get_conv_options()
            #get selection ind
            if self.prev_conv_keys[1] == 0 and self.conv_keys[1] == 1:
                self.conv_keys[3] += 1
                self.conv_keys[3] = self.conv_keys[3]%len(self.conv_text_options)
            if self.prev_conv_keys[2] == 0 and self.conv_keys[2] == 1:
                self.conv_keys[3] -= 1
                self.conv_keys[3] = self.conv_keys[3]%len(self.conv_text_options) 
            #select phrase
            if self.prev_conv_keys[4] == 0 and self.conv_keys[4] == 1: 
                self.conv_phrase = self.conv_text_options[self.conv_keys[3]]
                
            