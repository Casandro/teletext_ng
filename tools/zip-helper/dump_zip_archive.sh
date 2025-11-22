#!/bin/bash

ZIP_FILE="$1"


gcc -o dump_t42_color dump_t42_color.c


if [[ -e "$ZIP_FILE" ]]
then
	echo "##### $ZIP_FILE"
	unzip -p "$ZIP_FILE"   | ./dump_t42_color
fi


