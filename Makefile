#
# Copyright (C) 2026 Peter Varkoly <pvarkoly@cephalix.eu> Nürnberg, Germany.  All rights reserved.
#
DESTDIR        ?= /
PYTHONSITEARCH ?= /usr/lib/python3.13/site-packages/
PACKAGE         = cranix
VERSION         = $(shell cat VERSION)
HERE            = $(shell pwd)

.PHONY: all install test sdist wheel dist clean

all: test

install:
	mkdir -p $(DESTDIR)$(PYTHONSITEARCH)
	cp -r cranix $(DESTDIR)$(PYTHONSITEARCH)/
	find $(DESTDIR)$(PYTHONSITEARCH)/cranix -name '__pycache__' -type d -exec rm -rf {} +
	find $(DESTDIR)$(PYTHONSITEARCH)/cranix -name '*.pyc' -delete

test:
	python3 -m pytest -q

sdist wheel dist:
	python3 -m build

clean:
	rm -rf build dist *.egg-info .pytest_cache
	find . -name '__pycache__' -type d -exec rm -rf {} +