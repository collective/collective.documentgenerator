#!/usr/bin/make
# pyenv is a requirement, with the 3.13 python version, and virtualenv installed in it
# plone parameter must be passed to create environment 'make setup plone=6.1' or after a make cleanall
# The original Makefile can be found on https://github.com/IMIO/scripts-buildout

SHELL=/bin/bash
plones=6.1
lo_version=25.8
uno_python=/usr/bin/python3
b_o=
old_plone=$(shell [ -e .plone-version ] && cat .plone-version)

ifeq (, $(shell which pyenv))
  $(error "pyenv command not found! Aborting")
endif

ifndef plone
ifeq (,$(filter setup,$(MAKECMDGOALS)))
  plone=$(old_plone)
endif
endif

ifneq ($(wildcard bin/instance),)
    b_o=-N
endif

ifndef python
ifeq ($(plone),6.1)
  python=3.13
endif
endif

all: run

.PHONY: help
help:
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

.python-version:  ## Setups pyenv version
	@pyenv local `pyenv versions |grep "  $(python)" |tail -1 |xargs`
	@echo "Local pyenv version is `cat .python-version`"
	@ if [[ `pyenv which virtualenv` != `pyenv prefix`* ]] ; then echo "You need to install virtualenv in `cat .python-version` pyenv python (pip install virtualenv)"; exit 1; fi

bin/buildout: .python-version  ## Setups environment
	virtualenv .
	./bin/pip install --upgrade pip
	./bin/pip install -r requirements-$(plone).txt
	@echo "$(plone)" > .plone-version

.PHONY: setup
setup: oneof-plone backup cleanall bin/buildout restore  ## Setups environment for the given plone= version

.PHONY: buildout
buildout: oneof-plone bin/buildout uno-libs  ## Runs setup and buildout
	bin/buildout -t 5 -c test-$(plone).cfg ${b_o}

uno-libs:  ## Installs, for the uno python, the deps appy needs to convert documents
	$(uno_python) -m pip install -q --target uno-libs persistent

.PHONY: run
run: buildout  ## Starts the instance in foreground
	mkdir -p var/tmp
	$(MAKE) startlibreoffice
	bin/instance fg

.PHONY: test
test: oneof-plone bin/buildout uno-libs  ## Runs the tests without robot
	# can be run by example with: make test opt='-t "settings"'
	$(MAKE) startlibreoffice
	rm -fr htmlcov
	bin/translation-manage -c
	bin/test -t \!robot ${opt}
	$(MAKE) stoplibreoffice

.PHONY: cleanall
cleanall:  ## Cleans all installed buildout files
	rm -fr bin include lib local share develop-eggs downloads eggs parts htmlcov uno-libs .installed.cfg .mr.developer.cfg .python-version pyvenv.cfg

.PHONY: backup
backup:  ## Backups db files
	@if [ '$(old_plone)' != '' ] && [ -f var/filestorage/Data.fs ]; then mv var/filestorage/Data.fs var/filestorage/Data.fs.$(old_plone); mv var/blobstorage var/blobstorage.$(old_plone); fi

.PHONY: restore
restore:  ## Restores db files
	@if [ '$(plone)' != '' ] && [ -f var/filestorage/Data.fs.$(plone) ]; then mv var/filestorage/Data.fs.$(plone) var/filestorage/Data.fs; mv var/blobstorage.$(plone) var/blobstorage; fi

.PHONY: which-python
which-python: oneof-plone  ## Displays versions information
	@echo "current plone = $(old_plone)"
	@echo "current python = `cat .python-version`"
	@echo "plone var = $(plone)"
	@echo "python var = $(python)"

.PHONY: vcr
vcr:  ## Shows requirements in checkversion-r.html
	@bin/versioncheck -rbo checkversion-r-$(plone).html test-$(plone).cfg

.PHONY: vcn
vcn:  ## Shows newer packages in checkversion-n.html
	@bin/versioncheck -npbo checkversion-n-$(plone).html test-$(plone).cfg

.PHONY: startlibreoffice
startlibreoffice:  ## Starts the LibreOffice server container
	$(MAKE) stoplibreoffice
	docker run -p 2002:2002 -d --rm --pull always --name="oo_server" \
		-v /tmp:/tmp -v /var/tmp:/var/tmp \
		harbor.imio.be/library/libreoffice:$(lo_version)
	docker ps

.PHONY: stoplibreoffice
stoplibreoffice:  ## Stops the LibreOffice server container
	if docker ps | grep oo_server;then docker stop oo_server;fi

.PHONY: guard-%
guard-%:
	@ if [ "${${*}}" = "" ]; then echo "You must give a value for variable '$*' : like $*=xxx"; exit 1; fi

.PHONY: oneof-%
oneof-%:
	@ if ! echo "${${*}s}" | tr " " '\n' |grep -Fqx "${${*}}"; then echo "Invalid '$*' parameter ('${${*}}') : must be one of '${${*}s}'"; exit 1; fi
