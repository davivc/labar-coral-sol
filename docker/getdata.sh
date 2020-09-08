#!/bin/bash

# Get data from Copernicus
# https://resources.marine.copernicus.eu/?option=com_csw&view=order&record_id=c0635fc4-07d3-4309-9d55-cfd3e6aa788b
for i in {1993..2018}
do
    echo "Retrieving data for ${i}..."
    python -m motuclient \
        --motu='http://my.cmems-du.eu/motu-web/Motu' \
        --service-id=GLOBAL_REANALYSIS_PHY_001_030-TDS \
        --product-id=global-reanalysis-phy-001-030-daily \
        --longitude-min=-49 \
        --longitude-max=-48 \
        --latitude-min=-28 \
        --latitude-max=-27 \
        --date-min="${i}-01-01 12:00:00" \
        --date-max="${i}-12-31 12:00:00" \
        --depth-min=0.493 \
        --depth-max=21.599 \
        --variable=thetao \
        --variable=uo \
        --variable=vo \
        --variable=zos \
        --out-dir="/code/data" \
        --out-name="global-reanalysis-phy-001-030-daily-${i}.nc" \
        --user="${MOTU_USER}" \
        --pwd="${MOTU_PWD}"
done