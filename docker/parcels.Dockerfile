FROM continuumio/anaconda3

RUN apt-get update && apt-get install -y libgtk2.0-dev imagemagick  && \
    rm -rf /var/lib/apt/lists/*

RUN /opt/conda/bin/conda update -n base -c defaults conda
RUN /opt/conda/bin/conda install python=3.6
RUN /opt/conda/bin/conda install anaconda-client
RUN /opt/conda/bin/conda install jupyter -y
RUN /opt/conda/bin/conda install --channel https://conda.anaconda.org/menpo opencv3 -y
#RUN /opt/conda/bin/conda install numpy pandas scikit-learn matplotlib seaborn pyyaml h5py keras -y
RUN /opt/conda/bin/conda upgrade dask
#RUN pip install tensorflow imutils

RUN ["mkdir", "notebooks"]
COPY .jupyter /root/.jupyter
COPY run_jupyter.sh /

# Install parcels
RUN /opt/conda/bin/conda install -c conda-forge parcels cartopy ffmpeg

# Jupyter and Tensorboard ports
EXPOSE 8888 6006

# Store notebooks in this mounted directory
VOLUME /notebooks

CMD ["/run_jupyter.sh"]