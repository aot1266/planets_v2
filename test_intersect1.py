import numpy as np
def line_intersection(line1, line2):
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
       raise Exception('lines do not intersect')

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return x, y

def pol2cart(rho, phi):
    x = rho * np.cos(phi)
    y = rho * np.sin(phi)
    return(x, y)

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

def det_2(x1,y1,x2,y2):
    return x1*y2 - x2*y1

def intersection(l1p1,l1p2,l2p1,l2p2):
    denom = (l1p1[0] - l1p2[0])*(l2p1[1] - l2p2[1]) - (l1p1[1] - l1p2[1])*(l2p1[0] - l2p2[0])
    px = ((l1p1[0]*l1p2[1] - l1p2[0]*l1p1[1])*(l2p1[0] - l2p2[0]) -  (l2p1[0]*l2p2[1] - l2p2[0]*l2p1[1])*(l1p1[0] - l1p2[0]))/denom
    py = ((l1p1[0]*l1p2[1] - l1p2[0]*l1p1[1])*(l2p1[1] - l2p2[1]) -  (l2p1[0]*l2p2[1] - l2p2[0]*l2p1[1])*(l1p1[1] - l1p2[1]))/denom
    return np.array([px,py])

#print(line_intersection((A, B), (C, D)))

print(line_intersection([[0,1],[10,20]],[[10,10],[-10,10]]))
print(line_intersection([[0,1],[10,20]],[[10,-10],[-10,10]]))
print(line_intersection([[-2,3],[2,0]],[[1,4],[-0.5,-1]]))

print(intersection([0,1],[10,20],[10,10],[-10,10]))
print(intersection([0,1],[10,20],[10,-10],[-10,10]))
print(intersection([-2,3],[2,0],[1,4],[-0.5,-1]))

p1 = pol2cart(75.0,0.0)
p2 = pol2cart(105.0,0.5*np.pi)
p3 = pol2cart(125.0,0.2*np.pi)
print(p1,p2)
print(intersection(p1,p2,[0.0,0.0],p3))
print(absval(intersection(p1,p2,[0.0,0.0],p3)))
print(cart2pol(intersection(p1,p2,[0.0,0.0],p3)[0],intersection(p1,p2,[0.0,0.0],p3)[1]/np.pi))

p3 = pol2cart(125.0,0.3*np.pi)
print(p1,p2)
print(intersection(p1,p2,[0.0,0.0],p3))
print(absval(intersection(p1,p2,[0.0,0.0],p3)))
print(cart2pol(intersection(p1,p2,[0.0,0.0],p3)[0],intersection(p1,p2,[0.0,0.0],p3)[1]/np.pi))

p3 = pol2cart(125.0,0.4*np.pi)
print(p1,p2)
print(intersection(p1,p2,[0.0,0.0],p3))
print(absval(intersection(p1,p2,[0.0,0.0],p3)))
print(cart2pol(intersection(p1,p2,[0.0,0.0],p3)[0],intersection(p1,p2,[0.0,0.0],p3)[1]/np.pi))

p3 = pol2cart(125.0,0.45*np.pi)
print(p1,p2)
print(intersection(p1,p2,[0.0,0.0],p3))
print(absval(intersection(p1,p2,[0.0,0.0],p3)))
print(cart2pol(intersection(p1,p2,[0.0,0.0],p3)[0],intersection(p1,p2,[0.0,0.0],p3)[1]/np.pi))

p3 = pol2cart(125.0,0.1*np.pi)
print(p1,p2)
print(intersection(p1,p2,[0.0,0.0],p3))
print(absval(intersection(p1,p2,[0.0,0.0],p3)))
print(cart2pol(intersection(p1,p2,[0.0,0.0],p3)[0],intersection(p1,p2,[0.0,0.0],p3)[1]/np.pi))