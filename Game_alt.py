import json
import numpy as np
import pandas as pd
import pygame as pg
import random as rn 
from core_fns import absval, cart2pol, pol2cart, vec_comp, orth_vec, line_intersection, intersection
from planet_objs import obj_planet, on_planet_obj
from moveable_objs import obj_moveable, NPC, player

class game:   
    def __init__(self, player_object, sector_data_path, stars_data_path, screen):
        #screen 
        self.screen = screen
        #sectors
        self.sectors = []
        self.current_sector = [0,0]
        self.sector_scale = 100000
        self.closest_sector = None
        
        #stars data 
        self.all_stars_data = {}
        #load stars data 
        with open(stars_data_path) as json_file:
            all_stars_data = json.loads(json_file.read()) 
        all_stars_list = []
        for star_list in all_stars_data['stars']:
            new_star_list = []
            for star in star_list:
                new_star = np.array(star)
                new_star_list.append(new_star)
            all_stars_list.append(new_star_list)
        self.stars_list = all_stars_list
        
        #sector path 
        self.sector_data_path = sector_data_path
        self.sector_load_list = []
        #sector objects 
        self.sector_objects = {}
        self.sector_planets = {}       
        #load sector data 
        with open(self.sector_data_path) as json_file:
            all_sectors_data = json.loads(json_file.read())  
        #format sector data 
        self.all_sectors_data = {}
        for sector_data in all_sectors_data:
            print(sector_data['coords'][0])
            if sector_data['coords'][0] not in self.all_sectors_data.keys():
                self.all_sectors_data[sector_data['coords'][0]] = {}
            self.all_sectors_data[sector_data['coords'][0]][sector_data['coords'][1]] = sector_data['data']
                   
        #load lists 
        self.planet_list = []
        self.object_list = [player_object]
        #self.stars_list = []
        self.player = player_object
        try:
            self.window_pos = self.player.pos
        except:
            self.window_pos = np.zeros(2)            
        self.window_x_size = 800
        self.window_y_size = 600
        self.window_scale_val = 1
        
        #starting sector 
        self.load_sector(self.current_sector)
         
    def load_step(self):
        #get current sector 
        sector_pos = self.player.pos/self.sector_scale + np.array([0.5, 0.5])
        print('tt==',[self.player.pos[0]/1000,self.player.pos[1]/1000], self.player.pos, self.sector_scale)
        self.current_sector = np.floor(sector_pos)
        self.sector_pos_rem = (sector_pos - self.current_sector) % 1
        print('tt-====================',self.player.pos, sector_pos, self.sector_pos_rem, self.current_sector)
        #if distances significat load next sector 
        if self.sector_pos_rem[0] > 0.9:
            if self.sector_pos_rem[1] > 0.9:
                self.load_sector(self.current_sector + [1,1])
            elif self.sector_pos_rem[1] < 0.1:
                self.load_sector(self.current_sector + [1,-1]) 
            else:
                self.load_sector(self.current_sector + [1,0]) 
        elif self.sector_pos_rem[1] > 0.9:
            self.load_sector(self.current_sector + [0,1])   
        elif self.sector_pos_rem[0] < 0.1:
            if self.sector_pos_rem[1] > 0.9:
                self.load_sector(self.current_sector + [-1,1])
            elif self.sector_pos_rem[1] < 0.1:
                self.load_sector(self.current_sector + [-1,-1]) 
            else:
                self.load_sector(self.current_sector + [-1,0]) 
        elif self.sector_pos_rem[1] < 0.1:
            self.load_sector(self.current_sector + [0,-1])             

    def load_sector(self, coords): 
        if list(coords) not in self.sector_load_list:
            try:
                print('test2 ')
                new_data = self.all_sectors_data[coords[0]][coords[1]]
                print('new data test2 ',new_data)
                #add planets
                new_planet_list = []
                for planet in new_data['planet_list']:
                    #get geom 
                    geom = []
                    for g_point in planet['geom']:
                        geom.append([g_point['p1'],g_point['p2'],g_point['type'],g_point['mu']])
                    #planet objects
                    planet_obj_list = []
                    for planet_obj in planet['planet_obj_list']:
                        #create object 
                        planet_obj_list.append(on_planet_obj(planet_obj['cart_pos'], planet_obj['height'], planet_obj['state'], planet_obj['obj_type']))
                    new_planet_list.append(obj_planet(np.array(planet['pos']), np.array(planet['vel']), planet['mass'], geom, planet_obj_list, planet['planet_linked_list'], planet['grav_flag']))

                print('new planet list ',new_planet_list)
                for planet in new_planet_list:
                    planet.planet_linked_list = [new_planet_list[i] for i in planet.planet_linked_list]
                self.planet_list += new_planet_list
                #self.sector_planets[coords] = new_planet_list
                #add objects 
                new_obj_list = []
                for obj in new_data['object_list']:
                    new_obj_list.append(obj_moveable(obj['pos'], obj['vel'], obj['mass'], obj['geom']))
                self.object_list += new_obj_list
                #add to load list 
                self.sector_load_list.append(list(coords))
                #remove data from json 
                self.all_sectors_data[coords[0]][coords[1]] = {"object_list":[], "planet_list":[],"starfield":[]}
                #add stars
                #for stars_ind, stars in enumerate(new_data['starfield']):
                #    self.stars_list[stars_ind].append(stars)
            except:
                pass

    def unload_step(self):
        unload_list = []
        #get sectors to unload 
        for sector_coord in self.sector_load_list:
            if sector_coord != self.current_sector:
                sector_diff = sector_coord - (self.current_sector + np.array([0.5,0.5]))
                #determine the unload sector 
                if sector_diff[0] > 0.9 or sector_diff[0] < 0.1 or sector_diff[1] > 0.9 or sector_diff[1] < 0.1:
                    #self.unload_sector(sector_coord)
                    self.sector_load_list.drop(sector_coord)
                    unload_list.append(sector_coord)
        #get sector for each object 
        if unload_list != []:
            for obj in self.object_list:
                self.get_sector(obj)
            for planet in self.planet_list:        
                self.get_sector(planet)
            for coord in unload_list:
                self.unload_sector(coord)
            
    def get_sector(self, obj):
        sector_pos = obj.pos/self.sector_scale + np.array([0.5, 0.5])
        obj.current_sector = np.floor(sector_pos)        
    
    def unload_sector(self, coord):
        #get objects to remove 
        self.all_sectors_data[coord[0]][coord[1]]['object_list'] = []
        self.all_sectors_data[coord[0]][coord[1]]['planet_list'] = []        
        #coord_pos = (coord + np.array([0.5, 0.5]))*self.sector_scale
        #get objects 
        for obj in self.object_list:
            if obj.current_sector == coord:
                obj_entry = {'pos': obj.pos, 'vel': obj.vel, 'mass': obj.mass, 'geom': obj.geom}
                self.all_sectors_data[coord[0]][coord[1]]['object_list'].append(obj_entry)
                del obj
        #get planets 
        for planet in self.planet_list:
            if planet.current_sector == coord:
                geom = []
                for geom_point in planet.geom:
                    geom.append({'p1':geom_point[0], 'p2':geom_point[1],'type':geom_point[2],'mu':geom_point[3]})
                planet_obj_list = []
                for planet_obj in planet.planet_obj_list:
                    planet_obj_list.append({'cart_pos':planet_obj.cart_pos, 'height': planet_obj.height, 'state': planet_obj.state, 'obj_type': planet_obj.obj_type})
                    del planet_obj
                planet_objects_entry = {}
                planet_entry = {'pos': planet.pos, 'vel': planet.vel, 'mass': planet.mass, 'geom': geom, 'planet_obj_list': planet_obj_list}
                #drop the planet 
                del planet 
            
        
    def screen_step(self):
        #update draw positions
        for obj in self.object_list:
            obj.screen_pos = ((obj.pos - self.window_pos)*self.window_scale_val) + np.array([self.window_x_size/2,self.window_y_size/2])
            #print('positions ',obj.pos)
            if absval(obj.screen_pos) <= np.sqrt((self.window_x_size*2)**2 + (self.window_y_size*2)**2):
                #get object positionz
                obj.screen_pos = ((obj.pos - self.window_pos)*self.window_scale_val) + np.array([self.window_x_size/2,self.window_y_size/2])
                #draw the object
                pg.draw.circle(self.screen, (0, 255, 255), obj.screen_pos, 10*self.window_scale_val)
                pg.draw.line(self.screen,(220, 255, 5),obj.screen_pos,obj.screen_pos + obj.down*40)
                pg.draw.line(self.screen,(0, 0, 0),obj.screen_pos,obj.screen_pos + obj.m_speed*orth_vec(obj.down)*40)
                pg.draw.line(self.screen,(0, 0, 255),obj.screen_pos,obj.screen_pos + obj.m_force*40)

                pg.draw.line(self.screen,(255, 0, 0),obj.screen_pos,obj.screen_pos + obj.n_force*60)
                obj.screen_pos = ((obj.pos - self.window_pos)*self.window_scale_val) + np.array([self.window_x_size/2,self.window_y_size/2])
            
        for star_ind, stars in enumerate(self.stars_list):
            for star in stars:
                star_pos = ((star - self.window_pos)*self.window_scale_val*(0.10 + 0.15*star_ind)) + np.array([self.window_x_size/2,self.window_y_size/2])
                pg.draw.circle(self.screen, (0, 0, 0), star_pos, 3)
                
        for planet in self.planet_list:
            planet.screen_pos = ((planet.pos - self.window_pos)*self.window_scale_val) + np.array([self.window_x_size/2,self.window_y_size/2])
            pg.draw.line(self.screen,(255, 0, 0),planet.screen_pos,planet.screen_pos + planet.force*60)
            pg.draw.circle(self.screen,(255, 0, 0),planet.screen_pos,5)
            #draw the planet objects as circles
            for planet_obj in planet.planet_obj_list:
                print(planet_obj.state)
                if planet_obj.obj_type == 'ladder':
                    pg.draw.line(self.screen, (233, 255, 0), planet.screen_pos + pol2cart(planet_obj.rel_pos[0],planet_obj.rel_pos[1])*self.window_scale_val,planet.screen_pos + pol2cart(planet_obj.height + planet_obj.rel_pos[0],planet_obj.rel_pos[1])*self.window_scale_val,2)
                elif planet_obj.obj_type == 'room':
                    pg.draw.circle(self.screen, (50 + 100*self.player.inside_flag,0, 0), (planet.screen_pos + pol2cart(planet_obj.rel_pos[0],planet_obj.rel_pos[1])*self.window_scale_val), 30)
                    if self.player.inside_flag == 1:
                        if planet_obj == self.player.inside_room:
                            pg.draw.circle(self.screen, (50 + 100*self.player.inside_flag,0, 0), (planet.screen_pos + pol2cart(planet_obj.rel_pos[0],planet_obj.rel_pos[1])*self.window_scale_val), 60)
                            
                else:
                    pg.draw.circle(self.screen, (50 + 100*planet_obj.state,0, 0), (planet.screen_pos + pol2cart(planet_obj.rel_pos[0],planet_obj.rel_pos[1])*self.window_scale_val), 30)
    
            #draw the planet itself ----------------
            #print('positions planet',planet.screen_pos)
            if absval(planet.screen_pos) <= np.sqrt((self.window_x_size*2)**2 + (self.window_y_size*2)**2):
                #draw the object
                #pg.draw.circle(screen, (0, 255, 0), planet.screen_pos, planet.max_rad*self.window_scale_val)
                for point in planet.geom:
                    #print(test)
                    pg.draw.circle(self.screen, (233, 255, 0), planet.screen_pos + np.array([pol2cart(point[0][0],point[0][1])[0],-1*pol2cart(point[0][0],point[0][1])[1]]), 4)
                    if point[2] =='arc':
                        max_rad = max([point[0][0], point[1][0]])
                        #pg.draw.arc(screen, (233, 255, 0), [100,100,175,175], point[0][1], point[1][1],2)
                        #pg.draw.arc(screen, (233, 255, 0), [300,300,375,375], point[0][1], point[1][1],2)
                        
                        pg.draw.arc(self.screen, (233, 255, 0), list(planet.screen_pos - np.array([max_rad,max_rad])*self.window_scale_val)+[2*max_rad*self.window_scale_val,2*max_rad*self.window_scale_val], point[0][1]*self.window_scale_val, point[1][1]*self.window_scale_val,2)
                    if point[2] == 'line':
                        pg.draw.line(self.screen, (233, 255, 0), planet.screen_pos + np.array([pol2cart(point[0][0],point[0][1])[0],-1*pol2cart(point[0][0],point[0][1])[1]])*self.window_scale_val,planet.screen_pos + np.array([pol2cart(point[1][0],point[1][1])[0],pol2cart(point[1][0],-1*point[1][1])[1]])*self.window_scale_val,2)                 
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
                        pg.draw.circle(self.screen, (10, 255, 230), obj.intersect_point + planet.pos - self.window_pos, 4)
                            
                pg.draw.line(self.screen,(220, 255, 5),obj.screen_pos,obj.screen_pos + obj.down*20)
                pg.draw.line(self.screen,(0, 0, 0),obj.screen_pos,obj.screen_pos + obj.m_speed*orth_vec(obj.down)*20) 
                pg.draw.line(self.screen,(0, 0, 0),obj.screen_pos,obj.screen_pos + obj.force*240)  
                planet.screen_pos = ((obj.pos - self.window_pos)*self.window_scale_val) + np.array([self.window_x_size/2,self.window_y_size/2])
                pg.draw.line(self.screen,(255, 0, 0),obj.screen_pos,obj.screen_pos + obj.n_force*60)
                pg.draw.line(self.screen,(255, 0, 0),planet.screen_pos,planet.screen_pos + planet.force*60)
        for obj in self.object_list:
            pg.draw.line(self.screen,(255, 0, 255),obj.screen_pos,obj.screen_pos + obj.vel*600)
            pg.draw.line(self.screen,(255, 120, 255),obj.screen_pos,obj.screen_pos + obj.force*600)
            
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
            for i, planet in enumerate(self.planet_list):
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
                        print(11111111111111111111111,abs(obj_dist_pol[1]),geom_point)
                        if geom_point[0][1] < abs(obj_dist_pol[1]) <= geom_point[1][1]:
                            point_list.append(geom_point)
                        if geom_point[0][1] == geom_point[1][1]:
                            if abs(geom_point[0][1] - abs(obj_dist_pol[1])) < 0.05*np.pi:
                                vert_point_list.append(geom_point)
                    print(i, point_list,222222222222222222222222)
                    print(obj.pos, obj_dist_pol,2222)

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
                            self.intersect_point = intersect_point

                        #if radius of point smaller than the surface radius
                        if abs(rad) >= abs(obj_dist_pol[0]):                  
                            obj.contact_flag = 1
                            obj.contact_flag_obj = planet
                            
                            #if radius significantly smaller adjust 
                            if 0.96*abs(rad) > abs(obj_dist_pol[0]) and point not in vert_point_list:
                                #this if statement may need removing and fn retaining
                                #if point[2] == 'line' or rad == min([other_point[0] for other_point in point_list if other_point[2] != 'line']):
                                obj.pos -= obj_dist_vec*((rad - obj_dist_pol[0])/rad)

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
                                
                                print('planet pos ',planet.pos)
                                print('obj dist vec ',obj_dist_vec)
                                print('obj force ',obj.force, obj.g_force, planet.force, obj.vel, obj.m_force)
                                print('normal ',-1*vec_comp(obj.force, obj_dist_vec/absval(obj_dist_vec))*(obj_dist_vec/absval(obj_dist_vec)))
                                
                                if np.sign(obj.force[0]) == np.sign(obj_dist_vec[0]) or np.sign(obj.force[1]) == np.sign(obj_dist_vec[1]):
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
                                
                                #add speed force 
                                obj.m_force += 0.8*obj.m_speed*(np.array([-1*new_point_line[0],new_point_line[1]])/absval(orth_vec))

                                #add the m force to the total force 
                                obj.force += obj.m_force
                                
                                y_point = max([pol2cart(point[0][0],point[0][1])[1],pol2cart(point[1][0],point[1][1])[1]])
                                x_point = pol2cart(point[0][0],point[0][1])[0] 
                                x_diff =  pol2cart(point[1][0],point[1][1])[0] - pol2cart(point[0][0],point[0][1])[0]
                                # pg.draw.line(self.screen, (0, 150, 100), 
                                #              obj.screen_pos + np.array([pol2cart(point[0][0],point[0][1])[0],-1*pol2cart(point[0][0],point[0][1])[1]]),
                                #              obj.screen_pos + np.array([pol2cart(point[1][0],point[1][1])[0],pol2cart(point[1][0],-1*point[1][1])[1]])*self.window_scale_val,
                                #              2)
                                
                                # pg.draw.line(self.screen,(0, 255, 0),obj.screen_pos,obj.screen_pos + orth_vec*1000)
                                # pg.draw.line(self.screen,(0, 150, 100),obj.screen_pos,obj.screen_pos + new_point_line*1000)
                                # print('planet pos 1',planet.pos)
                                print(point)
                                print(point_list)
                                print('obj dist vec 1',obj_dist_vec)
                                print('obj force 1',obj.force, obj.g_force, planet.force, obj.vel, obj.m_force)
                                print('orth vec ',orth_vec)
                                print('normal 1',-1*vec_comp(obj.force, orth_vec)*(orth_vec/absval(orth_vec)))
                                print('contact flag ',obj.contact_flag_obj, self.planet_list.index(obj.contact_flag_obj))
                                self.screen_step()
                                pg.display.flip()
                                                                      
                                if np.sign(obj.force[0]) == np.sign(obj_dist_vec[0]) or np.sign(obj.force[1]) == np.sign(obj_dist_vec[1]):
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
                                    if 0.94*max(vert_point[0][0],vert_point[1][0]) > abs(obj_dist_pol[0]):
                                        #get next step position 
                                        next_pos = planet.pos - (obj.pos + obj.m_force)
                                        next_pos = planet.pos - (obj.pos + obj.force)
                                        
                                        print('t',obj_dist_vec, cart2pol(-1*obj_dist_vec[0],obj_dist_vec[1]), obj_dist_pol)
                                        next_pos_pol = cart2pol(-1*next_pos[0], next_pos[1])
                                        print('next pos ',obj_dist_pol,next_pos_pol)
                                        #print(t)
                                        #if will cross radius
                                        if (next_pos_pol[1] >= vert_point[0][1] >= obj_dist_pol[1]) or (obj_dist_pol[1] >= vert_point[0][1] >= next_pos_pol[1]):
                                            #get the cart points 
                                            new_point_line = np.array(pol2cart(vert_point[1][0], vert_point[1][1])) - np.array(pol2cart(vert_point[0][0], vert_point[0][1]))
                                            if obj_dist_pol[1] > 1.0*np.pi:
                                                orth_vec = np.array([-1*new_point_line[1],-1*new_point_line[0]])
                                            else:    
                                                orth_vec = np.array([-1*new_point_line[1],-1*new_point_line[0]])
                                            normal_force += -1*vec_comp(obj.force, orth_vec)*(orth_vec/absval(orth_vec))
                                            print('tt',-1*vec_comp(obj.force, orth_vec)*(orth_vec/absval(orth_vec)))
                                            #print(t)
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
                obj.vel += obj.g_force
                obj.force+=obj.vel
                if obj.move_keys[2]==1:
                    print('222222222',obj.vel, obj.g_force, obj.down, 1,obj.vel/obj.down,1, obj.m_force)
                    #print(t)
            else:
                print(1)
                #obj.vel = np.zeros(2)
        # #update object speed -------
      
        #update object position 
        for obj in self.object_list:
            #get the move force
            obj.move_force()
            obj.action_fn()
            #update the position 
            obj.pos += obj.force 
        
        #update the planet list
        for planet in self.planet_list:
            p_rad = planet.max_rad
            for planet_2 in self.planet_list:
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
                            planet.force += -1*(planet.mass/(planet.mass + planet_2.mass))*vec_comp(planet_rel_speed, planet_dist_vec)*(planet_dist_vec/absval(planet_dist_vec))
                        #if attacking then add damage and reduce elatsicity 
                        else:
                            planet.force += -1*(0.2)*(planet.mass/(planet.mass + planet_2.mass))*vec_comp(planet_rel_speed, planet_dist_vec)*(planet_dist_vec/absval(planet_dist_vec))
                            #need to imporve below to account for speed
                            planet_2.health -= (planet.mass/(planet.mass + planet_2.mass))                        
                    
                    #get gravity if relevent 
                    if planet.grav_flag == 1 and (p_rad + p2_rad) < abs_planet_dist:
                        planet.force += planet.grav_planet_force(planet_2,abs_planet_dist)*(-1*planet_dist_vec/abs_planet_dist)

        #update the object 
        for planet in self.planet_list:
            #update planet_pos
            planet.pos += planet.force
            #get the states of the object ---------------
            for planet_obj in planet.planet_obj_list:
                #fire cannon 
                if planet_obj.obj_type == 'cannon' and planet_obj.state == 2:
                    fire_obj = obj_moveable(pol2cart(planet_obj.rel_pos[0],planet_obj.rel_pos[1]) + planet.pos, 20*planet_obj.dir, 0.1, [np.array([0.0,0.1])])
                    self.object_list.append(fire_obj)
                    planet_obj.state = 0
