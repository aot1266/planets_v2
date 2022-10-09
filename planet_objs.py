import numpy as np
import pandas as pd
import pygame as pg
from core_fns import absval, cart2pol, pol2cart, vec_comp, orth_vec, line_intersection, intersection
from core_contact import planet_anchor_contact

#planet class
class obj_planet:
    def __init__(self, pos, vel, mass, geom, planet_obj_list, water_obj_list, planet_linked_list, grav_flag, planet_id):
        self.planet_id = planet_id
        #positional args
        self.screen_pos = np.zeros(2)
        self.pos = pos
        self.vel = vel
        self.mass = mass
        #geom form (p1 (ro, phi), p2, type, mu)
        self.geom = geom
        #planet objects
        self.planet_obj_list = planet_obj_list
        for planet_obj in self.planet_obj_list:
            planet_obj.rel_pos = [self.get_rad(planet_obj.cart_pos[1]) + planet_obj.cart_pos[0],2*np.pi - planet_obj.cart_pos[1]]
            #get the direction 
            planet_obj.dir = orth_vec(pol2cart(planet_obj.rel_pos[0],planet_obj.rel_pos[1]) - self.pos)/absval(pol2cart(planet_obj.rel_pos[0],planet_obj.rel_pos[1]) - self.pos)
        #water objects
        self.water_obj_list = water_obj_list
        for water_obj in self.water_obj_list:
            water_obj.planet = self
            #rel pos of list
            water_obj.rel_points = []
            for water_point in water_obj.points:
                water_obj.rel_points.append(np.array([self.get_rad(water_point[1]) + water_point[0],water_point[1]]))    
        #linked planets
        self.planet_linked_list = planet_linked_list
        #forces
        self.g_force = np.zeros(2)
        self.m_force = np.zeros(2)
        self.n_force = np.zeros(2)
        self.force = np.zeros(2) + vel
        #grav radius
        self.g_max_rad = mass*20*max([geom_point[0][0] for geom_point in geom])
        #max radius
        self.max_rad = max([geom_point[0][0] for geom_point in geom])
        self.min_rad = min([geom_point[0][0] for geom_point in geom])
        self.rad_diff = self.max_rad - self.min_rad
        #attack flag
        self.attack_flag = 0
        #health vals
        self.health = 1.0
        #grav flag 
        self.grav_flag = grav_flag
        #outside_vel
        self.outside_vel = None
        #planet atmos surfaces 
        self.atmos_surface = pg.Surface((800,600), pg.SRCALPHA)
        
    def grav_force(self, dist):
        return self.mass/(dist**2)
    
    def grav_planet_force(self, p2, dist):
        return 0.2*(self.mass*p2.mass)/(dist**2)   
    
    def get_rad(self, angle):
        rad = 0
        for point in self.geom:
            max_rad = max([point[0][0],point[1][0]])
            if point[0][1] < angle <= point[1][1]:   
                if point[2] == 'arc':
                    rad = point[0][0]

                if point[2] == 'line':
                    diff_rad = point[1][0] - point[0][0]
                    diff_phi = point[1][1] - point[0][1]
                    min_rad = min([point[1][0], point[0][0]])
                    #get the intersect point
                    intersect_point = line_intersection([np.array([0.0,0.0]),pol2cart(1.2*max_rad,angle)], [np.array(pol2cart(point[0][0],point[0][1])),np.array(pol2cart(point[1][0],point[1][1]))])
                    rad = absval(intersect_point)
                return rad

#planet dumb object class
class on_planet_obj:
    def __init__(self, cart_pos, height, state, obj_type):
        #position describes as [additional rad, angle]
        self.cart_pos = cart_pos
        self.rel_pos = np.zeros(2)
        self.dir = np.zeros(2)
        self.height = height
        self.state = state 
        self.obj_type = obj_type
        if self.obj_type == 'room':
            self.room_index = None
        #planet image
        self.img = None
  
        
class on_planet_anchor(on_planet_obj):
    def __init__(self, cart_pos, height, state, obj_type, deploy_max_len, planet_pos):
        super().__init__(cart_pos, height, state, obj_type)
        self.deploy_max_len = deploy_max_len 
        self.deploy_len = 0.0
        self.aim_step = 2*np.pi/200
        self.aim_angle = 0.0 
        
        self.hooked_flag = 0
        self.hooked_obj = None
        self.hooked_pos = None
        self.hooked_rad = None
        self.fire_flag = 0
        
        self.pos = planet_pos +  np.array(pol2cart(self.rel_pos[0], self.rel_pos[1]))
        
    def anchor_reset(self):
        self.state = 1
        self.deploy_len = 0.0
        self.hooked_flag = 0
        self.hooked_obj = None
        self.hooked_rel_obj_point = None
        self.hooked_pos = None
        self.hooked_rad = None
        self.fire_flag = 0
        
    def anchor_fire(self, on_planet, planet_list):#, planet_list):
        self.fire_flag = 1
        if self.hooked_obj == None and self.deploy_len < self.deploy_max_len:
            self.deploy_len += 5
        else:
            self.state = 3
        #get pos of the end 
        self.hooked_pos = on_planet.pos + np.array(pol2cart(self.rel_pos[0],self.rel_pos[1])) + np.array(pol2cart(self.deploy_len, self.aim_angle))
        self.anchor_contact_test(on_planet, planet_list)
        #if hooked set point 

    def anchor_contact_test(self, on_planet, planet_list):
        for planet in planet_list:
            if planet != on_planet:
                #get planet vector 
                planet_hooked_pos_vec = self.hooked_pos - planet.pos
                #if absval(planet_hooked_pos_vec) < 1.5*planet.max_rad:
                planet_anchor_contact(planet, self)
                
    def anchor_step(self, on_planet):
        if self.state == 3 and self.hooked_obj != None:
            #update hooke_pos 
            self.hooked_pos = self.hooked_obj.pos + self.hooked_rel_obj_point
            self.pos = on_planet.pos + np.array(pol2cart(self.rel_pos[0],self.rel_pos[1]))
            self.anchor_vec = self.hooked_pos - self.pos
            #get distance between the anchor and the hooked obj 
            
            if self.deploy_len <= absval(self.pos - (self.hooked_obj.pos - self.hooked_rel_obj_point)):
                #get total planet mass 
                total_planet_mass = self.hooked_obj.mass + on_planet.mass
                #get total vel 
                total_vel = (self.hooked_obj.mass/total_planet_mass)*self.hooked_obj.vel + (on_planet.mass/total_planet_mass)*on_planet.vel 
                total_force = self.hooked_obj.force + on_planet.force
                
                if abs(sum(self.hooked_obj.force)) > 0.0: 
                    self.hooked_obj.force += -1*(on_planet.mass/total_planet_mass)*vec_comp(self.hooked_obj.force, self.anchor_vec)*(self.anchor_vec/absval(self.anchor_vec))
                if abs(sum(on_planet.force)) > 0.0: 
                    #print('vec comp ', vec_comp(on_planet.force, self.anchor_vec)*(self.anchor_vec/absval(self.anchor_vec)))
                    on_planet.force += -1*(self.hooked_obj.mass/total_planet_mass)*vec_comp(on_planet.force, self.anchor_vec)*(self.anchor_vec/absval(self.anchor_vec))

                #self.hooked_obj.force += -1*(on_planet.mass/total_planet_mass)*vec_comp(total_force, self.anchor_vec)
                #on_planet.force += -1*(self.hooked_obj.mass/total_planet_mass)*vec_comp(total_force, self.anchor_vec)
                                               
                #on_planet.vel = (on_planet.mass/total_planet_mass)*total_vel
                
                
class on_planet_ladder(on_planet_obj):
    def __init__(self, cart_pos, polar_theta, polar_radius, height, state, obj_type):
        super().__init__(cart_pos, height, state, obj_type)
        self.polar_theta = polar_theta
        self.polar_radius = polar_radius
        
class on_planet_display(on_planet_obj):
    def __init__(self, cart_pos, height, state, obj_type, target_obj_id):
        super().__init__(cart_pos, height, state, obj_type)
        self.target_obj_id = target_obj_id 
        self.display_subj = None
        #counter if state = 1
        if self.state == 1:
            self.counter_val = None
    
    def get_counter_target(self, planet_list):
        self.target_obj = [obj for obj in planet_list if obj.planet_id == self.target_obj_id][0]
        
    #just for counter 
    def counter_step(self, planet_pos):
        #print('target obj pos ', self.target_obj.pos)
        obj_dist = planet_pos - self.target_obj.pos
        angle = int(np.degrees((np.pi - self.cart_pos[1]) - cart2pol(obj_dist[0], obj_dist[1])[1]))%360
        if angle < 10:
            angle_str = "00"+str(angle)
        elif angle < 100:
            angle_str = "0"+str(angle)
        else:
            angle_str = str(angle)
        self.counter_val = angle_str
        
        
#planet room 
class on_planet_room(on_planet_obj):
    def __init__(self, cart_pos, geom, height, state, obj_type, room_index):
        super().__init__(cart_pos, height, state, obj_type)
        self.room_index = room_index 
        #self.room_data_dict = room_data_dict
        
#water 
class on_planet_water:
    def __init__(self, arc_start ,arc, rad, planet_pos):
        self.rad = rad
        self.arc_start = arc_start
        self.arc = arc
        #self.planet_id = planet_id
        self.planet_pos = planet_pos
        #self.no_points = int(np.floor(arc/(0.05*np.pi)))
        self.no_points = int(np.floor(arc/(0.02*np.pi)))
        arc_delta = arc/self.no_points
        self.points = [[float(rad),arc_start+i*arc_delta] for i in range(self.no_points)]
        self.orig_points = [[float(rad),arc_start+i*arc_delta] for i in range(self.no_points)]
        self.rel_points = None
        self.planet = None
        
    def water_step(self, planets_list):
        point_force_list = []
        for point in self.orig_points:
            #get grav force at points
            point_force = 0.0
            for planet in planets_list:
                #if planet. != self.planet:
                point_planet_dist = absval((self.planet.pos + pol2cart(point[0],point[1])) - planet.pos)
                #point_force += planet.grav_force(point_planet_dist)**6
                point_force += planet.grav_force(point_planet_dist)**4
            point_force_list.append(point_force)
        #norm the force
        norm_point_force_list = ((point_force_list/np.mean(point_force_list)) - 0.5)*2
        norm_point_force_list = [min(norm_point,3.5) for norm_point in norm_point_force_list]
        #amend the points values 
        for norm_point_ind, norm_point_force in enumerate(norm_point_force_list):
            self.points[norm_point_ind] = [0.97*self.rad + 0.03*self.rad*norm_point_force,self.points[norm_point_ind][1]]

        self.rel_points = []
        for water_point in self.points:
            self.rel_points.append(np.array([water_point[0],water_point[1]]))    
    
        #sin the force points 
        sin_point_force_list = [5*np.sin(point_f*6) for point_f in norm_point_force_list]
        for sin_ind, sin_point in enumerate(sin_point_force_list):
            self.rel_points[sin_ind][0] += sin_point