import numpy as np
import pandas as pd
from core_fns import absval, cart2pol, pol2cart, vec_comp, orth_vec, line_intersection, intersection

#planet class
class obj_planet:
    def __init__(self, pos, vel, mass, geom, planet_obj_list, water_obj_list, planet_linked_list, grav_flag):
        self.screen_pos = np.zeros(2)
        self.pos = pos
        self.vel = vel
        self.mass = mass
        #geom form (p1 (ro, phi), p2, type, mu)
        self.geom = geom
        #planet objects
        self.planet_obj_list = planet_obj_list
        for planet_obj in self.planet_obj_list:
            planet_obj.rel_pos = [self.get_rad(planet_obj.cart_pos[1]) + planet_obj.cart_pos[0],planet_obj.cart_pos[1]]
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
        #attack flag
        self.attack_flag = 0
        #health vals
        self.health = 1.0
        #grav flag 
        self.grav_flag = grav_flag
        
    def grav_force(self, dist):
        return self.mass/(dist**2)
    
    def grav_planet_force(self, p2, dist):
        return 0.2*(self.mass*p2.mass)/(dist**2)   
    
    def get_rad(self, angle):
        rad = 0
        for point in self.geom:
            max_rad = max([point[0][0],point[1][0]])
            print()
            if point[0][1] < angle <= point[1][1]:   
                if point[2] == 'arc':
                    rad = point[0][0]
                    print(1, rad)
                if point[2] == 'line':
                    diff_rad = point[1][0] - point[0][0]
                    diff_phi = point[1][1] - point[0][1]
                    min_rad = min([point[1][0], point[0][0]])
                    #get the intersect point
                    intersect_point = line_intersection([np.array([0.0,0.0]),pol2cart(1.2*max_rad,angle)], [np.array(pol2cart(point[0][0],point[0][1])),np.array(pol2cart(point[1][0],point[1][1]))])
                    rad = absval(intersect_point)
                    print(2, rad)
                print(3, rad)
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
        
class on_planet_ladder(on_planet_obj):
    def __init__(self, cart_pos, polar_theta, polar_radius, height, state, obj_type):
        super().__init__(cart_pos, height, state, obj_type)
        self.polar_theta = polar_theta
        self.polar_radius = polar_radius
        
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
        self.no_points = int(np.floor(arc/(0.05*np.pi)))
        arc_delta = arc/self.no_points
        self.points = [[float(rad),arc_start+i*arc_delta] for i in range(self.no_points)]
        self.orig_points = [[float(rad),arc_start+i*arc_delta] for i in range(self.no_points)]
        self.rel_points = None
        self.planet = None
        
    def water_step(self, planets_list):
        print('rel points0 ',self.rel_points) 
        print('points',self.points)
        point_force_list = []
        for point in self.orig_points:
            point_force = 0.0
            for planet in planets_list:
                #if planet. != self.planet:
                point_planet_dist = absval((self.planet.pos + pol2cart(point[0],point[1])) - planet.pos)
                #point_force += planet.grav_force(point_planet_dist)**6
                point_force += planet.grav_force(point_planet_dist)**4
                print('ppd',point_planet_dist, point_force)
            point_force_list.append(point_force)
        print(point_force_list/sum(point_force_list))
        print((point_force_list/np.mean(point_force_list)))
        #norm_point_force_list = (point_force_list/sum(point_force_list))
        norm_point_force_list = ((point_force_list/np.mean(point_force_list)) - 0.5)*2
        norm_point_force_list = [min(norm_point,3.5) for norm_point in norm_point_force_list]
        print('norme force points ',norm_point_force_list)
        for norm_point_ind, norm_point_force in enumerate(norm_point_force_list):
            self.points[norm_point_ind] = [0.97*self.rad + 0.03*self.rad*norm_point_force,self.points[norm_point_ind][1]]
            #self.points[norm_point_ind] = [0.95*self.rad + 0.05*self.rad*norm_point_force,self.points[norm_point_ind][1]]

        print('points 1',self.points)
        print('rel points ',self.rel_points)
        #print(t)
        
        self.rel_points = []
        for water_point in self.points:
            self.rel_points.append(np.array([water_point[0],water_point[1]]))    
        print('rel points1 ',self.rel_points)        
