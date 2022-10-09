import json
import numpy as np
import pandas as pd
import pygame as pg
import random as rn 
from core_fns import absval, cart2pol, pol2cart, vec_comp, orth_vec, line_intersection, intersection, angle_between
from planet_objs import obj_planet, on_planet_obj, on_planet_water, on_planet_anchor, on_planet_display
from moveable_objs import obj_moveable, NPC, player
import copy 
import os 

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
            if sector_data['coords'][0] not in self.all_sectors_data.keys():
                self.all_sectors_data[sector_data['coords'][0]] = {}
            self.all_sectors_data[sector_data['coords'][0]][sector_data['coords'][1]] = sector_data['data']
                   
        #load lists 
        self.planet_list = []
        self.object_list = [player_object]
        #room sector data 
        self.sector_room_list = []
        #room details 
        self.room_obj = None
        #self.stars_list = []
        self.player = player_object
        try:
            self.window_pos = self.player.pos
        except:
            self.window_pos = np.zeros(2)            
        self.window_x_size = 800
        self.window_y_size = 600
        self.window_scale_val = 1.0
        self.prev_window_scale_val = 1.0
        self.room_scale_val = 2.8
        #starting sector 
        self.load_sector(self.current_sector)
         
    def load_step(self):
        #get current sector 
        sector_pos = self.player.pos/self.sector_scale + np.array([0.5, 0.5])
        self.current_sector = np.floor(sector_pos)
        self.sector_pos_rem = (sector_pos - self.current_sector) % 1
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

    def load_room(self, room, room_planet):
        #get geom 
        geom = []
        for g_point in room['geom']:
            geom.append([g_point['p1'],g_point['p2'],g_point['type'],g_point['mu']])
        #planet objects
        room_obj_list = []
        for room_obj in room['room_obj_list']:
            #create object 
            room_obj_list.append(on_planet_obj(room_obj['cart_pos'], room_obj['height'], room_obj['state'], room_obj['obj_type']))
        room_water_list = []
        #room_planet_obj = obj_planet(room_planet.pos, room_planet.vel, room_planet.mass, geom, room_obj_list, room_water_list, room['planet_linked_list'], 0, room['planet_id'])
        room_planet_obj = obj_planet(room_planet.pos, np.zeros(2), room_planet.mass, geom, room_obj_list, room_water_list, room['planet_linked_list'], 0, room['planet_id'])
        return room_planet_obj

    def load_sector(self, coords): 
        if list(coords) not in self.sector_load_list:
            #try:
            new_data = self.all_sectors_data[coords[0]][coords[1]]
            #add planets
            new_planet_list = []
            for planet_ind, planet in enumerate(new_data['planet_list']):
                #get geom 
                geom = []
                for g_point in planet['geom']:
                    geom.append([g_point['p1'],g_point['p2'],g_point['type'],g_point['mu']])
                #planet objects
                planet_obj_list = []
                planet_water_list = []
                for planet_obj in planet['planet_obj_list']:
                    #create object 
                    if planet_obj['obj_type'] == 'room':
                        room_obj = on_planet_obj(planet_obj['cart_pos'], planet_obj['height'], planet_obj['state'], planet_obj['obj_type'])
                        room_obj.room_index = planet_obj['room_index']
                        try:
                            planet_obj_img = pg.image.load(planet_obj['img'])
                            room_obj.img = planet_obj_img
                            room_obj.img_angle = np.degrees(planet_obj['cart_pos'][1] - 0.5*np.pi)
                        except:
                            pass
                        planet_obj_list.append(room_obj)
                    elif planet_obj['obj_type'] == 'water':
                        water_obj = on_planet_water(planet_obj['arc_start'], planet_obj['arc'], planet_obj['rad'], np.array(planet['pos']))
                        planet_water_list.append(water_obj)
                    elif planet_obj['obj_type'] == 'anchor':
                        anchor_obj = on_planet_anchor(planet_obj['cart_pos'], planet_obj['height'], planet_obj['state'], planet_obj['obj_type'], planet_obj['deploy_max_len'], planet['pos'])
                        planet_obj_list.append(anchor_obj) 
                    elif planet_obj['obj_type'] == 'display':
                        display_obj = on_planet_display(planet_obj['cart_pos'], planet_obj['height'], planet_obj['state'], planet_obj['obj_type'], planet_obj['target_obj'])
                        planet_obj_list.append(display_obj)
                        try:
                            planet_obj_img = pg.image.load(planet_obj['img'])
                            display_obj.img = planet_obj_img
                            display_obj.img_angle = np.degrees(planet_obj['cart_pos'][1] - 0.5*np.pi)
                        except:
                            pass
                    else:
                        planet_obj_list.append(on_planet_obj(planet_obj['cart_pos'], planet_obj['height'], planet_obj['state'], planet_obj['obj_type']))
                new_planet_list.append(obj_planet(np.array(planet['pos']), np.array(planet['vel']), planet['mass'], geom, planet_obj_list, planet_water_list, planet['planet_linked_list'], planet['grav_flag'], planet['planet_id']))
                try:
                    planet_img = pg.image.load(planet['img'])
                    planet_img.set_colorkey((255, 255, 255))
                    new_planet_list[planet_ind].planet_img = planet_img
                    new_planet_list[planet_ind].planet_display_img = planet_img
                    new_planet_list[planet_ind].img_scale = planet['img_scale']
                except:
                    #print('1')
                    continue
            #linked planets 
            #print('new planet list ',new_planet_list)

            for planet in new_planet_list:
                planet.planet_linked_list = [new_planet_list[i] for i in planet.planet_linked_list]
            self.planet_list += new_planet_list

            #update display objects 
            for planet in self.planet_list:
                #add display focus
                for planet_obj in planet.planet_obj_list:
                    if planet_obj.obj_type == "display":
                        planet_obj.get_counter_target(self.planet_list)

            #load single sector room lists
            self.sector_room_list = new_data['rooms']
            
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
            #except:
            #    pass

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
            
    def draw_planet(self, planet):
        #draw the atmosphere 
        #pg.draw.circle(self.screen,(200, 200, 250,10),planet.screen_pos*self.window_scale_val,500)
        planet.screen_pos = ((planet.pos - self.window_pos)*self.window_scale_val) + np.array([self.window_x_size/2,self.window_y_size/2])
        
        #draw planet atmos
        planet.atmos_surface.fill((255, 255, 255,0))
        pg.draw.circle(planet.atmos_surface,(0,181,226,50),planet.screen_pos,(1.4*planet.min_rad + 1.2*planet.rad_diff)*self.window_scale_val)        
        pg.draw.circle(planet.atmos_surface,(0,186,236,100),planet.screen_pos,(1.2*planet.min_rad + 0.8*planet.rad_diff)*self.window_scale_val)  
        pg.draw.circle(planet.atmos_surface,(0,191,246,150),planet.screen_pos,(1.1*planet.min_rad + 0.6*planet.rad_diff)*self.window_scale_val)  
        pg.draw.circle(planet.atmos_surface,(0,191,246,200),planet.screen_pos,(1.05*planet.min_rad + 0.5*planet.rad_diff)*self.window_scale_val)  
        pg.draw.circle(planet.atmos_surface,(0,199,255,230),planet.screen_pos,(1.03*planet.min_rad + 0.42*planet.rad_diff)*self.window_scale_val)  
        self.screen.blit(planet.atmos_surface,np.array([0.0,0.0]))# planet.screen_pos)
 
        #draw water step
        for water_obj in planet.water_obj_list:
            water_obj_points_set = [planet.screen_pos]
            for water_point_ind, water_point in enumerate(water_obj.rel_points):
                water_obj_points_set.append(planet.screen_pos + np.array(pol2cart(water_point[0],water_point[1]))*self.window_scale_val)
                #if water_point_ind < len(water_obj.rel_points) - 1:
                    #water_point_2 = water_obj.rel_points[water_point_ind + 1]
                    #pg.draw.line(self.screen, (0, 0, 220), planet.screen_pos + np.array(pol2cart(water_point[0],water_point[1]))*self.window_scale_val,planet.screen_pos + np.array(pol2cart(water_point_2[0],water_point_2[1]))*self.window_scale_val,2)
                #print('ww',water_point)
                #pg.draw.circle(self.screen, (0,0, 220), (planet.screen_pos + np.array(pol2cart(water_point[0],water_point[1]))*self.window_scale_val), 3)
            pg.draw.polygon(self.screen, pg.Color(0,0, 220,90), water_obj_points_set, width=0)
            #pg.draw.polygon(self.water_surface, pg.Color(0,0, 220,90), water_obj_points_set, width=0)
        
 
        #draw the image associated with the planet 
        try:
            planet.planet_display_img = pg.transform.scale(planet.planet_img, (planet.img_scale*self.window_scale_val, planet.img_scale*self.window_scale_val))
            planetRect = planet.planet_display_img.get_rect()
            self.screen.blit(planet.planet_display_img, (planet.screen_pos[0] - planetRect.centerx,planet.screen_pos[1] - planetRect.centery))    
            
            #planetRect = planet.planet_img.get_rect()
            #self.screen.blit(planet.planet_img, (planet.screen_pos[0] - planetRect.centerx,planet.screen_pos[1] - planetRect.centery))    
        except:
            #print(1111)
            pass
        pg.draw.line(self.screen,(255, 0, 0),planet.screen_pos,planet.screen_pos + planet.force*60)
        pg.draw.circle(self.screen,(255, 0, 0),planet.screen_pos,5)
        
        #draw the planet objects as circles
        for planet_obj in planet.planet_obj_list:
            #print(planet_obj.state)
            if planet_obj.obj_type == 'ladder':
                pg.draw.line(self.screen, (233, 255, 0), planet.screen_pos + np.array(pol2cart(planet_obj.rel_pos[0],planet_obj.rel_pos[1]))*self.window_scale_val,planet.screen_pos + np.array(pol2cart(planet_obj.height + planet_obj.rel_pos[0],planet_obj.rel_pos[1]))*self.window_scale_val,2)
            elif planet_obj.obj_type == 'room':
                #print('test val ',pol2cart(planet_obj.rel_pos[0],planet_obj.rel_pos[1]),type(pol2cart(planet_obj.rel_pos[0],planet_obj.rel_pos[1])))
                pg.draw.circle(self.screen, (50 + 100*self.player.inside_flag,0, 0), (planet.screen_pos + np.array(pol2cart(planet_obj.rel_pos[0],planet_obj.rel_pos[1]))*self.window_scale_val), 30)
                if self.player.inside_flag == 1:
                    if planet_obj == self.player.inside_room:
                        pg.draw.circle(self.screen, (50 + 100*self.player.inside_flag,0, 0), (planet.screen_pos + np.array(pol2cart(planet_obj.rel_pos[0],planet_obj.rel_pos[1]))*self.window_scale_val), 60)      
            elif planet_obj.obj_type == 'anchor':
                pg.draw.circle(self.screen, (50 + 50*planet_obj.state,0, 0), (planet.screen_pos + np.array(pol2cart(planet_obj.rel_pos[0],planet_obj.rel_pos[1]))*self.window_scale_val), 30)
                #draw aiming angle 
                if planet_obj.state == 1:
                    #pg.draw.line(self.screen, (233, 255, 0), planet.screen_pos + np.array(pol2cart(planet_obj.rel_pos[0],planet_obj.rel_pos[1]))*self.window_scale_val,planet.screen_pos + np.array(pol2cart(60 + planet_obj.rel_pos[0],planet_obj.rel_pos[1] + planet_obj.aim_angle))*self.window_scale_val,2)    
                    pg.draw.line(self.screen, (233, 255, 0), planet.screen_pos + np.array(pol2cart(planet_obj.rel_pos[0],planet_obj.rel_pos[1]))*self.window_scale_val,planet.screen_pos + np.array(pol2cart(planet_obj.rel_pos[0],planet_obj.rel_pos[1]))*self.window_scale_val + np.array(pol2cart(60, planet_obj.aim_angle))*self.window_scale_val,2)    
                #draw the fired anchor
                if planet_obj.state >= 2 and planet_obj.hooked_obj == None:
                    pg.draw.line(self.screen, (233, 255, 0), planet.screen_pos + np.array(pol2cart(planet_obj.rel_pos[0],planet_obj.rel_pos[1]))*self.window_scale_val,planet.screen_pos + np.array(pol2cart(planet_obj.rel_pos[0],planet_obj.rel_pos[1]))*self.window_scale_val + np.array(pol2cart(planet_obj.deploy_len, planet_obj.aim_angle))*self.window_scale_val,2)              
                if planet_obj.hooked_obj != None:    
                    pg.draw.line(self.screen, (233, 255, 0), planet.screen_pos + np.array(pol2cart(planet_obj.rel_pos[0],planet_obj.rel_pos[1]))*self.window_scale_val,planet_obj.hooked_obj.screen_pos - planet_obj.hooked_rel_obj_point*self.window_scale_val,2)              
            elif planet_obj.obj_type == 'display':
                if planet_obj.state == 1:
                    font = pg.font.SysFont(None, 24)
                    text_img = font.render(str(planet_obj.counter_val), True, (233, 255, 0))
                    self.screen.blit(text_img, (planet.screen_pos + np.array(pol2cart(planet_obj.rel_pos[0],planet_obj.rel_pos[1]))*self.window_scale_val))
            else:
                #print(np.array(pol2cart(planet_obj.rel_pos[0],planet_obj.rel_pos[1])*self.window_scale_val))
                pg.draw.circle(self.screen, (50 + 100*self.player.inside_flag,0, 0), (planet.screen_pos + np.array(pol2cart(planet_obj.rel_pos[0],planet_obj.rel_pos[1]))*self.window_scale_val), 30)
            #draw planet img 
            if planet_obj.img != None:
                if planet_obj.img.get_rect().width == 200:
                    planet_obj_display_img = pg.transform.scale(planet_obj.img, (60*self.window_scale_val, 180*self.window_scale_val))
                elif planet_obj.img.get_rect().width == 300:
                    planet_obj_display_img = pg.transform.scale(planet_obj.img, (150*self.window_scale_val, 100*self.window_scale_val))
                else:
                    planet_obj_display_img = pg.transform.scale(planet_obj.img, (105*self.window_scale_val, 180*self.window_scale_val))                    
                planet_obj_height = planet_obj_display_img.get_rect().height
                planet_obj_display_img = pg.transform.rotate(planet_obj_display_img, planet_obj.img_angle)
                planet_objRect = planet_obj_display_img.get_rect()
                
                surface_vector = np.array(pol2cart(planet_obj.rel_pos[0],planet_obj.rel_pos[1]))
                self.screen.blit(planet_obj_display_img, (planet.screen_pos + surface_vector*self.window_scale_val) - np.array([planet_objRect.centerx,planet_objRect.centery]) + (surface_vector/absval(surface_vector))*0.5*planet_obj_height)

                #draw display
                if planet_obj.obj_type == 'display':
                    if planet_obj.state == 1:
                        font = pg.font.SysFont(None, 24)
                        text_img = font.render(str(planet_obj.counter_val), True, (40, 40, 80))
                        text_img_display = pg.transform.scale(text_img, (45*self.window_scale_val, 20*self.window_scale_val))                  
                        text_img_display = pg.transform.rotate(text_img_display, planet_obj.img_angle)
                        text_objRect = text_img_display.get_rect()
                        self.screen.blit(text_img_display, (planet.screen_pos + np.array(pol2cart(planet_obj.rel_pos[0],planet_obj.rel_pos[1]))*self.window_scale_val - np.array([planet_objRect.centerx,planet_objRect.centery]) + np.array([text_objRect.centerx,text_objRect.centery])))# + (surface_vector/absval(surface_vector))*0.7*planet_obj_height))
        

        # #draw water step
        # for water_obj in planet.water_obj_list:
        #     print('rel points ',water_obj.rel_points)
        #     water_obj_points_set = [planet.screen_pos]
        #     for water_point_ind, water_point in enumerate(water_obj.rel_points):
        #         water_obj_points_set.append(planet.screen_pos + np.array(pol2cart(water_point[0],water_point[1]))*self.window_scale_val)
        #         #if water_point_ind < len(water_obj.rel_points) - 1:
        #             #water_point_2 = water_obj.rel_points[water_point_ind + 1]
        #             #pg.draw.line(self.screen, (0, 0, 220), planet.screen_pos + np.array(pol2cart(water_point[0],water_point[1]))*self.window_scale_val,planet.screen_pos + np.array(pol2cart(water_point_2[0],water_point_2[1]))*self.window_scale_val,2)
        #         #print('ww',water_point)
        #         #pg.draw.circle(self.screen, (0,0, 220), (planet.screen_pos + np.array(pol2cart(water_point[0],water_point[1]))*self.window_scale_val), 3)
        #     pg.draw.polygon(self.screen, pg.Color(0,0, 220,90), water_obj_points_set, width=0)
        #     #pg.draw.polygon(self.water_surface, pg.Color(0,0, 220,90), water_obj_points_set, width=0)

        #draw the planet itself ----------------
        #print('positions planet',planet.screen_pos)
        if absval(planet.screen_pos) <= np.sqrt((self.window_x_size*2)**2 + (self.window_y_size*2)**2):
            #draw the object
            #pg.draw.circle(screen, (0, 255, 0), planet.screen_pos, planet.max_rad*self.window_scale_val)
            for point in planet.geom:
                #print(test)
                pg.draw.circle(self.screen, (233, 255, 0), planet.screen_pos + np.array([pol2cart(point[0][0],point[0][1])[0],-1*pol2cart(point[0][0],point[0][1])[1]])*self.window_scale_val, 4)
                if point[2] =='arc':
                    max_rad = max([point[0][0], point[1][0]])
                    #pg.draw.arc(screen, (233, 255, 0), [100,100,175,175], point[0][1], point[1][1],2)
                    #pg.draw.arc(screen, (233, 255, 0), [300,300,375,375], point[0][1], point[1][1],2)
                    
                    pg.draw.arc(self.screen, (233, 255, 0), list(planet.screen_pos - np.array([max_rad,max_rad])*self.window_scale_val)+[2*max_rad*self.window_scale_val,2*max_rad*self.window_scale_val], point[0][1], point[1][1],2)
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

    def draw_obj(self, obj):
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

    def screen_step(self):
        if self.player.inside_flag == 0:
            if self.player.prev_inside_flag == 1:
                self.window_pos = self.player.pos
                print('t')
            #update draw positions
            for obj in self.object_list:
                self.draw_obj(obj)
                
            for star_ind, stars in enumerate(self.stars_list):
                for star in stars:
                    star_pos = ((star - self.window_pos)*self.window_scale_val*(0.10 + 0.15*star_ind)) + np.array([self.window_x_size/2,self.window_y_size/2])
                    pg.draw.circle(self.screen, (255, 255, 255), star_pos, 3)
                    
            for planet in self.planet_list:
                self.draw_planet(planet)

            for obj in self.object_list:
                pg.draw.line(self.screen,(255, 0, 255),obj.screen_pos,obj.screen_pos + obj.vel*600)
                pg.draw.line(self.screen,(255, 120, 255),obj.screen_pos,obj.screen_pos + obj.force*600)
        else:
            try:
                self.draw_planet(self.room_obj)     
                self.draw_obj(self.player)
            except:
                pass                    
                
    def orth_vec(self,v):
        return np.array([v[1],-1*v[0]])            

    def planet_contact(self, planet, obj):
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
                #print(11111111111111111111111,abs(obj_dist_pol[1]),geom_point)
                if ((geom_point[0][1] < abs(obj_dist_pol[1]) <= geom_point[1][1])
                or (geom_point[0][1] >= abs(obj_dist_pol[1]) > geom_point[1][1])):
                    point_list.append(geom_point)
                if geom_point[0][1] == geom_point[1][1]:
                    if abs(geom_point[0][1] - abs(obj_dist_pol[1])) < 0.05*np.pi:
                        vert_point_list.append(geom_point)

            #get the corresponding radius at point 
            rad_list = []
            intersect_point_list = []
            for point in point_list:
                if point[2] == 'arc':
                    rad = point[0][0]
                    #print('rad ',rad)
                    rad_list.append(rad)
                    intersect_point_list.append(None)
                if point[2] == 'line':
                    diff_rad = point[1][0] - point[0][0]
                    diff_phi = point[1][1] - point[0][1]
                    min_rad = min([point[1][0], point[0][0]])
                    #rad = diff_rad * np.cos(diff_phi - obj_dist_pol[1]) + point[0][0]
                    #get the intersect point
                    intersect_point = line_intersection([np.array([0.0,0.0]),pol2cart(obj_dist_pol[0],obj_dist_pol[1])], [np.array(pol2cart(point[0][0],point[0][1])),np.array(pol2cart(point[1][0],point[1][1]))])
                    intersect_point_list.append(intersect_point_list)
                    rad = absval(intersect_point)
                    rad_list.append(rad)
            #print('intersect_point_list ',intersect_point_list, point_list, 'vert list ',vert_point_list)
            #print('rad list ',rad_list)
            #if len(rad_list) > 1:
                # print(t)
            if rad_list != []:
                min_rad = min(rad_list)
                max_rad = max(rad_list)
                #print('min rad ',min_rad, max_rad,abs(obj_dist_pol[0]))
                other_rad_list = [rad for rad in rad_list if rad != max_rad]
                if other_rad_list != []:
                    other_rad = max(other_rad_list)
                    if abs(obj_dist_pol[0]) >= abs(other_rad) and other_rad != min_rad:
                        rad = max_rad
                    else:
                        rad = min_rad
                elif abs(obj_dist_pol[0]) >= abs(max_rad):
                    rad = max_rad
                else:
                    rad = min_rad
                point = point_list[rad_list.index(rad)]

                if point[2] == 'line':
                    intersect_point = intersect_point_list[rad_list.index(rad)]
                    self.intersect_point = intersect_point
                
                #if radius of point smaller than the surface radius
                if (abs(rad) >= abs(obj_dist_pol[0]) 
                or abs(rad) >= abs(cart2pol(-1*(obj_dist_vec - obj.g_force)[0], (obj_dist_vec - obj.g_force)[1])[0])):                  
                    obj.contact_flag = 1
                    obj.contact_flag_obj = planet
                    
                    #if radius significantly smaller adjust 
                    if 0.998*abs(rad) > abs(obj_dist_pol[0]) and point not in vert_point_list:
                        #this if statement may need removing and fn retaining
                        #if point[2] == 'line' or rad == min([other_point[0] for other_point in point_list if other_point[2] != 'line']):
                        obj.pos -= obj_dist_vec*((rad - obj_dist_pol[0])/rad)

                    #add movement speed and movement force here
                    obj.m_speed = (1-point[3])*obj.m_speed    
                    if abs(obj.m_speed) < 0.01:
                        obj.m_speed = 0.0
                    #obj.m_force += obj.m_speed*(self.orth_vec(obj.down))
 
                    #get the normal force of total force 
                    if point[2] == 'arc':
                        obj.m_force += obj.m_speed*(self.orth_vec(obj.down))
                        #add the m force to the total force 
                        obj.force += obj.m_force
                        #obj.force += planet.force
                        #obj_dist_vec += planet.force
                        
                        # print('planet pos ',planet.pos)
                        # print('obj dist vec ',obj_dist_vec)
                        # print('obj force ',obj.force, obj.g_force, planet.force, obj.vel, obj.m_force)
                        # print('normal ',-1*vec_comp(obj.force, obj_dist_vec/absval(obj_dist_vec))*(obj_dist_vec/absval(obj_dist_vec)))
                        
                        if np.sign(obj.force[0]) == np.sign(obj_dist_vec[0]) or np.sign(obj.force[1]) == np.sign(obj_dist_vec[1]):
                            normal_force += -1*vec_comp(obj.force, obj_dist_vec/absval(obj_dist_vec))*(obj_dist_vec/absval(obj_dist_vec))
                        #add planet speed component
                        #normal_force += vec_comp(planet.force, obj_dist_vec/absval(obj_dist_vec))*(obj_dist_vec/absval(obj_dist_vec))
                        
                        #get the velocity normal component 
                        if ((obj.move_keys[2] == 0 and obj.prev_move_keys[2] == 0) 
                        or (obj.move_keys[2] == 1)):
                            vel_comp = vec_comp(obj.vel, obj.down/absval(obj.down))*(obj.down/absval(obj.down))
                            obj.vel += -1*vel_comp
                            obj.vel = (1-2*point[3])*obj.vel  

                        if absval(obj.vel) < 0.04:
                            obj.vel = np.zeros(2)
                            
                        #add normal force
                        obj.n_force = normal_force
                        #add planet force 
                        obj.force += planet.force
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

                        #get proportion of normal force                                      
                        delta_angle = 4*(point[1][1] - point[0][1])/np.pi
                        if delta_angle <= 0.05:
                            normal_mod = 0.0
                        elif point[3] > 0.75:
                            normal_mod = min([4*delta_angle,1])
                        else:
                            normal_mod = min([3*delta_angle*(point[3] + 0.25), 1])
                        #print('normsl mod ---',3*delta_angle*(point[3] + 0.25), normal_mod, delta_angle)
                        #print(vec_comp(obj.force, orth_vec)*(orth_vec/absval(orth_vec)))
                        #print('down ',orth_vec, vec_comp(obj.force, obj_dist_vec/absval(obj_dist_vec))*(obj_dist_vec/absval(obj_dist_vec)))
                        #test for different 
                        if np.sign(obj.force[0]) == np.sign(obj_dist_vec[0]) or np.sign(obj.force[1]) == np.sign(obj_dist_vec[1]):  
                            normal_force += -(1.0 - normal_mod)*vec_comp(obj.force, orth_vec)*(orth_vec/absval(orth_vec)) -normal_mod*vec_comp(obj.force, obj_dist_vec/absval(obj_dist_vec))*(obj_dist_vec/absval(obj_dist_vec))
 
                        #add planet speed component
                        #normal_force += -1*(normal_mod)*vec_comp(planet.force, obj_dist_vec/absval(obj_dist_vec))*(obj_dist_vec/absval(obj_dist_vec))
                        #normal_force += (1.0 - normal_mod)*vec_comp(planet.force, orth_vec)*(orth_vec/absval(orth_vec)) 
                        
                                                
                        #get the velocity normal component 
                        if ((obj.move_keys[2] == 0 and obj.prev_move_keys[2] == 0) 
                        or (obj.move_keys[2] == 1)):                                   
                            obj.vel -= vec_comp(obj.vel, orth_vec)*(orth_vec/absval(orth_vec))
                            #vel_comp = vec_comp(obj.vel, obj.down/absval(obj.down))*(obj.down/absval(obj.down))
                            #obj.vel += -1*vel_comp
                            obj.vel = (1-2*point[3])*obj.vel  
  
                        if absval(obj.vel) < 0.04:
                            obj.vel = np.zeros(2)
                    
                        #add normal force 
                        obj.n_force = normal_force
                        obj.force += planet.force
                        #print('LINE')
                    if vert_point_list != []:
                        for vert_point in vert_point_list:
                            #if rad smaller than the point rad
                            if (0.94*max(vert_point[0][0],vert_point[1][0]) > abs(obj_dist_pol[0]) 
                            and 0.90*min(vert_point[0][0],vert_point[1][0]) <= abs(obj_dist_pol[0])):
                                #get next step position 
                                next_pos = planet.pos - (obj.pos + obj.m_force)
                                next_pos = planet.pos - (obj.pos + obj.force)
                                
                                #print('t',obj_dist_vec, cart2pol(-1*obj_dist_vec[0],obj_dist_vec[1]), obj_dist_pol)
                                next_pos_pol = cart2pol(-1*next_pos[0], next_pos[1])
                                #print(t)
                                #if will cross radius
                                if (next_pos_pol[1] >= vert_point[0][1] >= obj_dist_pol[1]) or (obj_dist_pol[1] >= vert_point[0][1] >= next_pos_pol[1]):
                                    #get the cart points 
                                    new_point_line = np.array(pol2cart(vert_point[1][0], vert_point[1][1])) - np.array(pol2cart(vert_point[0][0], vert_point[0][1]))
                                    if obj_dist_pol[1] > 1.0*np.pi:
                                        orth_vec = np.array([-1*new_point_line[1],-1*new_point_line[0]])
                                    else:    
                                        orth_vec = np.array([-1*new_point_line[1],-1*new_point_line[0]])
                                    normal_force += -1.0*vec_comp(obj.force, orth_vec)*(orth_vec/absval(orth_vec))

                
                    #print('teststssss4-------------------', normal_force,obj.force,obj.m_speed)
                    obj.force += obj.vel
                    obj.force += normal_force 
            #water contact 
            self.water_contact(planet, obj, obj_dist, obj_dist_vec, obj_dist_pol)
            
            #water movement 
            if obj.water_contact_flag == 1:
                if obj.move_flag == 1:
                    obj.force += 0.4*obj.m_speed*(self.orth_vec(obj.down))
                else:
                    obj.m_speed = 0.5*obj.m_speed
                    obj.force += 0.4*obj.m_speed*(self.orth_vec(obj.down))
                    # if obj.move_flag == 1:
                    #     print(t)
                        
    def water_contact(self, planet, obj, obj_dist, obj_dist_vec, obj_dist_pol):
        #rad_list = []
        #water_intersect_point_list = []
        for water_obj in planet.water_obj_list:
            #if in range of water
            if 2*np.pi - (water_obj.arc_start  + water_obj.arc) <= obj_dist_pol[1] < 2*np.pi - (water_obj.arc_start):
                #go througfh points 
                #print(obj_dist_pol[1])
                for water_ind, water_point in enumerate(water_obj.rel_points):
                    #print('water point ', water_point)
                    if water_ind < len(water_obj.rel_points) - 1:
                        next_water_point = water_obj.rel_points[water_ind + 1]
                        #get the corresponding radius at point 
                        diff_rad = next_water_point[0] - water_point[0]
                        diff_phi = next_water_point[1] - water_point[1]
                        #print('diff rad ',diff_rad,next_water_point[0], water_point[0])
                        min_rad = min([next_water_point[0], water_point[0]])
                        min_phi = min([2*np.pi - next_water_point[1], 2*np.pi - water_point[1]])
                        max_phi = max([2*np.pi - next_water_point[1], 2*np.pi - water_point[1]])
                        #print(t)
                        if min_phi < obj_dist_pol[1] < max_phi:
                            rad_val = ((obj_dist_pol[1] - min_phi)/diff_phi)*diff_rad + min_rad
                            #print(t)
                            if obj_dist_pol[0] < rad_val:
                                obj.force += (-1.5)*obj.g_force
                                #obj.vel = np.zeros(2)
                                obj.water_contact_flag = 1
                                #print(t)

    def step(self):
        for obj in self.object_list:
            #reset forces 
            obj.m_force = np.zeros(2)
            obj.g_force = np.zeros(2)
            obj.n_force = np.zeros(2) 
            
            #get the move force
            obj.move_force()
            
            #reset contact flag 
            obj.contact_flag = 0 
            obj.water_contact_flag = 0
            
            #apply gravity depending on room or not 
            if self.player.inside_flag == 0:
                if self.player.prev_inside_flag == 1:
                    self.player.prev_inside_flag = 0
                    self.window_scale_val = self.prev_window_scale_val
                    self.room_obj = None
                    #reset the velocity when leaving the room
                    for planet in self.planet_list:
                        planet.vel = planet.outside_vel.copy()
                for planet in self.planet_list:
                    #get the gravitional effect on each object
                    obj_dist_vec = planet.pos - obj.pos
                    obj_dist = absval(obj_dist_vec)
                    if obj_dist <= planet.g_max_rad:
                        obj.g_force += obj_dist_vec*planet.grav_force(obj_dist)
            elif self.player.inside_flag == 1:  
                if self.room_obj == None:
                    room = self.sector_room_list[self.player.inside_room]
                    self.room_obj = self.load_room(room, self.player.contact_flag_obj)
                    self.prev_window_scale_val = np.float(self.window_scale_val + 0.01)
                    self.window_scale_val = max([self.window_scale_val,self.room_scale_val])
                    #reset the velocity when leaving the room
                    for planet in self.planet_list:
                        planet.outside_vel = planet.vel.copy()
                        
                obj_dist_vec = self.room_obj.pos - obj.pos
                obj_dist = absval(obj_dist_vec)
                if obj_dist <= self.room_obj.g_max_rad:
                    obj.g_force += obj_dist_vec*self.room_obj.grav_force(obj_dist)                

            #update down of the object 
            obj.down = obj.g_force/absval(obj.g_force)
            #update the jump force
            if absval(obj.vel) != 0:
                obj.vel = obj.vel 
            
            #update the total force
            obj.force = obj.g_force.copy()
            
            #check if in contact 
            if self.player.inside_flag == 0:
                for i, planet in enumerate(self.planet_list):
                    #####------------------ deal with the interaction with the objects
                    #get the gravitional effect on each object
                    self.planet_contact(planet, obj)
            else:
                self.planet_contact(self.room_obj, obj)
            
            if obj.contact_flag == 0 or (obj.move_keys[2]==0 and obj.prev_move_keys[2] == 1):
                if obj.water_contact_flag == 1:
                    water_mod = 0.2
                else:
                    water_mod = 1.0
                obj.vel += water_mod*obj.g_force
                obj.force += obj.vel
                # if (obj.move_keys[2]==0 and obj.prev_move_keys[2] == 1):
                #     #print('222222222',obj.vel, obj.g_force, obj.down, 1,obj.vel/obj.down,1, obj.m_force)
                #     #print(obj.TEST_move_flags_list)
                #     print(obj.contact_flag)
                    
            #slow vel if in water 
            if obj.water_contact_flag == 1:
                obj.vel = (1-0.7)*obj.vel  
                    
        # #update object speed -------
        
        #update object position 
        for obj in self.object_list:
            #get the move force
            if obj.contact_flag == 0 and obj.water_contact_flag == 0:
                obj.m_force = obj.m_speed*(self.orth_vec(obj.down))
                obj.force += obj.m_force
            #obj.move_force()
            obj.action_fn(self.planet_list)
            #update the position 
            obj.pos += obj.force 
            #update prev move keys 
            obj.prev_move_keys = obj.move_keys.copy()
  
        if self.player.inside_flag == 0:
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
                                if planet.mass + planet_2.mass != 0.0:
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
                    #step for anchor 
                    if planet_obj.obj_type == 'anchor' and planet_obj.state == 3:
                        planet_obj.anchor_step(planet)
                    #step for display state 1 == timer
                    if planet_obj.obj_type == 'display' and planet_obj.state == 1:
                        planet_obj.counter_step(planet.pos)#, target_planet.pos)                
                    
                #update water object 
                for water_obj in planet.water_obj_list:
                    water_obj.water_step([planet2 for planet2 in self.planet_list if planet2 != planet])