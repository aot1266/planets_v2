import numpy as np
import pandas as pd

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

#get angles
def angle_between(p1, p2):
    ang1 = np.arctan2(*p1[::-1])
    ang2 = np.arctan2(*p2[::-1])
    return (ang1 - ang2) % (2 * np.pi)

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
