#!/usr/bin/make
#
lo_version=latest

all: run
py:=2.7

.PHONY: bootstrap buildout run test cleanall startlibreoffice stoplibreoffice
bootstrap:
	if [ -f /usr/bin/virtualenv-2.7 ] ; then virtualenv-2.7 -p python$(py) .;else virtualenv -p python$(py) .;fi
	bin/pip install -r requirements.txt
	./bin/python bootstrap.py --version=2.13.2

buildout:
	if ! test -f bin/buildout;then make bootstrap;fi
	bin/buildout -Nt 5

run:
	if ! test -f bin/instance;then make buildout;fi
	bin/instance fg
	mkdir -p var/tmp

test:
	if ! test -f bin/test;then make buildout;fi
	make startlibreoffice
	rm -fr htmlcov
	bin/translation-manage -c
	env USE_STREAM=True bin/test
	make stoplibreoffice

cleanall:
	rm -fr bin develop-eggs htmlcov include .installed.cfg lib .mr.developer.cfg parts downloads eggs

startlibreoffice:
	make stoplibreoffice
	docker run -p 2002:8997 -d --rm --name="oo_server" xcgd/libreoffice:$(lo_version)
	docker ps

stoplibreoffice:
	if docker ps | grep oo_server;then docker stop oo_server;fi
