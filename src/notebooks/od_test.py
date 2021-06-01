import numpy as np

from datetime import timedelta
from datetime import datetime
from pprint import pprint

from opendrift.models.oceandrift import OceanDrift
from opendrift.models.oceandrift import Lagrangian3DArray
from opendrift.readers import reader_netCDF_CF_generic
from opendrift.readers import reader_global_landmask
from opendrift.readers import reader_shape

data = reader_netCDF_CF_generic.Reader('/data/global-reanalysis-phy-001-030-daily/05_500m_regrid_joined/grid_201*.nc')
# data2 = reader_netCDF_CF_generic.Reader('/data/global-reanalysis-phy-001-030-daily/05_500m_regrid_joined/grid_1994.nc')
reader_costao = reader_shape.Reader.from_shpfiles('/data/shapefiles/costoes/pol_diferenca_costao_terra.shp')
# reader_gshhs = reader_shape.Reader.from_shpfiles('/data/shapefiles/gshhs/GSHHS_shp/h/GSHHS_h_L1.shp')
reader_landmask = reader_global_landmask.Reader(extent=[-49, -28, 48, -26])  # lonmin, latmin, lonmax, latmax

import traceback
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt
import cartopy.feature as cfeature

import shapely
from shapely.geometry import box

import pyproj


# Defining the larvae element properties
class CoralLarvae(Lagrangian3DArray):
    """Extending LagrangianArray for elements moving in 3 dimensions
    The Particle may be buoyant and/or subject to vertical mixing
    buoyant bahaviour is described by terminal velocity
    """

    variables = Lagrangian3DArray.add_variables([
        ('objectType', {'dtype': np.int16,
                        'units': '1',
                        'seed': False,
                        'default': 0}),
        ('predationProbability', {'dtype': np.float32,
                             'units': '1/h',
            'description': 'Probability per hour that a larvae may be predated',
                             'default': 0.1}),
        ('deathProbability', {'dtype': np.float32,
                             'units': '1/h',
            'description': 'Probability per hour that a larvae may die by a random reason',
                             'default': 0.1}),
        ('jibeProbability', {'dtype': np.float32,
                             'units': '1/h',
            'description': 'Probability per hour that a larvae may change orientation (jibing)',
                             'default': 0.1}),
    ])
    

class CoralSol(OceanDrift):
    
    ElementType = CoralLarvae

    max_speed = 0.5  # m/s
    
    required_variables = {
        'x_sea_water_velocity': {'fallback': 0},
        'y_sea_water_velocity': {'fallback': 0},
        'sea_water_temperature': {'fallback': 19},
        'land_binary_mask': {'fallback': None},
    }
    
    # The depth range (in m) which profiles shall cover
    required_profiles_z_range = [-20, 0]
    
    # Default colors for plotting
    status_colors = {
        'initial': 'green',
        'active': 'blue',
        'died': 'red',
        'eaten': 'yellow',
        'died_temp': 'magenta',
        'settled': 'black'
    }

    def __init__(self, *args, **kwargs):

        # Calling general constructor of parent class
        super(CoralSol, self).__init__(*args, **kwargs)
        
        # By default, larvae do not strand towards coastline
        self.set_config('general:coastline_action', 'none')
        self.set_config('seed:ocean_only', True)

        # Vertical mixing is disabled by default
        self.set_config('drift:vertical_mixing', False)
        self.set_config('drift:vertical_advection', False)
        
#         self.priority_list['land_binary_mask'] = ['shape', 'global_landmask']
        
    def interact_with_rockyreef(self, final=False):
        if self.num_elements_active() == 0:
            return
        
        self.deactivate_elements(self.environment.land_binary_mask == 1, reason='settled')
        
#         self.deactivate_elements(self.environment.land_binary_mask == 1, reason='died')

    def get_map_background_vector(self, ax, background, time=None):
        # Get background field for plotting on map or animation
        # TODO: this method should be made more robust
        if type(background) is list:
            variable = background[0]  # A vector is requested
        else:
            variable = background  # A scalar is requested
            
        import pdb;pdb.set_trace()
        for readerName in self.readers:
            reader = self.readers[readerName]
            if variable in reader.variables:
                if time is None:
                    break
                if (time>= reader.start_time and time <= reader.end_time):
                    break
                if (reader.always_valid is True):
                    break
                    
        if time is None:
            if hasattr(self, 'elements_scheduled_time'):
                # Using time of first seeded element
                time = self.elements_scheduled_time[0]

        # Get reader coordinates covering given map area
        axisproj = pyproj.Proj(ax.projection.proj4_params)
        xmin, xmax, ymin, ymax = ax.get_extent(ccrs.PlateCarree())
        cornerlons = np.array([xmin, xmin, xmax, xmax])
        cornerlats = np.array([ymin, ymax, ymin, ymax])
        reader_x, reader_y = reader.lonlat2xy(cornerlons, cornerlats)
        if sum(~np.isfinite(reader_x+reader_y)) > 0:
            # Axis corner points are not within reader domain
            reader_x = np.array([reader.xmin, reader.xmax])
            reader_y = np.array([reader.ymin, reader.ymax])
        else:
            reader_x = np.linspace(reader_x.min(), reader_x.max(), 10)
            reader_y = np.linspace(reader_y.min(), reader_y.max(), 10)

        data = reader.get_variables(
            background, time, reader_x, reader_y, None)
        reader_x, reader_y = np.meshgrid(data['x'], data['y'])
        if type(background) is list:
            u_component = data[background[0]]
            v_component = data[background[1]]
            with np.errstate(invalid='ignore'):
                scalar = np.sqrt(u_component**2 + v_component**2)
            # NB: rotation not completed!
            u_component, v_component = reader.rotate_vectors(
                reader_x, reader_y, u_component, v_component,
                reader.proj, ccrs.PlateCarree(
                globe=ccrs.Globe(datum='WGS84', ellipse='WGS84')
                ).proj4_init)
        else:
            scalar = data[background]
            u_component = v_component = None

        # Shift one pixel for correct plotting
        reader_x = reader_x - reader.delta_x
        reader_y = reader_y - reader.delta_y
        if reader.projected is False:
            reader_y[reader_y<0] = 0
            reader_x[reader_x<0] = 0

        rlons, rlats = reader.xy2lonlat(reader_x, reader_y)
        if rlons.max() > 360:
            rlons = rlons - 360
        map_x, map_y = (rlons, rlats)

        scalar = np.ma.masked_invalid(scalar)
        if reader.convolve is not None:
            from scipy import ndimage
            N = reader.convolve
            if isinstance(N, (int, np.integer)):
                kernel = np.ones((N, N))
                kernel = kernel/kernel.sum()
            else:
                kernel = N
            self.logger.debug('Convolving variables with kernel: %s' % kernel)
            scalar = ndimage.convolve(
                scalar, kernel, mode='nearest')

        return map_x, map_y, scalar, u_component, v_component
     
    
    def update(self):
        """Update positions and properties of elements."""
        
        # Turbulent Mixing
        self.vertical_mixing()

        # Simply move particles with ambient current
        self.advect_ocean_current()
        
        # Vertical advection
        if self.get_config('drift:vertical_advection') is True:
            self.vertical_advection()
            
        # Simply move particles with ambient current
#         self.interact_with_rockyreef()

    def plot_costoes(self, background=None, buffer=.2, corners=None, linecolor=None, filename=None,
             show=True, vmin=None, vmax=None, compare=None, cmap='jet',
             lvmin=None, lvmax=None, skip=2, scale=10, show_scalar=True,
             contourlines=False, trajectory_dict=None, colorbar=True,
             linewidth=1, lcs=None, show_particles=True, show_initial=True,
             density_pixelsize_m=1000,
             surface_color=None, submerged_color=None, markersize=20,
             title='auto', legend=True, legend_loc='best', lscale=None,
             fast=False, hide_landmask=False, **kwargs):
        """Basic built-in plotting function intended for developing/debugging.
        Plots trajectories of all particles.
        Positions marked with colored stars:
        - green: all start positions
        - red: deactivated particles
        - blue: particles still active at end of simulation
        Requires availability of Cartopy.
        Arguments:
            background: string, name of variable (standard_name) which will
                be plotted as background of trajectories, provided that it
                can be read with one of the available readers.
            buffer: float; spatial buffer of plot in degrees of
                longitude/latitude around particle collection.
            background: name of variable to be plotted as background field.
            Use two element list for vector fields, e.g. ['x_wind', 'y_wind']
            vmin, vmax: minimum and maximum values for colors of background.
            linecolor: name of variable to be used for coloring trajectories, or matplotlib color string.
            lvmin, lvmax: minimum and maximum values for colors of trajectories.
            lscale (string): resolution of land feature ('c', 'l', 'i', 'h', 'f', 'auto'). default is 'auto'.
            fast (bool): use some optimizations to speed up plotting at the cost of accuracy
            :param hide_landmask: do not plot landmask (default False). See :ref:`model_landmask_only_model` for example usage.
            :type hide_landmask: bool
        """

        if self.num_elements_total() == 0:
            raise ValueError('Please run simulation before plotting')

        start_time = datetime.now()

        # x, y are longitude, latitude -> i.e. in a PlateCarree CRS
        gcrs = ccrs.PlateCarree()
#         fig, ax, crs, x, y, index_of_first, index_of_last = \
#             self.set_up_map(buffer=buffer, corners=corners, lscale=lscale, fast=fast, hide_landmask=hide_landmask, **kwargs)

        mappable = None
        
        fig = plt.figure(figsize=[11,11])
        ax = fig.add_subplot(1, 1, 1)  # specify (nrows, ncols, axnum)
        
        fig.canvas.draw()
        fig.set_tight_layout(True)
        
        request = cimgt.OSM()
        ax = plt.axes(projection=request.crs)
        ax.set_extent(corners, crs=gcrs)
        
#         landmask = self.readers['global_landmask'].mask
#         extent = box(corners[0], corners[2], corners[1], corners[3])
#         extent = shapely.prepared.prep(extent)
#         polys = [p for p in landmask.polys.geoms if extent.intersects(p)]
#         ax.add_geometries(polys,
#             ccrs.PlateCarree(),
#             facecolor=cfeature.COLORS['land'],
#             edgecolor='black')
        
#         ax.add_image(request, 11, alpha=0.75)
        
#         f = cfeature.GSHHSFeature(scale='h', levels=[1], facecolor=cfeature.COLORS['land'])
#         ax.add_geometries(
#                 f.intersecting_geometries(corners),
#                 gcrs,
#                 facecolor=cfeature.COLORS['land'],
#                 edgecolor='black')
#         ax.add_geometries(
#             self.readers['global_landmask'].polys, 
#             gcrs, 
#             facecolor=cfeature.COLORS['land'],
#             edgecolor='black',
#             alpha=0.75
#         )
    
        ax.add_geometries(
            self.readers['shape'].polys, 
            gcrs, 
            facecolor='blue', 
            edgecolor='blue',
            alpha=0.75
        )
        
        ax.add_image(request, 10, alpha=0.50)
        
        if background is not None:
            map_x, map_y, scalar, u_component, v_component = \
                self.get_map_background(ax, background, time=self.start_time)
            ax.quiver(
                map_x[::skip, ::skip],
                map_y[::skip, ::skip],
                u_component[::skip, ::skip],
                v_component[::skip, ::skip], scale=scale, transform = gcrs
            )
        
        lons = self.history['lon']
        lats = self.history['lat']
        
        if not hasattr(self, 'ds'):
            try:
                firstlast = np.ma.notmasked_edges(lons, axis=1)
                index_of_first = firstlast[0][1]
                index_of_last = firstlast[1][1]
            except:
                index_of_last = 0
        else:
            index_of_first = None
            index_of_last = None
        
        x = lons.T
        y = lats.T
        
        markercolor = self.plot_comparison_colors[0]
        
        # The more elements, the more transparent we make the lines
        min_alpha = 0.1
        max_elements = 5000.0
        alpha = min_alpha**(2*(self.num_elements_total()-1)/(max_elements-1))
        alpha = np.max((min_alpha, alpha))
        if legend is False:
            legend = None
        if hasattr(self, 'history') and linewidth != 0:
            # Plot trajectories
            from matplotlib.colors import is_color_like
            if linecolor is None or is_color_like(linecolor) is True:
                if is_color_like(linecolor):
                    linecolor = linecolor
                else:
                    linecolor = 'gray'
                if compare is not None and legend is not None:
                    if legend is True:
                        if hasattr(compare, 'len'):
                            numleg = len(compare)
                        else:
                            numleg = 2
                        legend = ['Simulation %d' % (i+1) for i in
                                  range(numleg)]
                    ax.plot(x[:,0], y[:,0], color=linecolor, alpha=alpha, label=legend[0], linewidth=linewidth, transform = gcrs)
                    ax.plot(x, y, color=linecolor, alpha=alpha, label='_nolegend_', linewidth=linewidth, transform = gcrs)
                else:
                    ax.plot(x, y, color=linecolor, alpha=alpha, linewidth=linewidth, transform = gcrs)
            else:
                colorbar = True
                # Color lines according to given parameter
                try:
                    if isinstance(linecolor, str):
                        param = self.history[linecolor]
                    else:
                        param = linecolor
                except:
                    raise ValueError(
                        'Available parameters to be used for linecolors: ' +
                        str(self.history.dtype.fields))
                from matplotlib.collections import LineCollection
                for i in range(x.shape[1]):
                    vind = np.arange(index_of_first[i], index_of_last[i] + 1)
                    points = np.array(
                        [x[vind, i].T, y[vind, i].T]).T.reshape(-1, 1, 2)
                    segments = np.concatenate([points[:-1], points[1:]],
                                              axis=1)
                    if lvmin is None:
                        lvmin = param.min()
                        lvmax = param.max()
                    lc = LineCollection(segments,
                                        #cmap=plt.get_cmap('Spectral'),
                                        cmap=cmap,
                                        norm=plt.Normalize(lvmin, lvmax), transform = gcrs)
                    #lc.set_linewidth(3)
                    lc.set_array(param.T[vind, i])
                    mappable = ax.add_collection(lc)
            
        label_initial = None
        label_active = None
        color_initial = 'gray'
        color_active = 'gray'
        if show_particles is True:
            if show_initial is True:
                ax.scatter(x[index_of_first, range(x.shape[1])],
                       y[index_of_first, range(x.shape[1])],
                       s=markersize,
                       zorder=10, edgecolor=markercolor, linewidths=.2,
                       c=color_initial, label=label_initial,
                       transform = gcrs)
            if surface_color is not None:
                color_active = surface_color
                label_active = 'surface'
            ax.scatter(x[index_of_last, range(x.shape[1])],
                       y[index_of_last, range(x.shape[1])],
                       s=markersize, zorder=3,
                       edgecolor=markercolor, linewidths=.2,
                       c=color_active, label=label_active,
                       transform = gcrs)

            x_deactivated, y_deactivated = (self.elements_deactivated.lon,
                                               self.elements_deactivated.lat)
            # Plot deactivated elements, labeled by deactivation reason
            for statusnum, status in enumerate(self.status_categories):
                if status == 'active':
                    continue  # plotted above
                if status not in self.status_colors:
                    # If no color specified, pick an unused one
                    for color in ['red', 'blue', 'green', 'black', 'gray',
                                  'cyan', 'DarkSeaGreen', 'brown']:
                        if color not in self.status_colors.values():
                            self.status_colors[status] = color
                            break
                indices = np.where(self.elements_deactivated.status == statusnum)
                if len(indices[0]) > 0:
                    if (status == 'seeded_on_land' or
                        status == 'seeded_at_nodata_position'):
                        zorder = 11
                    else:
                        zorder = 3
                    if compare is not None:
                        legstr = None
                    else:
                        legstr = '%s (%i)' % (status, len(indices[0]))
                    if compare is None:
                        color_status = self.status_colors[status]
                    else:
                        color_status = 'gray'
                    ax.scatter(x_deactivated[indices], y_deactivated[indices],
                                s=markersize,
                                zorder=zorder, edgecolor=markercolor, linewidths=.1,
                                c=color_status, label=legstr,
                                transform = gcrs)

        try:
            if legend is not None:# and compare is None:
                plt.legend(loc=legend_loc, markerscale=2)
        except Exception as e:
            self.logger.warning('Cannot plot legend, due to bug in matplotlib:')
            self.logger.warning(traceback.format_exc())


        if mappable is not None:
            cb = fig.colorbar(mappable, orientation='horizontal', pad=.05, aspect=30, shrink=.8)
            # TODO: need better control of colorbar content
            if background is not None:
                cb.set_label(str(background))
            if linecolor is not None:
                cb.set_label(str(linecolor))

        if type(background) is list:
            delta_x = (map_x[1,2] - map_x[1,1])/2.
            delta_y = (map_y[2,1] - map_y[1,1])/2.
            ax.quiver(map_x[::skip, ::skip] + delta_x, map_y[::skip, ::skip] + delta_y,
                      u_component[::skip, ::skip],
                      v_component[::skip, ::skip], scale=scale, transform = gcrs)

        if title is not None:
            if title == 'auto':
                if hasattr(self, 'time'):
                    plt.title('%s\n%s to %s UTC (%i steps)' % (
                              self._figure_title(),
                              self.start_time.strftime('%Y-%m-%d %H:%M'),
                              self.time.strftime('%Y-%m-%d %H:%M'),
                              self.steps_output))
                else:
                    plt.title('%s\n%i elements seeded at %s UTC' % (
                              self._figure_title(),
                              self.num_elements_scheduled(),
                              self.elements_scheduled_time[0].strftime(
                              '%Y-%m-%d %H:%M')))
            else:
                plt.title(title)

        if trajectory_dict is not None:
            self._plot_trajectory_dict(ax, trajectory_dict)
        plt.show()

o = CoralSol(loglevel=20)
# o.disable_vertical_motion()
# pprint(OceanDrift.required_variables)
# o.disable_vertical_motion()
o.add_reader([data, reader_costao])
# o.add_reader([data, reader_gshhs])

start = datetime(1993, 1, 1, 12, 0, 0)

# 2014;Rancho Norte (RN);-27.277.734;-48.374.985
# GPS corrected -48.381440; -27.277070
seed_rn = [-48.381440, -27.277070]
# 2012;Engenho (EG);-27.291.957;-48.367.384
seed_eg = [-48.367384, -27.291957]
# 2014;Vidal (SV);-27.297.548;-48.360.013
seed_sv = [-48.360013, -27.297548]
# 2013;Farol (SF);-27.296.645;-48.363.786
seed_sf = [-48.363786, -27.296645]
# 2015;Galé (GI);-2.717.785;-4.840.758
seed_gi = [-48.40758, -27.17785]

o.seed_elements(lon=seed_rn[0], lat=seed_rn[1], number=100, radius=10, time=[start, start+timedelta(hours=4)])
# o.seed_elements(lon=seed_eg[0], lat=seed_eg[1], number=100, radius=10, time=[start, start+timedelta(hours=4)])
# o.seed_elements(lon=seed_sv[0], lat=seed_sv[1], number=100, radius=10, time=[start, start+timedelta(hours=4)])
# o.seed_elements(lon=seed_sf[0], lat=seed_sf[1], number=100, radius=10, time=[start, start+timedelta(hours=4)])
# o.seed_elements(lon=seed_gi[0], lat=seed_gi[1], number=100, radius=10, time=[start, start+timedelta(hours=4)])
o.set_config('general:coastline_action', 'none')
o.set_config('general:use_auto_landmask', False)
# o.run(duration=timedelta(hours=288), time_step_output=3600, outfile= '/data/coral_sol_output.nc')
o.run(duration=timedelta(hours=54), time_step=450, time_step_output=3600)

domain = [-48.7, -48.2, -27.8, -27]
o.plot_costoes(corners=domain, linecolor='sea_water_temperature', background=['x_sea_water_velocity', 'y_sea_water_velocity'])