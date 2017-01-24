#!/bin/bash -ex

mkdir -p tmp
/opt/python-2.7.9/bin/python /mnt/software/v/virtualenv/13.0.1/virtualenv.py tmp/venv
source tmp/venv/bin/activate

(cd repos/PacBioTestData && make python)
(cd repos/pbcommand && make install)
(cd .circleci && bash installHDF5.sh)
export HDF5_DIR=$PWD/.circleci/prefix
pip install -r PB_REQUIREMENTS.txt
(cd repos/pbcore && make install)
pip install -r REQUIREMENTS.txt
pip install -r REQUIREMENTS_DEV.txt

python setup.py install
# FIXME need to update "make test"
make test
