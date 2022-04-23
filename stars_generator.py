import numpy as np
import pandas as pd
import pygame as pg
import random as rn 
import json 

#starfield 
from scipy import stats
starfield = []
stars_dict = {}
for i in range (0,3):
    stars = []
    for j in range(0,200 + 50*i):
        #x = rn.randint(-500, 500)
        #y = rn.randint(40, 400)
        x = rn.uniform(-5000*(1 + 0.5*i), 5000*(1 + 0.5*i))
        y = rn.uniform(-5000*(1 + 0.5*i), 5000*(1 + 0.5*i))        
        #stars.append(np.random.rand(2)*5000)
        stars.append([x,y])
    starfield.append(stars)
    stars_dict['stars_'+str(i)] = stars
    
file = {'stars': starfield}

with open('stars_data.json', 'w') as outfile:
    json.dump(file, outfile)