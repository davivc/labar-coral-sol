# FROM continuumio/anaconda3
FROM continuumio/miniconda3

RUN apt-get update && apt-get install -y libgtk2.0-dev libgeos-dev imagemagick libproj-dev && \
    rm -rf /var/lib/apt/lists/*

RUN conda init bash
RUN conda update -n base -c defaults conda
RUN conda install jupyter -y

# Install NCL for shapefile conversion
#RUN /opt/conda/bin/conda install -c conda-forge ncl

#RUN /opt/conda/bin/conda install -c conda-forge opencv -y
#RUN /opt/conda/bin/conda install numpy pandas scikit-learn matplotlib seaborn pyyaml h5py keras -y

# Install basemap
# RUN pip install https://github.com/matplotlib/basemap/archive/master.zip

# Install IPyNCL kernel for NCAR command line
# RUN git clone https://github.com/suvarchal/IPyNCL.git /home/IPyNCL
# RUN cd /home/IPyNCL && python setup.py install

WORKDIR /root

RUN git clone https://github.com/OpenDrift/opendrift.git

WORKDIR /root/opendrift

RUN conda config --add channels conda-forge
RUN conda env create -f environment.yml

# Make RUN commands use the new environment:
# https://pythonspeed.com/articles/activate-conda-dockerfile/
SHELL ["conda", "run", "-n", "opendrift", "/bin/bash", "-c"]

RUN pip install -e .

# Install libs
RUN conda install pandas
RUN conda install pyyaml
RUN conda install geopandas
RUN conda install nb_conda
RUN conda install ipykernel

RUN python -m ipykernel install --user --name=opendrift


RUN ["mkdir", "notebooks"]
COPY .jupyter /root/.jupyter
COPY run_jupyter.sh /

RUN apt-get update && apt-get install -y dos2unix
RUN dos2unix /run_jupyter.sh

EXPOSE 8888 6006

# Store notebooks in this mounted directory
VOLUME /notebooks

# CMD ["/run_jupyter.sh"]
ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "opendrift", "/run_jupyter.sh"]