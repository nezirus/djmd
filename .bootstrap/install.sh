#!/bin/bash

# $Revision$

# Virtualenv bootstrap script.
#
# Copyright (C) 2012-2013 Adis Nezirović <adis at localhost.ba>

VIRTUALENV_URL="https://raw.github.com/pypa/virtualenv/master/virtualenv.py"
SCRIPT_PATH=$(readlink -f $0)
SCRIPT_DIR=$(dirname $SCRIPT_PATH)

## Virtualenv installation >
rm -rf $SCRIPT_DIR/virtualenv.py $SCRIPT_DIR/virtualenv.pyc
wget -O $SCRIPT_DIR/virtualenv.py $VIRTUALENV_URL

if [[ $? != 0 ]]; then
	echo "Could not download virtualenv.py"
	exit 1
fi

rm -rf $SCRIPT_DIR/../.virtualenv
python $SCRIPT_DIR/virtualenv.py $SCRIPT_DIR/../.virtualenv

if [[ $? != 0 ]]; then
	echo "Could not create virtualenv"
	exit 1
fi

if [[ -r $SCRIPT_DIR/../.virtualenv/bin/activate ]]; then
	source $SCRIPT_DIR/../.virtualenv/bin/activate
else
	echo "Could not activate virtualenv"
	exit 1
fi

pip install -r $SCRIPT_DIR/requirements.txt
