#!/bin/bash -ex

NX3PBASEURL=http://nexus/repository/unsupported/pitchfork/gcc-4.9.2
export PATH=$PWD/build/bin:/mnt/software/a/anaconda2/4.2.0/bin:$PATH
export PYTHONUSERBASE=$PWD/build
export CFLAGS="-I/mnt/software/a/anaconda2/4.2.0/include"
PIP="pip --cache-dir=$bamboo_build_working_directory/.pip"
type module >& /dev/null || . /mnt/software/Modules/current/init/bash
module load gcc/4.9.2
module load graphviz/2.28.0
rm -rf   build
mkdir -p build/bin build/lib build/include build/share
$PIP install --user \
  iso8601
$PIP install --user \
  $NX3PBASEURL/pythonpkgs/xmlbuilder-1.0-cp27-none-any.whl \
  $NX3PBASEURL/pythonpkgs/tabulate-0.7.5-cp27-none-any.whl \
  $NX3PBASEURL/pythonpkgs/pysam-0.9.1.4-cp27-cp27mu-linux_x86_64.whl \
  $NX3PBASEURL/pythonpkgs/avro-1.7.7-cp27-none-any.whl
ln -sfn ../data repos/PacBioTestData/pbtestdata/data
$PIP install --user -e repos/PacBioTestData
$PIP install --user -e repos/pbcommand
$PIP install --user -e repos/pbcore
$PIP install --user -r PB_REQUIREMENTS.txt
$PIP install --user -r REQUIREMENTS.txt
$PIP install --user -r REQUIREMENTS_DEV.txt
$PIP install --user -e ./
make test
