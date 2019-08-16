#!/bin/bash
#Uses mscgen to build sequence diagrams
for each in `find . -wholename "*.msc" -type f -printf '%P\n'`; do
	NAME="`echo $each | cut -d '.' -f 1`"
	EXT="`echo $each | cut -d '.' -f 2`"
	echo $NAME
	mscgen -i $each -o "$NAME.png" -T png
done
