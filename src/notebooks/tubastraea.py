import traceback

from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt
import cartopy.feature as cfeature

import shapely
from shapely.geometry import box

import pyproj

from opendrift.models.oceandrift import OceanDrift
from opendrift.models.oceandrift import Lagrangian3DArray
from opendrift.models.oceandrift import LagrangianArray

# Defining the larvae element properties
class CoralLarvae(LagrangianArray):
    """Extending LagrangianArray for elements moving in 3 dimensions
    The Particle may be buoyant and/or subject to vertical mixing
    buoyant bahaviour is described by terminal velocity
    """

    # variables = Lagrangian3DArray.add_variables([
    #     ('predation_probability', {
    #         'dtype': np.float32, 'units': '1/h', 'default': 0.1,
    #         'description': 'Probability per hour that a larvae may be predated'            
    #     }),
    #     ('death_probability', {
    #         'dtype': np.float32, 'units': '1/h', 'default': 0.1,
    #         'description': 'Probability per hour that a larvae may die by a random reason'
    #     }),
    #     ('jibe_probability', {
    #         'dtype': np.float32, 'units': '1/h', 'default': 0.04,
    #         'description': 'Probability per hour that a larvae may change orientation (jibing)'
    #     }),
    #     ('drag', {'dtype': np.float32, 'units': '1', 'default': 1,
    #         'description': 'Relationship between larvae velocity and current velocity (ie. 1 means that larvae moves in the same velocity as the ocean current)'
    #     }),
    # ])
    

class Tubastraea(OceanDrift):
    
    ElementType = CoralLarvae

    max_speed = 1  # m/s
      
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
        'initial': 'orange',
        'active': 'blue',
        'died': 'black',
        'probably_settled': 'yellow',
        'settled': 'green'
    }

    def __init__(self, *args, **kwargs):

        # Calling general constructor of parent class
        super(Tubastraea, self).__init__(*args, **kwargs)
        
        # By default, larvae do not strand towards coastline
        self.set_config('general:coastline_action', 'none')
        self.set_config('general:use_auto_landmask', True)
        self.set_config('seed:ocean_only', True)

        # Vertical mixing is disabled by default
        # self.set_config('drift:vertical_mixing', False)
        # self.set_config('drift:vertical_advection', False)

        # self.set_config({
        #     'seed:drag': {'type': 'float',
        #         'default': 0.04, 'min': 0, 'max': 1},
        #     })
        
    def get_reef_mask(self, shape_name='shape'):
        self.priority_list['land_binary_mask'] = [shape_name]
        en, en_prof, missing = \
            self.get_environment(['land_binary_mask'],
                                 self.time,
                                 self.elements.lon,
                                 self.elements.lat,
                                 self.elements.z,
                                 None)
#         self.environment['land_binary_mask_{0}'.format(shape_name)] = en.land_binary_mask
#         self.environment['land_binary_mask_{0}'.format(shape_name)] = en.land_binary_mask
        self.priority_list['land_binary_mask'] = ['global_landmask']
        return en
        
    def interact_with_reef(self, final=False):
        if not hasattr(self, 'environment') or not hasattr(self.environment, 'land_binary_mask'):
            print('Class does not have environment')
            return
        
        if self.num_elements_active() == 0:
            return
        
        for shape in self.reef_shapes:
            env = self.get_reef_mask(shape)
            self.deactivate_elements(env.land_binary_mask == 1, reason='settled')        
        
        land = self.get_reef_mask('global_landmask')
        self.deactivate_elements(land.land_binary_mask == 1, reason='died')     
    
    def update(self):
        """Update positions and properties of elements."""
        
        # Turbulent Mixing
        self.vertical_mixing()

        # Simply move particles with ambient current
        self.advect_ocean_current(self.factor)
        
#         # Give Random Movement to larvae
#         self.update_positions(self.environment.x_sea_water_velocity,
#                               self.environment.y_sea_water_velocity)
        
        # Vertical advection
        if self.get_config('drift:vertical_advection') is True:
            self.vertical_advection()
            
        # Simply move particles with ambient current
        self.interact_with_reef()

    def plot_reef(self, background=None, buffer=.2, corners=None, linecolor=None, filename=None,
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
        
        landmask = self.readers['global_landmask'].mask
        extent = box(corners[0], corners[2], corners[1], corners[3])
        extent = shapely.prepared.prep(extent)
        polys = [p for p in landmask.polys.geoms if extent.intersects(p)]
        ax.add_geometries(polys,
            ccrs.PlateCarree(),
            facecolor=cfeature.COLORS['land'],
            edgecolor='black',
            alpha=0.50
        )
        
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
            alpha=0.25
        )
        
        # ax.add_image(request, 10, alpha=0.50)
        
        if background is not None:
            map_x, map_y, scalar, u_component, v_component = \
                self.get_map_background_vector(ax, background, time=self.start_time)
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
        color_active = 'blue'
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
