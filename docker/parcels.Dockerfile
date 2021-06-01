# FROM continuumio/anaconda3
FROM continuumio/miniconda3

RUN apt-get update && apt-get install -y libgtk2.0-dev libgeos-dev imagemagick libproj-dev && \
    rm -rf /var/lib/apt/lists/*

RUN /opt/conda/bin/conda update -n base -c defaults conda
RUN /opt/conda/bin/conda install python=3.7
RUN /opt/conda/bin/conda install anaconda-client
RUN /opt/conda/bin/conda install jupyter -y
# RUN /opt/conda/bin/conda install --channel https://conda.anaconda.org/menpo opencv3 -y
RUN /opt/conda/bin/conda install -c conda-forge opencv -y
#RUN /opt/conda/bin/conda install numpy pandas scikit-learn matplotlib seaborn pyyaml h5py keras -y
# RUN /opt/conda/bin/conda upgrade dask
#RUN pip install tensorflow imutils

# Install NCL for shapefile conversion
RUN /opt/conda/bin/conda install -c conda-forge ncl
# Install parcels
RUN /opt/conda/bin/conda install -c conda-forge parcels cartopy ffmpeg
RUN /opt/conda/bin/conda install -c conda-forge geopandas

# Install basemap
RUN pip install https://github.com/matplotlib/basemap/archive/master.zip

# Install other libs
RUN pip install geopandas
RUN pip install --upgrade matplotlib
RUN pip install descartes
RUN pip install rioxarray

# Install IPyNCL kernel for NCAR command line
RUN git clone https://github.com/suvarchal/IPyNCL.git /home/IPyNCL
RUN cd /home/IPyNCL && python setup.py install

# Install OpenDrift
RUN /opt/conda/bin/conda config --add channels conda-forge
# RUN /opt/conda/bin/conda install -c opendrift -c conda-forge -c noaa-orr-erd opendrift=1.4.2 xarray
RUN /opt/conda/bin/conda install -c opendrift -c conda-forge -c noaa-orr-erd opendrift=1.6.0 xarray

# Update OpenDrift
# RUN git clone https://github.com/OpenDrift/opendrift.git /home/opendrift
# RUN cd /home/opendrift && pip install -e .
# ENV PYTHONPATH "${PYTHONPATH}:/home/opendrift"

# Jupyter and Tensorboard ports
RUN ["mkdir", "notebooks"]
COPY .jupyter /root/.jupyter
COPY run_jupyter.sh /
EXPOSE 8888 6006

# Store notebooks in this mounted directory
VOLUME /notebooks

CMD ["/run_jupyter.sh"]