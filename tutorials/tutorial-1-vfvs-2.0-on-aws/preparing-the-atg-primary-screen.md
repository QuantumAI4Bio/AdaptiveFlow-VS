# Preparing the ATG Primary Screen

After the ATG Prescreen has been post-processed, we can run the below command in the `tools` folder to automatically prepare the ATG Primary Screen.&#x20;

```
./vfvs_prepare_atg-primary-screen-todo-files.sh tranche_min_score 10000
```

This command will create the todo files for the ATG Primary Screens. For this to happen, it first needs to create an activity map for the 18-dimensional tranche table based on the results of the ATG Prescreen. Currently, 3 methods are supported:

* **dimension\_averaging:** For each molecular property/dimension of the 18-dimensional tranche table, calculate the average for each property interval over all other dimensions. This allows selecting the most suitable hyperrectangle in the 18-dimensional tranche table for the ATG Primary Screen.&#x20;
* **tranche\_min\_score:** For individual cell/tranche in the 18-dimensional tranche table (12 million in total), calculate the minimum docking score among all docked ligands of that tranche.&#x20;
* **tranche\_ave\_score:** For individual cell/tranche in the 18-dimensional tranche table (12 million in total), calculate the average docking score among all docked ligands of that tranche.&#x20;

The subsequent arguments that are passed to the command are the number of ligands (screening size) that should be screened in the ATG Primary Screen. Multiple numbers can be specified, causing the command to create multiple todo files for each of these numbers. We only specified one screening size of 10000, meaning that around 10000 ligands (the most promising 10000) would be screened in the ATG Primary Screen. The 10000 ligands will be the ones corresponding to the tranches that were most active in the ATG Prescreen according to the activity map that was created.

After the todo files have been prepared, we can create the folders for the ATG Primary Screen. These will be new VirtualFlow folders, one for each docking scenario and screening size, and can be done automatically with the following command:

```
./vfvs_prepare_atg-primary-screen-folders.sh screening_sizes:10000 replica_counts:1 qvina02
```

The command does the following:

1. Creating new folders for the ATG Primary Screen. For each docking scenario and each specified screening size, a new screening folder is created in the parent folder `../../` (two levels above the current working directory), one for each ATG Primary Screen. In this tutorial, we have one docking scenario, and the new folder name is called atg-primaryscreen\_10000\_ds1/.
2. Copying the `input-files` and `tools` folders from `VFVS` to the new folders.
3. Copying the todo file corresponding to the screening size created in the section.[postprocessing-the-atg-prescreen.md](postprocessing-the-atg-prescreen.md "mention") to the `tools` folders.&#x20;
4. Configuring the all.ctrl file with proper settings in the `tools` folder.

Notably, the screening sizes specified here have to match the screening sizes that were specified during the preparation of the todo files for ATG Prescreen.&#x20;

Improtantly, multiple folders can be generated simultaneously by inputing multiple screening sizes seperated by comma, and multiple numbers of replicas separeated by comma. For example, `./vfvs_prepare_atg-primary-screen-folders.sh screening_sizes:1000,10000 replica_counts:1,3 qvina02`will generate 4 folders.

Usage: vfvs\_prepare\_atg-primary-screen-folders.sh screening\_sizes:\<size 1>,\<size 2>,... replica\_counts:\<replica count 1>,\<replica count 2>,...

We now change the directory to the corresponding ATG Primary Screen folder:

```
cd ../../atg-primary_10000_gk-ds1/tools
```

Then, we prepare the workflow in the same way as we did for the ATG Prescreen:

```
./vfvs_prepare_folders.py
./vfvs_prepare_workunits.py
./vfvs_build_docker.sh
```

It can happen that this command requires to be run as root, depending on your specific setup. Please try `sudo ./vfvs_build_docker.sh` in case the above command fails. The command ./vfvs\_prepare\_workunits.py will print the total number of work units. Please remember this number, as it is needed in the next section.&#x20;

