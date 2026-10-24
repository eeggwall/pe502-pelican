# Build, preview and test the PE502 site. See README.md.

PYTHON ?= python3
PELICAN = $(PYTHON) -m pelican

.PHONY: html serve publish test clean

html:
	$(PELICAN) content -s pelicanconf.py

serve:
	$(PELICAN) content -s pelicanconf.py --autoreload --listen

publish:
	$(PELICAN) content -s publishconf.py

test:
	$(PYTHON) -m unittest discover -s tests

clean:
	rm -rf output
