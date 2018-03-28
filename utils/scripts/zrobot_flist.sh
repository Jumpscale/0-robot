#!/usr/bin/env bash

iyo="main"

while getopts "i:" opt; do
   case $opt in
   i )  iyo=$OPTARG ;;
   esac
done


/usr/bin/python3 packages/dockerbuild.py --push --flist --iyo "$iyo" --debug