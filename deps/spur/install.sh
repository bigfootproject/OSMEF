#!/bin/sh

if [ z"`which pip`" = z"" ]; then
	echo "Please install the python-pip package"
	exit
fi

sudo pip install spur

