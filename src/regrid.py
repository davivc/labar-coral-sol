import os
import sys
import numpy as np
import cf
import cfplot as cfp
import matplotlib as mpl
if os.environ.get('DISPLAY','') == '':
    print('no display found. Using non-interactive Agg backend')
    mpl.use('Agg')

from netCDF4 import Dataset


def main(argv):
    try:
        year = sys.argv[1]
    except:
        print("You must pass a year as arg")
        sys.exit()

    # Find attributes
    print('Loading NetCDF file')
    nc_file = 'data/global-reanalysis-phy-001-030-daily-{0}.nc'.format(year)
    nc_fid = Dataset(nc_file, 'r')  # Dataset is the class behavior to open the file
                                    # and create an instance of the ncCDF4 class
    time = nc_fid.variables['time'][:]
    lats = nc_fid.variables['latitude'][:]  # extract/copy the data
    lons = nc_fid.variables['longitude'][:]

    base_step = 0.083
    base_folder = 'data/regrids'

    # Regridding
    # https://ncas-cms.github.io/cf-python/tutorial.html#regridding
    grid_9km = cf.read(nc_file)
    print('Loading grids of 9km')
    grid_9km_temp = grid_9km[0]
    grid_9km_u0 = grid_9km[1]
    grid_9km_v0 = grid_9km[2]

    # Here we select only one depth because regridding all the resulting nc file is too large
    print('Loading one depth')
    grid_9km_temp = grid_9km_temp[:,0,:,:]
    grid_9km_u0 = grid_9km_u0[:,0,:,:]
    grid_9km_v0 = grid_9km_v0[:,0,:,:]
    import pdb; pdb.set_trace()
    cf.write(grid_9km_u0, '{0}/grid_9km_u0-{1}.nc'.format(base_folder, year))
    cf.write(grid_9km_v0, '{0}/grid_9km_v0-{1}.nc'.format(base_folder, year))
    cf.write(grid_9km_temp, '{0}/grid_9km_temp-{1}.nc'.format(base_folder, year))

    # Define the output grid
    print('Defining output grid of 3km')
    lat = cf.DimensionCoordinate(data=cf.Data(np.arange(-28, -26, base_step/3), 'degreesN'))
    lon = cf.DimensionCoordinate(data=cf.Data(np.arange(-49, -48, base_step/3), 'degreesE'))
    # Regrid the field
    print('Regriding 9km to 3km for u0...')
    grid_3km_u0 = grid_9km_u0.regrids({'latitude': lat, 'longitude': lon}, method='linear')
    print('Writing nc file for regrided 3km u0...')
    cf.write(grid_3km_u0, '{0}/grid_3km_u0-{1}.nc'.format(base_folder, year))

    print('Regriding 9km to 3km for v0...')
    grid_3km_v0 = grid_9km_v0.regrids({'latitude': lat, 'longitude': lon}, method='linear')
    print('Writing nc file for regrided 3km v0...')
    cf.write(grid_3km_v0, '{0}/grid_3km_v0-{1}.nc'.format(base_folder, year))

    print('Regriding 9km to 3km for temp...')
    grid_3km_temp = grid_9km_temp.regrids({'latitude': lat, 'longitude': lon}, method='linear')
    print('Writing nc file for regrided 3km temp...')
    cf.write(grid_3km_temp, '{0}/grid_3km_temp-{1}.nc'.format(base_folder, year))

    # Define the output grid
    print('Defining output grid of 1km')
    lat = cf.DimensionCoordinate(data=cf.Data(np.arange(-28, -26, base_step/9), 'degreesN'))
    lon = cf.DimensionCoordinate(data=cf.Data(np.arange(-49, -48, base_step/9), 'degreesE'))
    # Regrid the field
    print('Regriding 3km to 1km for u0...')
    grid_1km_u0 = grid_3km_u0.regrids({'latitude': lat, 'longitude': lon}, method='linear')
    print('Writing nc file for regrided 1km u0...')
    cf.write(grid_1km_u0, '{0}/grid_1km_u0-{1}.nc'.format(base_folder, year))

    print('Regriding 3km to 1km for v0...')
    grid_1km_v0 = grid_3km_v0.regrids({'latitude': lat, 'longitude': lon}, method='linear')
    print('Writing nc file for regrided 1km v0...')
    cf.write(grid_1km_v0, '{0}/grid_1km_v0-{1}.nc'.format(base_folder, year))

    print('Regriding 3km to 1km for temp...')
    grid_1km_temp = grid_3km_temp.regrids({'latitude': lat, 'longitude': lon}, method='linear')
    print('Writing nc file for regrided 1km temp...')
    cf.write(grid_1km_temp, '{0}/grid_1km_temp-{1}.nc'.format(base_folder, year))

    # Define the output grid
    print('Defining output grid of 500m')
    lat = cf.DimensionCoordinate(data=cf.Data(np.arange(-28, -26, base_step/18), 'degreesN'))
    lon = cf.DimensionCoordinate(data=cf.Data(np.arange(-49, -48, base_step/18), 'degreesE'))
    # Regrid the field
    print('Regriding 1km to 500m for u0...')
    grid_500m_u0 = grid_1km_u0.regrids({'latitude': lat, 'longitude': lon}, method='linear')
    print('Writing nc file for regrided 500m u0...')
    cf.write(grid_500m_u0, '{0}/grid_500m_u0-{1}.nc'.format(base_folder, year))

    print('Regriding 1km to 500m for v0...')
    grid_500m_v0 = grid_1km_v0.regrids({'latitude': lat, 'longitude': lon}, method='linear')
    print('Writing nc file for regrided 500m v0...')
    cf.write(grid_500m_v0, '{0}/grid_500m_v0-{1}.nc'.format(base_folder, year))

    print('Regriding 1km to 500m for temp...')
    grid_500m_temp = grid_1km_temp.regrids({'latitude': lat, 'longitude': lon}, method='linear')
    print('Writing nc file for regrided 500m temp...')
    cf.write(grid_500m_temp, '{0}/grid_500m_temp-{1}.nc'.format(base_folder, year))

if __name__ == '__main__':
    main(sys.argv[0:])