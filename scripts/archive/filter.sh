#!/bin/bash

# This script renames files found by grepping the list of files.

bad_studies=(1083631 1193704 1277307 1282358 1284339 1329004 1395523 1436988 1549083 1570992 1740434 1778103 1807867 1828569 1882581)

for (( i=0; i<${#bad_studies[@]}; i++ ))
do
	fn=$(ls | grep ${bad_studies[i]})
	if [ -f "$fn" ]; then
		printf "${fn} exists\n"
		#mv $fn "${fn}.missingdata"
		#fn_new=$(ls | grep ${bad_studies[i]})
		#printf "${fn} is now ${fn_new}\n"
	else
		printf "${bad_studies[i]} not found\n"
	fi
done
