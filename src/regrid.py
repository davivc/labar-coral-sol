import os
import sys
import numpy as np
import cf
import cfplot as cfp
import matplotlib as mpl
import psutil
import gc
process = psutil.Process(os.getpid())

if os.environ.get('DISPLAY','') == '':
    print('no display found. Using non-interactive Agg backend')
    mpl.use('Agg')

from netCDF4 import Dataset

def main(argv):
    try:
        year = sys.argv[1]
        years = [year]
    except:
        years = range(1993, 2018)

    for year in years:
        # Find attributes
        print('Loading NetCDF file')
        nc_file = 'data/global-reanalysis-phy-001-030-daily/00_base/global-reanalysis-phy-001-030-daily-{0}.nc'.format(year)
        print(nc_file)
        nc_fid = Dataset(nc_file, 'r')  # Dataset is the class behavior to open the file
                                        # and create an instance of the ncCDF4 class
        time = nc_fid.variables['time'][:]
        lats = nc_fid.variables['latitude'][:]  # extract/copy the data
        lons = nc_fid.variables['longitude'][:]

        print('Memory: ', process.memory_info().rss)

        base_step = 0.083
        new_lat = [-30, -25]
        new_long = [-49, -45]
        base_folder = 'data/global-reanalysis-phy-001-030-daily'
        

        # Regridding
        # https://ncas-cms.github.io/cf-python/tutorial.html#regridding
        print('Loading grids of 9km')
        grid_9km_temp = cf.read(nc_file, select='sea_water_potential_temperature')[0]
        grid_9km_uo = cf.read(nc_file, select='eastward_sea_water_velocity')[0]
        grid_9km_vo = cf.read(nc_file, select='northward_sea_water_velocity')[0]

        print('Memory: ', process.memory_info().rss / 1024 / 1024 ** 2)

        # Here we select only one depth because regridding all the resulting nc file is too large
        print('Loading one depth')
        grid_9km_temp = grid_9km_temp[:,0,:,:]
        grid_9km_uo = grid_9km_uo[:,0,:,:]
        grid_9km_vo = grid_9km_vo[:,0,:,:]

        # 
        cf.write(grid_9km_uo, '{0}/01_9km_regrid/grid_uo-{1}.nc'.format(base_folder, year))
        cf.write(grid_9km_vo, '{0}/01_9km_regrid/grid_vo-{1}.nc'.format(base_folder, year))
        cf.write(grid_9km_temp, '{0}/01_9km_regrid/grid_temp-{1}.nc'.format(base_folder, year))

        print('Memory: ', process.memory_info().rss / 1024 / 1024 ** 2)
        # Joining data
        print('Joining data for 9km grid...')
        nc_file_dst = '{0}/01_9km_regrid_joined/grid_{1}.nc'.format(base_folder, year)
        nc_file_uo = '{0}/01_9km_regrid/grid_uo-{1}.nc'.format(base_folder, year)
        toinclude = ["time","depth","latitude","longitude","uo"]
        rewriteNetCDF(nc_file_uo, nc_file_dst, toinclude)
        del nc_file_uo

        nc_file_vo = '{0}/01_9km_regrid/grid_vo-{1}.nc'.format(base_folder, year)
        toinclude = ["vo"]
        rewriteNetCDF(nc_file_vo, nc_file_dst, toinclude)
        del nc_file_vo
        
        nc_file_temp = '{0}/01_9km_regrid/grid_temp-{1}.nc'.format(base_folder, year)
        toinclude = ["thetao"]
        rewriteNetCDF(nc_file_temp, nc_file_dst, toinclude)
        del nc_file_temp

        del nc_file_dst

        print('Memory: ', process.memory_info().rss / 1024 / 1024 ** 2)

        # Define the output grid
        print('Defining output grid of 3km')
        lat = cf.DimensionCoordinate(data=cf.Data(np.arange(new_lat[0], new_lat[1], base_step/3), 'degreesN'))
        lon = cf.DimensionCoordinate(data=cf.Data(np.arange(new_long[0], new_long[1], base_step/3), 'degreesE'))
        # Regrid the field
        print('Regriding 9km to 3km for uo...')
        grid_3km_uo = grid_9km_uo.regrids({'latitude': lat, 'longitude': lon}, method='linear')
        # print('Writing nc file for regrided 3km uo...')
        cf.write(grid_3km_uo, '{0}/02_3km_regrid/grid_uo-{1}.nc'.format(base_folder, year))
        
        del grid_9km_uo
        print('Memory: ', process.memory_info().rss / 1024 / 1024 ** 2)

        print('Regriding 9km to 3km for vo...')
        grid_3km_vo = grid_9km_vo.regrids({'latitude': lat, 'longitude': lon}, method='linear')
        # print('Writing nc file for regrided 3km vo...')
        cf.write(grid_3km_vo, '{0}/02_3km_regrid/grid_vo-{1}.nc'.format(base_folder, year))

        del grid_9km_vo
        print('Memory: ', process.memory_info().rss / 1024 / 1024 ** 2)

        print('Regriding 9km to 3km for temp...')
        grid_3km_temp = grid_9km_temp.regrids({'latitude': lat, 'longitude': lon}, method='linear')
        # print('Writing nc file for regrided 3km temp...')
        cf.write(grid_3km_temp, '{0}/02_3km_regrid/grid_temp-{1}.nc'.format(base_folder, year))

        del grid_9km_temp
        print('Memory: ', process.memory_info().rss / 1024 / 1024 ** 2)

        # Joining data
        print('Joining data for 3km grid...')
        nc_file_dst = '{0}/02_3km_regrid_joined/grid_{1}.nc'.format(base_folder, year)
        nc_file_uo = '{0}/02_3km_regrid/grid_uo-{1}.nc'.format(base_folder, year)
        toinclude = ["time","depth","latitude","longitude","uo"]
        rewriteNetCDF(nc_file_uo, nc_file_dst, toinclude)
        del nc_file_uo

        nc_file_vo = '{0}/02_3km_regrid/grid_vo-{1}.nc'.format(base_folder, year)
        toinclude = ["vo"]
        rewriteNetCDF(nc_file_vo, nc_file_dst, toinclude)
        del nc_file_vo
        
        nc_file_temp = '{0}/02_3km_regrid/grid_temp-{1}.nc'.format(base_folder, year)
        toinclude = ["thetao"]
        rewriteNetCDF(nc_file_temp, nc_file_dst, toinclude)
        del nc_file_temp

        del nc_file_dst

        print('Memory: ', process.memory_info().rss / 1024 / 1024 ** 2)

        # Define the output grid
        print('Defining output grid of 1km')
        lat = cf.DimensionCoordinate(data=cf.Data(np.arange(new_lat[0], new_lat[1], base_step/9), 'degreesN'))
        lon = cf.DimensionCoordinate(data=cf.Data(np.arange(new_long[0], new_long[1], base_step/9), 'degreesE'))
        # Regrid the field
        print('Regriding 3km to 1km for uo...')
        grid_1km_uo = grid_3km_uo.regrids({'latitude': lat, 'longitude': lon}, method='linear')
        # print('Writing nc file for regrided 1km uo...')
        cf.write(grid_1km_uo, '{0}/03_1km_regrid/grid_uo-{1}.nc'.format(base_folder, year))

        del grid_3km_uo
        print('Memory: ', process.memory_info().rss / 1024 / 1024 ** 2)

        print('Regriding 3km to 1km for vo...')
        grid_1km_vo = grid_3km_vo.regrids({'latitude': lat, 'longitude': lon}, method='linear')
        # print('Writing nc file for regrided 1km vo...')
        cf.write(grid_1km_vo, '{0}/03_1km_regrid/grid_vo-{1}.nc'.format(base_folder, year))

        del grid_3km_vo
        print('Memory: ', process.memory_info().rss / 1024 / 1024 ** 2)

        print('Regriding 3km to 1km for temp...')
        grid_1km_temp = grid_3km_temp.regrids({'latitude': lat, 'longitude': lon}, method='linear')
        # print('Writing nc file for regrided 1km temp...')
        cf.write(grid_1km_temp, '{0}/03_1km_regrid/grid_temp-{1}.nc'.format(base_folder, year))

        del grid_3km_temp
        print('Memory: ', process.memory_info().rss / 1024 / 1024 ** 2)

        # Joining data
        print('Joining data for 1km grid...')
        nc_file_dst = '{0}/03_1km_regrid_joined/grid_{1}.nc'.format(base_folder, year)
        nc_file_uo = '{0}/03_1km_regrid/grid_uo-{1}.nc'.format(base_folder, year)
        toinclude = ["time","depth","latitude","longitude","uo"]
        rewriteNetCDF(nc_file_uo, nc_file_dst, toinclude)
        del nc_file_uo

        nc_file_vo = '{0}/03_1km_regrid/grid_vo-{1}.nc'.format(base_folder, year)
        toinclude = ["vo"]
        rewriteNetCDF(nc_file_vo, nc_file_dst, toinclude)
        del nc_file_vo
        
        nc_file_temp = '{0}/03_1km_regrid/grid_temp-{1}.nc'.format(base_folder, year)
        toinclude = ["thetao"]
        rewriteNetCDF(nc_file_temp, nc_file_dst, toinclude)
        del nc_file_temp

        del nc_file_dst

        print('Memory: ', process.memory_info().rss / 1024 / 1024 ** 2)

        # # Define the output grid
        # print('Defining output grid of 500m')
        # lat = cf.DimensionCoordinate(data=cf.Data(np.arange(new_lat[0], new_lat[1], base_step/18), 'degreesN'))
        # lon = cf.DimensionCoordinate(data=cf.Data(np.arange(new_long[0], new_long[1], base_step/18), 'degreesE'))
        # # Regrid the field
        # print('Regriding 1km to 500m for uo...')
        # grid_500m_uo = grid_1km_uo.regrids({'latitude': lat, 'longitude': lon}, method='linear')
        # print('Writing nc file for regrided 500m uo...')
        # cf.write(grid_500m_uo, '{0}/04_500m_regrid/grid_uo-{1}.nc'.format(base_folder, year))

        # del grid_1km_uo
        # del grid_500m_uo
        # print('Memory: ', process.memory_info().rss / 1024 / 1024 ** 2)

        # print('Regriding 1km to 500m for vo...')
        # grid_500m_vo = grid_1km_vo.regrids({'latitude': lat, 'longitude': lon}, method='linear')
        # print('Writing nc file for regrided 500m vo...')
        # cf.write(grid_500m_vo, '{0}/04_500m_regrid/grid_vo-{1}.nc'.format(base_folder, year))

        # del grid_1km_vo
        # del grid_500m_vo
        # print('Memory: ', process.memory_info().rss / 1024 / 1024 ** 2)

        # print('Regriding 1km to 500m for temp...')
        # grid_500m_temp = grid_1km_temp.regrids({'latitude': lat, 'longitude': lon}, method='linear')
        # print('Writing nc file for regrided 500m temp...')
        # cf.write(grid_500m_temp, '{0}/04_500m_regrid/grid_temp-{1}.nc'.format(base_folder, year))
        
        # del grid_1km_temp
        # del grid_500m_temp
        # print('Memory: ', process.memory_info().rss / 1024 / 1024 ** 2)

        # # Joining data
        # print('Joining data for 500m grid...')
        # nc_file_dst = '{0}/05_500m_regrid_joined/grid_{1}.nc'.format(base_folder, year)
        # nc_file_uo = '{0}/04_500m_regrid/grid_uo-{1}.nc'.format(base_folder, year)
        # toinclude = ["time","depth","latitude","longitude","uo"]
        # rewriteNetCDF(nc_file_uo, nc_file_dst, toinclude)
        # del nc_file_uo

        # nc_file_vo = '{0}/04_500m_regrid/grid_vo-{1}.nc'.format(base_folder, year)
        # toinclude = ["vo"]
        # rewriteNetCDF(nc_file_vo, nc_file_dst, toinclude)
        # del nc_file_vo
        
        # nc_file_temp = '{0}/04_500m_regrid/grid_temp-{1}.nc'.format(base_folder, year)
        # toinclude = ["thetao"]
        # rewriteNetCDF(nc_file_temp, nc_file_dst, toinclude)
        # del nc_file_temp

        # del nc_file_dst

        print('Memory: ', process.memory_info().rss / 1024 / 1024 ** 2)
        gc.collect()
        print('Memory at garbage: ', process.memory_info().rss / 1024 / 1024 ** 2)

def rewriteNetCDF(nc_file_src, nc_file_dst, toinclude=[]):
    try:
        dst = Dataset(nc_file_dst, "r+")
    except:
        dst = Dataset(nc_file_dst, "w")

    with Dataset(nc_file_src) as src, dst:
        print(src.dimensions)
        # copy attributes
        for name in src.ncattrs():
            if name in toinclude:
                dst.setncattr(name, src.getncattr(name))
        # copy dimensions
        for name, dimension in src.dimensions.items():
            if name in toinclude:
                dst.createDimension(name, len(dimension))
        # copy all file data except for the excluded
        for name, variable in src.variables.items():
            if name in toinclude:
                x = dst.createVariable(name, variable.datatype, variable.dimensions)
                # Copy variable attributes
                x.setncatts({k: variable.getncattr(k) for k in variable.ncattrs()})
                dst.variables[name][:] = src.variables[name][:]

if __name__ == '__main__':
    main(sys.argv[0:])