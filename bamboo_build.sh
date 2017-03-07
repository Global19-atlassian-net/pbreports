#!/bin/bash -ex

source /mnt/software/Modules/current/init/bash
module load hdf5-tools/1.8.16
module load python/2.7.9

mkdir -p tmp
python /mnt/software/v/virtualenv/13.0.1/virtualenv.py tmp/venv
source tmp/venv/bin/activate

(cd repos/PacBioTestData && make python)
(cd repos/pbcommand && make install)
pip install -r PB_REQUIREMENTS.txt
(cd repos/pbcore && make install)
pip install -r REQUIREMENTS.txt
pip install -r REQUIREMENTS_DEV.txt

python setup.py install
# FIXME need to update "make test"
make test
