#!/bin/bash

# Get data from Copernicus
# https://resources.marine.copernicus.eu/?option=com_csw&view=order&record_id=c0635fc4-07d3-4309-9d55-cfd3e6aa788b
for i in {1993..2018}
do
    echo "Retrieving data for ${i}..."
    python -m motuclient \
        --motu 'http://my.cmems-du.eu/motu-web/Motu' \
        --service-id GLOBAL_REANALYSIS_PHY_001_030-TDS \
        --product-id global-reanalysis-phy-001-030-daily \
        --longitude-min -49 \
        --longitude-max -45 \
        --latitude-min -30 \
        --latitude-max -25 \
        --date-min "${i}-01-01 00:00:00" \
        --date-max "${i}-12-31 00:00:00" \
        --depth-min 0.49402499198913574 \
        --depth-max 0.49402499198913574 \
        --variable thetao \
        --variable uo \
        --variable vo \
        --out-dir "/code/data" \
        --out-name "global-reanalysis-phy-001-030-daily-${i}.nc" \
        --user "${MOTU_USER}" \
        --pwd "${MOTU_PWD}"
done