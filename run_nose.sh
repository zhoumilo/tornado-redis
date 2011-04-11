#!/usr/bin/env sh
PYTHONPATH=../facebook-tornado/:. nosetests tests:ServerCommandsTestCase$1 --with-coverage --cover-package=brukva

