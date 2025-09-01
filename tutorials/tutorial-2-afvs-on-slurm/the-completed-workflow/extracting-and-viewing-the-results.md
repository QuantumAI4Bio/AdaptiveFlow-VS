# Extracting and viewing the results

Docked ligands are stored in archives located in the `/output-files` folder (for example):  \
\
/AFVS/output-files/qvina02\_rigid\_receptor1/logs/1/0.tar.gz\


In order to extract the docked poses and generate a file containing predicted affinities for each compound, one can use the following scripts:&#x20;

{% file src="../../.gitbook/assets/extract_poses_to_folder.py" %}

{% file src="../../.gitbook/assets/extract_scores.py" %}

The first script to execute is `extract_poses_to_folder.py.` It is meant to extract docking poses located in archives present in the current folder to a folder named `/results.` You can easily modify the path to the archive(s) you want to extract by editing the line 35 in the script: \
\
`Specify the path to your tar.gz file`

`tar_file_path = '0.tar.gz'`\
\
The second script, extract\_scores.py, will generate a file named `scores.csv`, containing the names and binding affinities of all the previously extracted poses, located in the `./results` folder. Please be aware that the script currently only extracts docking scores that have negative values. \
The resulting file can be viewed in the linux terminal using for example `vi` or `nano`.
