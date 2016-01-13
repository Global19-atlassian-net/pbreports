.PHONY: all clean install dev-install test
SHELL = /bin/bash -e


install:
	@which pip > /dev/null
	@pip freeze|grep 'pbreports=='>/dev/null \
      && pip uninstall -y pbreports \
      || echo -n ''
	@pip install ./
	@echo "Installed version pbreports $(shell pbreports --version)"


dev-install:
	python setup.py develop

clean:
	rm -rf build/;\
	find . -name "*.egg-info" | xargs rm -rf;\
	find . -name "*.pyc" | xargs rm -f;\
	find . -name "*.err" | xargs rm -f;\
	find . -name "*.log" | grep -v amplicon_analysis | xargs rm -f;\
	rm -rf dist/

test:
	nosetests --nocapture --nologcapture --verbose tests/unit/test*.py

pip-install:
	@which pip > /dev/null
	@pip freeze|grep 'pbreports=='>/dev/null \
      && pip uninstall -y pbreports \
      || true
	@pip install --no-index \
          --install-option="--install-scripts=$(PREFIX)/bin" ./

run-pep8:
	find pbreports -name "*.py" -exec pep8 --ignore=E501,E265,E731,E402 {} \;

run-auto-pep8:
	find reports -name "*.py" -exec autopep8 -i --ignore=E501,E265,E731,E402 {} \;
