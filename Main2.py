import numpy as np
import pandas as pd
import pygame as pg
import random as rn 

#basic functions
def absval(x):
    if (x[0]**2+x[1]**2)>0.0:
        absvec=np.sqrt(x[0]**2+x[1]**2)
    else:
        absvec=0.0
    return absvec

def cart2pol(x, y):
    rho = np.sqrt(x**2 + y**2)
    if y < 0:
        phi = 2*np.pi + np.arctan2(y, x)
    else:
        phi = np.arctan2(y, x)
    return(rho, phi)

def pol2cart(rho, phi):
    x = rho * np.cos(phi)
    y = rho * np.sin(phi)
    return(x, y)

def vec_comp(v1, v2):
    return np.dot(v1, v2)/absval(v2)

def orth_vec(v):
    return np.array([v[1],-1*v[0]])

#get line intersection 
def line_intersection(line1, line2):
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
       return None

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return x, y

def intersection(l1p1,l1p2,l2p1,l2p2):
    denom = (l1p1[0] - l1p2[0])*(l2p1[1] - l2p2[1]) - (l1p1[1] - l1p2[1])*(l2p1[0] - l2p2[0])
    px = ((l1p1[0]*l1p2[1] - l1p2[0]*l1p1[1])*(l2p1[0] - l2p2[0]) -  (l2p1[0]*l2p2[1] - l2p2[0]*l2p1[1])*(l1p1[0] - l1p2[0]))/denom
    py = ((l1p1[0]*l1p2[1] - l1p2[0]*l1p1[1])*(l2p1[1] - l2p2[1]) -  (l2p1[0]*l2p2[1] - l2p2[0]*l2p1[1])*(l1p1[1] - l1p2[1]))/denom
    return np.array([px,py])

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
        #move_keys
        self.move_keys = [0,0,0]
        #action keys: action, dive, 
        self.action_keys = [0,0,0,0]
        #------------------intersect_point 
        self.intersect_point = np.zeros(2)

    def move_force(self):
        if self.move_keys[0] == 1:
            if self.m_speed > -self.max_speed:
                self.m_speed += -self.speed_step
                self.move_flag = 1
        if self.move_keys[1] == 1:
            if self.m_speed < self.max_speed:
                self.m_speed += self.speed_step
                self.move_flag = 1                           
        if self.move_keys[2] == 1:
            #self.force += -25*self.down 
            print(121212,self.vel)
            self.vel = -10*self.down + 1.5*self.m_speed*(orth_vec(self.down))
            print('22222', self.vel, self.down)
            #print(t)
            
    def action_fn(self):
        if self.action_keys[1] == 1:
            self.contact_flag_obj.force += 0.1*self.down            

#player class 
class player(obj_moveable):
    def __init__(self, pos, vel, mass, geom):
        super().__init__(pos, vel, mass, geom)
        
#planet class
class obj_planet:
    def __init__(self, pos, vel, mass, geom):
        self.screen_pos = np.zeros(2)
        self.pos = pos
        self.vel = vel
        self.mass = mass
        self.geom = geom
        #geom form (p1 (ro, phi), p2, type, mu)
        #forces
        self.g_force = np.zeros(2)
        self.m_force = np.zeros(2)
        self.n_force = np.zeros(2)
        self.force = np.zeros(2)
        #grav radius
        for geom_point in geom:
            print('ttt',geom_point[0][0],geom_point[0],geom_point)
        self.g_max_rad = mass*20*max([geom_point[0][0] for geom_point in geom])
        #max radius
        self.max_rad = max([geom_point[0][0] for geom_point in geom])
        #attack flag
        self.attack_flag = 0
        #health vals
        self.health = 1.0
        
    def grav_force(self, dist):
        return self.mass/(dist**2)

class game:
    def __init__(self, planet_list, object_list, stars_list):
        self.planet_list = planet_list
        self.object_list = object_list
        self.stars_list = stars_list
        self.player = object_list[0]
        try:
            self.window_pos = self.player.pos
        except:
            self.window_pos = np.zeros(2)            
        self.window_x_size = 800
        self.window_y_size = 600
        self.window_scale_val = 1
    
    def screen_step(self):
        #update draw positions
        for obj in self.object_list:
            obj.screen_pos = ((obj.pos - self.window_pos)*self.window_scale_val) + np.array([self.window_x_size/2,self.window_y_size/2])
            #print('positions ',obj.pos)
            if absval(obj.screen_pos) <= np.sqrt((self.window_x_size*2)**2 + (self.window_y_size*2)**2):
                #get object positionz
                obj.screen_pos = ((obj.pos - self.window_pos)*self.window_scale_val) + np.array([self.window_x_size/2,self.window_y_size/2])
                #draw the object
                pg.draw.circle(screen, (0, 255, 255), obj.screen_pos, 10)
                pg.draw.line(screen,(220, 255, 5),obj.screen_pos,obj.screen_pos + obj.down*40)
                pg.draw.line(screen,(0, 0, 0),obj.screen_pos,obj.screen_pos + obj.m_speed*orth_vec(obj.down)*40)
                #print('piss ',obj.n_force)
                pg.draw.line(screen,(255, 0, 0),obj.screen_pos,obj.screen_pos + obj.n_force*60)
                obj.screen_pos = ((obj.pos - self.window_pos)*self.window_scale_val) + np.array([self.window_x_size/2,self.window_y_size/2])
            
        for star_ind, stars in enumerate(self.stars_list):
            for star in stars:
                star_pos = ((star - self.window_pos)*self.window_scale_val*(0.10 + 0.15*star_ind)) + np.array([self.window_x_size/2,self.window_y_size/2])
                pg.draw.circle(screen, (0, 0, 0), star_pos, 3)
                
        for planet in self.planet_list:
            planet.screen_pos = ((planet.pos - self.window_pos)*self.window_scale_val) + np.array([self.window_x_size/2,self.window_y_size/2])
            #print('positions planet',planet.screen_pos)
            if absval(planet.screen_pos) <= np.sqrt((self.window_x_size*2)**2 + (self.window_y_size*2)**2):
                #draw the object
                pg.draw.circle(screen, (0, 255, 0), planet.screen_pos, planet.max_rad)
                for point in planet.geom:
                    #print(test)
                    pg.draw.circle(screen, (233, 255, 0), planet.screen_pos + np.array([pol2cart(point[0][0],point[0][1])[0],-1*pol2cart(point[0][0],point[0][1])[1]]), 4)
                    if point[2] =='arc':
                        max_rad = max([point[0][0], point[1][0]])
                        #pg.draw.arc(screen, (233, 255, 0), [100,100,175,175], point[0][1], point[1][1],2)
                        #pg.draw.arc(screen, (233, 255, 0), [300,300,375,375], point[0][1], point[1][1],2)
                        
                        pg.draw.arc(screen, (233, 255, 0), list(planet.screen_pos - np.array([max_rad,max_rad]))+[2*max_rad,2*max_rad], point[0][1], point[1][1],2)
                    if point[2] == 'line':
                        pg.draw.line(screen, (233, 255, 0), planet.screen_pos + np.array([pol2cart(point[0][0],point[0][1])[0],-1*pol2cart(point[0][0],point[0][1])[1]]),planet.screen_pos + np.array([pol2cart(point[1][0],point[1][1])[0],pol2cart(point[1][0],-1*point[1][1])[1]]),2)                 
                        #print test line 
                        diff_rad = point[1][0] - point[0][0]
                        diff_phi = point[1][1] - point[0][1]
                        min_rad = min([point[1][0], point[0][0]])
                        phi_test = diff_phi/20
                        y_point = max([pol2cart(point[0][0],point[0][1])[1],pol2cart(point[1][0],point[1][1])[1]])
                        x_point = pol2cart(point[0][0],point[0][1])[0] 
                        x_diff =  pol2cart(point[1][0],point[1][1])[0] - pol2cart(point[0][0],point[0][1])[0]
                        x_diff_test = x_diff/20
                        for i in range(0,20):
                            int_point = line_intersection([planet.pos,planet.pos + np.array([x_point + x_diff_test*i,y_point])], [planet.pos + np.array(pol2cart(point[0][0],point[0][1])),planet.pos + np.array(pol2cart(point[1][0],point[1][1]))])
                        pg.draw.circle(screen, (10, 255, 230), obj.intersect_point + planet.pos - self.window_pos, 4)
                            
                pg.draw.line(screen,(220, 255, 5),obj.screen_pos,obj.screen_pos + obj.down*20)
                pg.draw.line(screen,(0, 0, 0),obj.screen_pos,obj.screen_pos + obj.m_speed*orth_vec(obj.down)*20) 
                pg.draw.line(screen,(0, 0, 0),obj.screen_pos,obj.screen_pos + obj.force*240)  
                planet.screen_pos = ((obj.pos - self.window_pos)*self.window_scale_val) + np.array([self.window_x_size/2,self.window_y_size/2])
                pg.draw.line(screen,(255, 0, 0),obj.screen_pos,obj.screen_pos + obj.n_force*60)
                pg.draw.line(screen,(255, 0, 0),planet.screen_pos,planet.screen_pos + planet.force*60)
        for obj in self.object_list:
            pg.draw.line(screen,(255, 0, 255),obj.screen_pos,obj.screen_pos + obj.vel*600)
                
    def orth_vec(self,v):
        return np.array([v[1],-1*v[0]])            

    def step(self):
        for obj in self.object_list:
            #reset forces 
            obj.m_force = np.zeros(2)
            obj.g_force = np.zeros(2)
            obj.n_force = np.zeros(2) 
            #reset contact flag 
            obj.contact_flag = 0 
            
            for planet in self.planet_list:
                #get the gravitional effect on each object
                obj_dist_vec = planet.pos - obj.pos
                obj_dist = absval(obj_dist_vec)
                print('obj dist ', obj_dist_vec)
                if obj_dist <= planet.g_max_rad:
                    obj.g_force += obj_dist_vec*planet.grav_force(obj_dist)
            
            #update down of the object 
            obj.down = obj.g_force/absval(obj.g_force)
            
            #update the jump force
            if absval(obj.vel) != 0:
                obj.vel = obj.vel 
            
            #update the total force
            obj.force = obj.g_force
            
            #check if in contact 
            for planet in self.planet_list:
                #####------------------ deal with the interaction with the objects
                #get the gravitional effect on each object
                obj_dist_vec = planet.pos - obj.pos
                obj_dist = absval(obj_dist_vec)                
                #check if contacting planet 

                if obj_dist < 1.2*(planet.max_rad):
                    #get the angle of the vector relative to the 
                    obj_dist_pol = cart2pol(-1*obj_dist_vec[0], obj_dist_vec[1])
                    #get the points that the object is between for the planet
                    point_list = []
                    #also get vertical points close to the player
                    vert_point_list = []
                    normal_force = np.zeros(2)
                    for geom_point in planet.geom:
                        if geom_point[0][1] < abs(obj_dist_pol[1]) <= geom_point[1][1]:
                            point_list.append(geom_point)
                        if geom_point[0][1] == geom_point[1][1]:
                            if abs(geom_point[0][1] - abs(obj_dist_pol[1])) < 0.05*np.pi:
                                vert_point_list.append(geom_point)
                    # print(obj_dist_vec)
                    # print('ttttttetetet11',obj_dist_pol)
                    # print(geom_point[0][1],obj_dist_pol[1],geom_point[1][1])
                    # print(point_list)
                    
                    #print(test)
                    #get the corresponding radius at point 
                    for point in point_list:
                        if point[2] == 'arc':
                            rad = point[0][0]
                        if point[2] == 'line':
                            diff_rad = point[1][0] - point[0][0]
                            diff_phi = point[1][1] - point[0][1]
                            min_rad = min([point[1][0], point[0][0]])
                            #rad = diff_rad * np.cos(diff_phi - obj_dist_pol[1]) + point[0][0]
                            #get the intersect point
                            intersect_point = line_intersection([np.array([0.0,0.0]),pol2cart(obj_dist_pol[0],obj_dist_pol[1])], [np.array(pol2cart(point[0][0],point[0][1])),np.array(pol2cart(point[1][0],point[1][1]))])
                            rad = absval(intersect_point)
                            #print(obj.pos, planet.pos + np.array(pol2cart(point[0][0],point[0][1])),planet.pos,planet.pos + np.array(pol2cart(point[1][0],point[1][1])))
                            self.intersect_point = intersect_point

                        #if radius of point smaller than the surface radius
                        if abs(rad) >= abs(obj_dist_pol[0]):                  
                            obj.contact_flag = 1
                            obj.contact_flag_obj = planet

                            #add movement speed and movement force here
                            obj.m_speed = (1-point[3])*obj.m_speed    
                            if abs(obj.m_speed) < 0.01:
                                obj.m_speed = 0.0
                            obj.m_force += obj.m_speed*(self.orth_vec(obj.down)) 

                            # #add the m force to the total force 
                            # print('obj force ',obj.force,obj.m_force)
                            # obj.force += obj.m_force
                            
                            #get the normal force of total force 
                            if point[2] == 'arc':
                                #add the m force to the total force 
                                obj.force += obj.m_force
                                obj.force += planet.force
                                #obj_dist_vec += planet.force
                                normal_force += -1*vec_comp(obj.force, obj_dist_vec/absval(obj_dist_vec))*(obj_dist_vec/absval(obj_dist_vec))
                                #add planet speed component
                                normal_force += vec_comp(planet.force, obj_dist_vec/absval(obj_dist_vec))*(obj_dist_vec/absval(obj_dist_vec))
                                
                                #get the velocity normal component 
                                if obj.move_keys[2] != 1:
                                    vel_comp = vec_comp(obj.vel, obj.down/absval(obj.down))*(obj.down/absval(obj.down))
                                    obj.vel += -1*vel_comp
                                    obj.vel = (1-2*point[3])*obj.vel   
                                if absval(obj.vel) < 0.04:
                                    obj.vel = np.zeros(2)
                                    
                                #add normal force
                                obj.n_force = normal_force
                                #print(test)
                            if point[2] == 'line':
                                new_point_line = np.array(pol2cart(point[1][0], point[1][1])) - np.array(pol2cart(point[0][0], point[0][1]))
                                orth_vec = np.array([-1*new_point_line[1],-1*new_point_line[0]])

                                #add the m force to the total force 
                                obj.force += obj.m_force
                                normal_force += -1*vec_comp(obj.force, orth_vec)*(orth_vec/absval(orth_vec))
                                #add planet speed component
                                normal_force += vec_comp(planet.force, orth_vec)*(orth_vec/absval(orth_vec))
                                #get the velocity normal component 
                                if obj.move_keys[2] != 1:
                                    obj.vel -= vec_comp(obj.vel, orth_vec)*(orth_vec/absval(orth_vec))
                                    #vel_comp = vec_comp(obj.vel, obj.down/absval(obj.down))*(obj.down/absval(obj.down))
                                    #obj.vel += -1*vel_comp
                                    obj.vel = (1-2*point[3])*obj.vel   
                                if absval(obj.vel) < 0.04:
                                    obj.vel = np.zeros(2)
                            
                                #add normal force 
                                obj.n_force = normal_force
                                print('LINE')
                            if vert_point_list != []:
                                for vert_point in vert_point_list:
                                    #if rad smaller than the point rad
                                    if 0.99*max(vert_point[0][0],vert_point[1][0]) > abs(obj_dist_pol[0]):
                                        #get next step position 
                                        next_pos = planet.pos - (obj.pos + obj.m_force)
                                        #next_pos = obj_dist_vec + obj.m_force
                                        #print('t',obj_dist_vec, cart2pol(-1*obj_dist_vec[0],obj_dist_vec[1]), obj_dist_pol)
                                        next_pos_pol = cart2pol(-1*next_pos[0], next_pos[1])
                                        #if will cross radius
                                        if (next_pos_pol[1] >= vert_point[0][1] >= obj_dist_pol[1]) or (obj_dist_pol[1] >= vert_point[0][1] >= next_pos_pol[1]):
                                            #get the cart points 
                                            new_point_line = np.array(pol2cart(vert_point[1][0], vert_point[1][1])) - np.array(pol2cart(vert_point[0][0], vert_point[0][1]))
                                            if obj_dist_pol[1] > 1.0*np.pi:
                                                orth_vec = np.array([-1*new_point_line[1],-1*new_point_line[0]])
                                            else:    
                                                orth_vec = np.array([-1*new_point_line[1],-1*new_point_line[0]])
                                            normal_force += -1*vec_comp(obj.force, orth_vec)*(orth_vec/absval(orth_vec))

                            #print('teststssss4-------------------', normal_force,obj.force,obj.m_speed)
                            obj.force += obj.vel
                            obj.force += normal_force
                            #print(test22)
                        elif obj.contact_flag == 0:
                            print(1)
                            #obj.force += obj.m_speed*(self.orth_vec(obj.down)) 

                elif obj.contact_flag == 0:
                    #add the m force to the total force 
                    print('force 11111---', obj.m_force, obj.m_speed*(self.orth_vec(obj.down)))
                    #obj.force += obj.m_speed*(self.orth_vec(obj.down))                
            
            if obj.contact_flag == 0 or obj.move_keys[2]==1:
                print('11111',obj.vel)
                print(obj.vel, obj.g_force, obj.down, 1,obj.vel/obj.down,1, obj.m_force)
                obj.vel += obj.g_force
                obj.force+=obj.vel
                if obj.move_keys[2]==1:
                    print(obj.vel, obj.g_force, obj.down, 1,obj.vel/obj.down,1, obj.m_force)
                    #print(t)               
                # if absval(obj.vel) != 0:
                #     print('11111',obj.vel)
                #     print(obj.vel, obj.g_force, obj.down, 1,obj.vel/obj.down,1, obj.m_force)
                #     obj.vel += obj.g_force
                #     obj.force+=obj.vel
                #     if obj.move_keys[2]==1:
                #         print(obj.vel, obj.g_force, obj.down, 1,obj.vel/obj.down,1, obj.m_force)
                #         #print(t)
            else:
                print(1)
                #obj.vel = np.zeros(2)
        # #update object speed -------
      
        #update object position 
        for obj in self.object_list:
            #get the move force
            obj.move_force()
            obj.action_fn()
            print('force ',obj.force, obj.g_force)
            obj.pos += obj.force 
        
        #update the planet list
        for planet in planet_list:
            p_rad = planet.max_rad
            for planet_2 in planet_list:
                if planet != planet_2:
                    p2_rad = planet_2.max_rad
                    #get distance 
                    planet_dist_vec = planet.pos - planet_2.pos
                    abs_planet_dist = absval(planet_dist_vec)
                    #get the relative speed
                    planet_rel_speed = planet.force - planet_2.force
                    #if hit 
                    if (p_rad + p2_rad) >= abs_planet_dist:
                        #if not attacking then bounce off
                        if planet.attack_flag == 0:
                            print(1111111111111111111111111111)
                            planet.force += -1*(planet.mass/(planet.mass + planet_2.mass))*vec_comp(planet_rel_speed, planet_dist_vec)*(planet_dist_vec/absval(planet_dist_vec))
                        #if attacking then add damage and reduce elatsicity 
                        else:
                            planet.force += -1*(0.2)*(planet.mass/(planet.mass + planet_2.mass))*vec_comp(planet_rel_speed, planet_dist_vec)*(planet_dist_vec/absval(planet_dist_vec))
                            #need to imporve below to account for speed
                            planet_2.health -= (planet.mass/(planet.mass + planet_2.mass))                        
                            
        #update the object 
        for planet in planet_list:
            planet.pos += planet.force

#planet class

#draw the screen
pg.init()
screen = pg.display.set_mode((800,600))
#run game
obj2 = obj_moveable(np.array([0.0,40.0]), np.array([0.0,0.0]), 2.0, [np.array([0.0,0.1])])
obj3 = obj_moveable(np.array([20.0,30.0]), np.array([0.0,0.0]), 2.0, [np.array([0.0,0.1])])

obj1 = player(np.array([0.0,0.0]), np.array([0.0,0.0]), 2.0, [np.array([0.0,0.1])])

geom = [[[75.0,0.0],[75.0,2*np.pi],'arc', 0.04]]
#geom = [[[75.0,0.0],[101.0,0.4*np.pi],'line', 0.1],[[101.0,0.4*np.pi],[75.0,0.99*np.pi],'line', 0.1],[[75.0,0.99*np.pi],[75.0,1.2*np.pi],'arc', 0.1],[[102.0,1.2*np.pi],[84.0,1.4*np.pi],'line', 0.1],[[84.0,1.4*np.pi],[75.0,2*np.pi],'arc', 0.1]]
#geom = [[[75.0,0.0],[105.0,0.5*np.pi],'line', 0.051], [[105.0,0.5*np.pi],[75.0,1.0*np.pi],'line', 0.051],[[75.0,1.0*np.pi],[105.0,1.5*np.pi],'line', 0.051],[[105.0,1.5*np.pi],[75.0,2.0*np.pi],'line', 0.051]]
#geom = [[[75.0,0.0],[75.0,0.3*np.pi],'arc', 0.01], [[105.0,0.3*np.pi],[105.0,0.5*np.pi],'line', 0.01], [[105.0,0.5*np.pi],[100.0,0.8*np.pi],'line', 0.1], [[100.0,0.8*np.pi],[120.0,0.8*np.pi],'line', 0.1], [[120.0,0.8*np.pi],[75.0,1.0*np.pi],'line', 0.1],[[75.0,1.0*np.pi],[105.0,1.5*np.pi],'line', 0.1],[[105.0,1.5*np.pi],[75.0,2.0*np.pi],'line', 0.1]]
##geom = [[[75.0,0.0],[75.0,0.5*np.pi],'arc', 0.1], [[75.0,0.5*np.pi],[105.0,0.5*np.pi],'line', 0.1],[[105.0,0.5*np.pi],[105.0,1.4*np.pi],'arc', 0.1],[[105.0,1.4*np.pi],[75.0,1.4*np.pi],'line', 0.1],[[75.0,1.4*np.pi],[75.0,2.0*np.pi],'arc', 0.1]]
#geom = [[[105.0,0.0],[105.0,0.15*np.pi],'arc', 0.1], [[105.0,0.15*np.pi],[75.0,0.15*np.pi],'line', 0.1],[[75.0,0.15*np.pi],[75.0,0.3*np.pi],'arc', 0.1],
        # [[75.0,0.30*np.pi],[105.0,0.30*np.pi],'line', 0.1], [[105.0,0.3*np.pi],[105.0,0.5*np.pi],'arc', 0.1], [[105.0,0.5*np.pi],[75.0,0.5*np.pi],'line', 0.1],[[75.0,0.5*np.pi],[75.0,0.7*np.pi],'arc', 0.1],
        # [[75.0,0.70*np.pi],[105.0,0.70*np.pi],'line', 0.1], [[105.0,0.7*np.pi],[105.0,0.9*np.pi],'arc', 0.1], [[105.0,0.9*np.pi],[75.0,0.9*np.pi],'line', 0.1],[[75.0,0.9*np.pi],[75.0,1.1*np.pi],'arc', 0.1],
        # [[75.0,1.1*np.pi],[105.0,1.1*np.pi],'line', 0.1], [[105.0,1.1*np.pi],[105.0,1.3*np.pi],'arc', 0.1], [[105.0,1.3*np.pi],[75.0,1.3*np.pi],'line', 0.1],[[75.0,1.3*np.pi],[75.0,1.5*np.pi],'arc', 0.1],
        # [[75.0,1.5*np.pi],[105.0,1.5*np.pi],'line', 0.1], [[105.0,1.5*np.pi],[105.0,1.7*np.pi],'arc', 0.1], [[105.0,1.7*np.pi],[75.0,1.7*np.pi],'line', 0.1],[[75.0,1.7*np.pi],[75.0,2.0*np.pi],'arc', 0.1]
        # ]
n_geom = [[[25.0,0.0],[25.0,2.0*np.pi],'arc', 0.08]]

a_geom = [[[35.0,0.0*np.pi],[32.0,0.1*np.pi],'line', 0.08],[[32.0,0.1*np.pi],[40.0,0.25*np.pi],'line', 0.08],
          [[40.0,0.25*np.pi],[40.0,0.45*np.pi],'line', 0.08],[[40.0,0.45*np.pi],[32.0,0.75*np.pi],'line', 0.08],
          [[32.0,0.75*np.pi],[30.0,0.90*np.pi],'line', 0.08],[[30.0,0.90*np.pi],[40.0,1.5*np.pi],'line', 0.08],
          [[40.0,1.5*np.pi],[41.0,1.75*np.pi],'line', 0.08],[[41.0,1.75*np.pi],[35.0,2.0*np.pi],'line', 0.08]]

#starfield 
from scipy import stats
starfield = []
for i in range (0,3):
    stars = []
    for i in range(0,200):
        #x = rn.randint(-500, 500)
        #y = rn.randint(40, 400)
        x = rn.uniform(-5000, 5000)
        y = rn.uniform(-5000, 5000)        
        #stars.append(np.random.rand(2)*5000)
        stars.append(np.array([x,y]))
    starfield.append(stars)

#p1 = obj_planet(np.array([-60.0, 100.0]), np.array([0.0,0.0]), 60.0, geom)
p2 = obj_planet(np.array([-200.0, -60.0]), np.array([0.0,0.0]), 10.0, n_geom)
p3 = obj_planet(np.array([-200.0, 200.0]), np.array([0.0,0.0]), 50.0, n_geom)

p1 = obj_planet(np.array([-60.0, 100.0]), np.array([0.0,0.0]), 150.0, geom)

obj4 = obj_moveable(np.array([-54.0,-120.0]), np.array([15.5,0.0]), 2.0, [np.array([0.0,0.1])])

star_field = []

planet_list = [p1,p2,p3]
obj_list = [obj1, obj2, obj4]
g1 = game(planet_list, obj_list, starfield)
g1.step()

# Run until the user asks to quit
running = True
while running:

    # Did the user click the window close button?
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False

    # Fill the background with white
    screen.fill((255, 255, 255))

    #player movement and actions
    keys = pg.key.get_pressed()
    if g1.player.contact_flag == 1:
        events = pg.event.get()
        if keys[pg.K_LEFT]: # We can check if a key is pressed like this
            g1.player.move_keys[0] = 1
        else:
            g1.player.move_keys[0] = 0
        if keys[pg.K_RIGHT]:
            g1.player.move_keys[1] = 1
        else:
            g1.player.move_keys[1] = 0
        if keys[pg.K_SPACE]:
            g1.player.move_keys[2] = 1
        else:
            g1.player.move_keys[2] = 0     
        #action for moving 
        if keys[pg.K_w]:
            g1.player.action_keys[1] = 1
        else:   
            g1.player.action_keys[1] = 0
    else:
        g1.player.move_keys = [0,0,0]
    
    print(g1.player.move_keys)
    #main game step 
    g1.step()
    g1.screen_step()
    # Flip the display
    pg.display.flip()

# Done! Time to quit.
pg.quit()