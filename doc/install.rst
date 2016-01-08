Setup/Install
-------------

Code is in //depot/software/bioinformatics/tools/pbreports

Recommended installation using a virtualenv:

First, make sure $SEYMOUR_HOME is set to whatever build you will be using, then follow these instructions:

.. code-block:: bash

    $> source $SEYMOUR_HOME/etc/setup.sh
    $> my_venv=$HOME/venvs/siv
    $> python virtualenv.py --python=$SEYMOUR_HOME/redist/python2.7/bin/python $my_venv
    $> source $my_venv/bin/activate
    $> cd pbreports
    $> pip install -r REQUIREMENTS.txt # or -r REQUIREMENTS_DEV.txt
    $> make install

Alternate installation:

One can also install Pysiv and it's dependencies directly in to their own personal build:

.. code-block:: bash

    $> source $SEYMOUR_HOME/etc/setup.sh
    $> easy_install pip
    $> cd Pysiv
    $> pip install -r REQUIREMENTS.txt
    $> make install # python setup.py develop


Running the unittests is useful to ensure you've installed the library correctly and that the code is working.
Because the test data files are large, they have not been checked into p4. pbreports/tests/nose.cfg contains
a data root entry that points to: /opt/testdata/pbreports-unittest/data. Be sure your tests can
see this dir, or copy the data somewhere and change nose.cfg

.. code-block:: bash

    $> cd pbreports
    $> make test

    (snip...)
    ----------------------------------------------------------------------
	Ran 41 tests in 54.357s
	
	OK
	cram tests/cram/*.t
	..
	# Ran 2 tests, 0 skipped, 0 failed.



