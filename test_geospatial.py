from shapely.geometry import Point, Polygon, LinearRing
import numpy as np
# Create Point objects
p1 = Point(77.049909,28.568399)
p2 = Point(24.895, 60.05)

# Create a square
coords = [(77.0503707,28.5587053), (77.0566288,28.5675884),(77.0503707,28.5587053)]
poly = LinearRing(coords)

N=10
lat = np.random.uniform(28.5587053,28.5687945,N)
lon = np.random.uniform(77.0503707,77.0574443,N)
#print(lat)
#print(lon)
# PIP test with 'within'
print(p1.within(poly))     # True
print(p2.within(poly))     # False

# PIP test with 'contains'
poly.contains(p1)   # True
poly.contains(p2)   # False