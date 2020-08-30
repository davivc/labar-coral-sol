#!/bin/bash
# installing ESMF on Ubuntu Linux


CUSTOMINSTALLDIR=/opt/esmf/8.0.1

#------------------ installing the ESMF libraries ---------------
cd $HOME
wget https://github.com/esmf-org/esmf/archive/ESMF_8_0_1.tar.gz
tar -xf ESMF_8_0_1.tar.gz
ls -l
cd esmf-ESMF_8_0_1

export ESMF_DIR=$( pwd )
export ESMF_INSTALL_PREFIX=$CUSTOMINSTALLDIR
export ESMF_OS=Linux
export ESMF_NETCDF="local"
export ESMF_COMM=mpiuni
export ESMF_F90COMPILER=gfortran
export ESMF_CXXCOMPILER=g++
export ESMF_TESTEXHAUSTIVE=on
export ESMF_TESTSHAREDOBJ=on
export ESMF_NETCDF_INCLUDE=/usr/include
export ESMF_NETCDF_LIBS="-lnetcdf -lnetcdff"
export ESMF_NETCDF_LIBPATH=/usr/lib
export ESMF_BOPT=O3
# export ESMF_DIR=$( pwd )
# export ESMF_INSTALL_PREFIX=$CUSTOMINSTALLDIR
# export ESMF_COMM=openmpi
# export ESMF_NETCDF=split
# export ESMF_NETCDF_INCLUDE=/usr/include
# export ESMF_NETCDF_LIBPATH=/usr/lib
# export ESMF_NETCDF_LIBS="-lnetcdff -lnetcdf"

make all
make install
make installcheck

# At this point you should have ESMF installed
#------------------ installing the python3 wrapper ---------------

cd $( pwd )/src/addon/ESMPy/
python3 setup.py build --ESMFMKFILE=$CUSTOMINSTALLDIR/lib/libO3/Linux.gfortran.64.mpiuni.default/esmf.mk
python3 setup.py install

# cd ..
# git clone https://github.com/raphaeldussin/ESMPy3.git ESMPy3
# cd ESMPy3
# $PYTHONBIN/python setup.py build --ESMFMKFILE=$CUSTOMINSTALLDIR/lib/libO/Linux.gfortran.64.openmpi.default/esmf.mk install