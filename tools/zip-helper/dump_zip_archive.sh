#!/bin/bash

ZIP_FILE="$1"

TMP=/tmp/t42_zip

gcc -o dump_t42_color dump_t42_color.c

mkdir -p $TMP

if [[ -e "$ZIP_FILE" ]]
then
	echo "##### $ZIP_FILE"
	unzip "$ZIP_FILE" -d "$TMP"
	cat "$TMP"/*.t42 | ./dump_t42_color
fi


