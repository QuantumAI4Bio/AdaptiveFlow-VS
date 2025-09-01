#!/bin/sh

#Checking the input arguments
usage="Usage: afvs_postprocess_atg-prescreen.sh

Description: Postprocessing the ATG Prescreen, and preparing the todo files for the ATG Primary Screens. The script can handle multiple docking scenarios in the ATG Prescreen.

"

if [ "${1}" == "-h" ]; then
   echo -e "\n${usage}\n\n"
   exit 0
fi
if [ "$#" -ne "0" ]; then
   echo -e "\nWrong number of arguments."
   echo -e "\n${usage}\n\n"
   echo -e "Exiting..."
   exit 1
fi

# Output-files directory
echo "Creating output-files folder (if it does not yet exist) ..."
mkdir -p ../output-files
cd ../output-files

# Getting the CSV files with the ligand rankings
for ds in $(cat ../workflow/config.json  | jq -r ".docking_scenario_names" | tr "," " " | tr -d '"\n[]' | tr -s " "); do
  echo "Generating the ranking of docking scenario ${ds} and downloading it to ../output-files/${ds}.ranking.complete.csv ..."
  ../tools/afvs_get_top_results.py --scenario-name $ds --download
done

# Creating subset of the CSV files
for ds in $(cat ../workflow/config.json  | jq -r ".docking_scenario_names" | tr "," " " | tr -d '"\n[]' | tr -s " "); do
  echo "Creating a subset of the ranking file with fewer columns and storing it in ../output-files/${ds}.subset-1.csv.gz ..."
  awk 'BEGIN { FS=OFS="," } { gsub("_", ",", $2); print }' ${ds}.ranking.complete.csv | awk -F ',' '{print $2","$3","$1","$5}' | sed "1s/.*/Tranche,Collection,LigandVFID,ScoreMin/" | tr -d '"' | pigz -c > ${ds}.ranking.subset-1.csv.gz
done

# Compressing the complete ranking files
for ds in $(cat ../workflow/config.json  | jq -r ".docking_scenario_names" | tr "," " " | tr -d '"\n[]' | tr -s " "); do
  echo "Compressing the file ../output-files/${ds}.ranking.complete.csv into ../output-files/${ds}.ranking.complete.csv.gz ..."
  cat ${ds}.ranking.complete.csv | tr -d '"' | pigz -c > ${ds}.ranking.complete.csv.gz
  rm ${ds}.ranking.complete.csv
done

wait 

cd ../tools
