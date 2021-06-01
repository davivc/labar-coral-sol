import geopandas as gpd

import matplotlib as mpl    
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt

from cartopy.io.shapereader import Reader
from cartopy.feature import ShapelyFeature
from cartopy.feature import LAND
from cartopy.feature import OCEAN

def plotTrajectories(domain, data=None, zoom=11, shape_file=None):
    # request = cimgt.Stamen('terrain-background')
    # request = cimgt.OSM(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36 Edg/86.0.622.69')
    request = cimgt.OSM()

    fig = plt.figure(figsize=[15,15])
    ax = fig.add_subplot(1, 1, 1)  # specify (nrows, ncols, axnum)

    ax = plt.axes(projection=request.crs)
    ax.set_extent(domain, crs=ccrs.PlateCarree())
    # ax.add_image(request, 4, interpolation='spline36')
    ax.add_image(request, zoom, alpha=0.75)
    if shape_file:
        shape_feature = ShapelyFeature(Reader(shape_file).geometries(),
                                ccrs.PlateCarree(), facecolor='red', alpha=0.5)
        ax.add_feature(shape_feature)
        # ax.add_geometries(Reader(shape_file).geometries(),
        #            ccrs.PlateCarree(), facecolor='red', alpha=0.5)
    if data:
        ax.plot(data['lon'].T, data['lat'].T, marker='o', transform=ccrs.PlateCarree())

    ax.add_feature(OCEAN)
    plt.show()