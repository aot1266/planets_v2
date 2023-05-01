import numpy as np
import pandas as pd
import pygame as pg
from core_fns import absval, cart2pol, pol2cart, vec_comp, orth_vec, line_intersection, intersection

def orth_vec(v):
    return np.array([v[1],-1*v[0]])    

def planet_anchor_contact(planet, obj):
    obj_dist_vec = planet.pos - obj.hooked_pos
    obj_dist = absval(obj_dist_vec)                
    #check if contacting planet 
    intersect_point = None
    contact_flag = 0
    
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
                print('intersect point 1 ', intersect_point_list)
            if point[2] == 'line':
                diff_rad = point[1][0] - point[0][0]
                diff_phi = point[1][1] - point[0][1]
                min_rad = min([point[1][0], point[0][0]])
                #rad = diff_rad * np.cos(diff_phi - obj_dist_pol[1]) + point[0][0]
                #get the intersect point
                intersect_point = line_intersection([np.array([0.0,0.0]),pol2cart(obj_dist_pol[0],obj_dist_pol[1])], [np.array(pol2cart(point[0][0],point[0][1])),np.array(pol2cart(point[1][0],point[1][1]))])
                intersect_point_list.append(intersect_point)
                rad = absval(intersect_point)
                rad_list.append(rad)
        #print('intersect_point_list ',intersect_point_list, point_list, 'vert list ',vert_point_list)
        #print('rad list ',rad_list)
        #if len(rad_list) > 1:
            # print(t)
        print('intersect_point_list) ',intersect_point_list,planet.pos, obj.hooked_pos)

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
                print('point ',obj.hooked_pos)
                print('test ',intersect_point_list,rad_list.index(rad))
                intersect_point = intersect_point_list[rad_list.index(rad)]
                print('intersect point ',intersect_point)
                obj.hooked_pos = intersect_point
            #if radius of point smaller than the surface radius
            if abs(rad) >= abs(obj_dist_pol[0]):                  
                contact_flag = 1
                
                #if radius significantly smaller adjust 
                if 0.998*abs(rad) > abs(obj_dist_pol[0]) and point not in vert_point_list:
                    #this if statement may need removing and fn retaining
                    #if point[2] == 'line' or rad == min([other_point[0] for other_point in point_list if other_point[2] != 'line']):
                    obj.hooked_pos -= obj_dist_vec*((rad - obj_dist_pol[0])/rad)
                obj.hooked_flag = 1
                obj.hooked_rad = rad
                obj.hooked_obj = planet
                obj.hooked_rel_obj_point = obj_dist_vec

    if contact_flag == 1:
        obj.hooked_flag = 1
        obj.hooked_rad = rad
        obj.hooked_obj = planet
        obj.hooked_rel_obj_point = obj_dist_vec        

