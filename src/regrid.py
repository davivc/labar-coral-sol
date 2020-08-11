import numpy as np
import cf
import cfplot as cfp

from netCDF4 import Dataset
# from netcdf_dump import ncdump

nc_file = 'data/global-reanalysis-phy-001-030-daily_test.nc'

# Regridding
# https://ncas-cms.github.io/cf-python/tutorial.html#regridding
f = cf.read(nc_file)
eastward_v = f[4]
# g = cf.read_field(nc_file, select='eastward_sea_water_velocity')
print(f)

# Find attributes
nc_fid = Dataset(nc_file, 'r')  # Dataset is the class behavior to open the file
                                # and create an instance of the ncCDF4 class
# nc_attrs, nc_dims, nc_vars = ncdump(nc_fid)

time = nc_fid.variables['time'][:]
lats = nc_fid.variables['latitude'][:]  # extract/copy the data
lons = nc_fid.variables['longitude'][:]

base_step = 0.083
# Define the output grid
lat = cf.DimensionCoordinate(data=cf.Data(np.arange(-28, -26, base_step/2), 'degreesN'))
lon = cf.DimensionCoordinate(data=cf.Data(np.arange(360-49, 360-48, base_step/2), 'degreesE'))

# Regrid the field
import pdb; pdb.set_trace()
g = eastward_v.regrids({'latitude': lat, 'longitude': lon}, method='linear')
print(g)

cfp.gopen(rows=1, columns=2)
cfp.gpos(1)
cfp.con(f[0], blockfill=True, lines=False, colorbar_label_skip=2)
cfp.gpos(2)
cfp.con(g[0], blockfill=True, lines=False, colorbar_label_skip=2)
cfp.gclose()