#!/bin/sh

if [ $# -lt 1 ]
then
    echo "usage: $0 program-name"
    exit 1
fi
PROG_NAME="$1"

while true 
do
    python $PROG_NAME
    sleep 1
done
