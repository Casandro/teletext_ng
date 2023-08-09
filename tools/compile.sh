#!/bin/bash


for x in *.c
do
	gcc $x -o `basename $x .c` 
done
