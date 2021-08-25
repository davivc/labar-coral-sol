# Paper Coral-sol - LABAR

## Pre-requisites

* Git
* Docker
* Some python knowledge and jupyter notebooks

Now clone the repository and follow the instructions.

```
git clone git@github.com:davivc/labar-coral-sol.git
cd labar-coral-sol
```

## 1. Services and containers

In this project we define 3 services for different tasks inside the `docker-compose.yml` file. Each task will run in its specific container.

* getdata: this service is responsible to download the netCDF files from https://resources.marine.copernicus.eu/. 
* regridnetcdf: this service is responsible to regrid the downloaded netCDF files to a smaller scale
* tubastraea_notebook: this service will hold the code and the jupyter notebooks for our model

*Warning*: To run the codes inside the notebook you must have the regrided netcdf files. So you must run the first 2 containers at least one time to fetch the data and regrid it. After that you can execute the notebook whenever you want.

## 2. Build the containers

To run the code we first need download images and build containers. This step will take some time (maybe a couple hours depending on your internet and RAM Memory)

This command will build all 3 containers
```
docker-compose build
```

You can also build each one at a time
```
docker-compose build getdata
```

```
docker-compose build regridnetcdf
```

```
docker-compose build tabastraea_notebook
```

## 3. Download the data

To retrieve the data first copy the file `.env-example` to `.env` and change the credentials for Copernicus. If you don't have and account you can create here at https://resources.marine.copernicus.eu/?option=com_sla. After that change the credentials in the `.env` file to your credentials

```
MOTU_USER=YOUR_USER
MOTU_PWD=YOUR_PASSWORD
```

With the credentials configured just execute and wait the script to finish downloading. It will take approximately 1 hour (depending your on connection).
```
docker-compose run --rm getdata
```
This command will retrieve nc data from 1993 to 2018 for the variables thetao, uo, vo and zos and depth between 0.493 and 21.599. However you can change the file `docker/getdata.sh` to retrieve different data. After the changes build the container again and execute the command above.


## 4. Regridding
Run regrid to downscale NetCDF files. This step will regrid the nc files from ~9km to 3km, then 3km to 1km and finally will regrid 1km to 500m. It will take approximately 10 minutes on a pc with 16GB RAM.

```
docker-compose run --rm regridnetcdf regrid.py
```

Or you can select one year only
```
docker-compose run --rm regridnetcdf regrid.py YEAR
```

## 5. Start the notebooks

```
docker-compose up tubastraea_notebook
```

After that go to the url shown in your terminal and navigate through the notebooks.

### Validation
To validate our regrid we will use data from PNBOIA at https://www.marinha.mil.br/chm/dados-do-pnboiaboias/boia-itajai

DMS: Lat 27°24,35'S / Lon 047°15,93'W
DD: Lat 27.4° / Lon 47.2655°

### Parcels
To see the parcels advection on action just fire up our stack

# Others

## Papers
[1] Engler R, Guisan A. MigClim: Predicting plant distribution and dispersal in a changing climate. Divers Distrib 2009;15:590–601. doi:10.1111/j.1472-4642.2009.00566.x.


## Platform offshore
-26.767222 -46.767264


## Uncertaintity
Incorporar desvio padrão da validação
Esquecer função da temperatura
Assentar protegido cor vermelha
Assentar exposto cor amarela
Validação
Preditivo

Taxa de mortalidade progressiva