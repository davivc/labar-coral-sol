# Paper Coral-sol - LABAR

## Pre-requisites

To run the following steps you must have Docker installed on your computer and clone the repository.

```
git clone git@github.com:davivc/labar-coral-sol.git
cd labar-coral-sol
```

## 1. Build the containers

To download images and build containers run this command. This step will take some time (maybe a couple hours)
```
docker-compose build
```

## 2. Download the data

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


## 3. Regridding
Run regrid to downscale NetCDF files. This step will regrid the nc files from ~9km to 3km, then 3km to 1km and finally will regrid 1km to 500m. It will take approximately 10 minutes on a pc with 16GB RAM.

```
docker-compose run --rm regridnetcdf regrid.py all
```

Or you can select one year only
```
docker-compose run --rm regridnetcdf regrid.py YEAR
```

## 4. Parcels

To see the parcels advection on action just fire up our stack
```
docker-compose up
```

After that go to the url shown in your terminal and navigate through the notebooks.

# Others

## Papers
[1] Engler R, Guisan A. MigClim: Predicting plant distribution and dispersal in a changing climate. Divers Distrib 2009;15:590–601. doi:10.1111/j.1472-4642.2009.00566.x.
