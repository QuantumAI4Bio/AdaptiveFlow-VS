# Preparing the ATG Primary Screen

After the ATG Prescreen has been postprocessed, we can prepare the ATG Primary Screen:&#x20;

* **VFVS Folder:** Preparation of a new VFVS folder for the ATG Primary Screen
* **Input Files:** The VFVS Folder needs to be prepared by copying the docking input files into it, as well as the todo file that contains the ligand collections that should be screened. In addition, the all.ctrl file has to be configured with the proper settings. &#x20;

All of the above can be automatically done with the following command to be run in the `tools` folder:

```
./vfvs_prepare_atg-primary-screen.sh gk-vs1 10000
```

The first argument is a prefix that can be freely chosen, that used for the file path when the screening data is stored in S3. We chose the prefix gk-vs1, "gk" standing for the target glucokinase, and "vs1" for virtual screening 1. The screening size specified here has to match with the screening size that was specified during the postprocessing of the ATG Prescreen.

For each docking scenario and each specified screening size, a new VFVS folder was created in the parent folder `../../` (two levels above the current working directory), one for each ATG Primary Screen. In our case, we have one docking scenario called `gk_ds1`. We now change the directory to the corresponding ATG primary screen folder:

```
cd ../../atg-primary_10000_gk-ds1/tools
```

Then we prepare the workflow in the same way as we did for the ATG Prescreen:

```
./vfvs_prepare_folders.py
./vfvs_prepare_workunits.py
./vfvs_build_docker.sh
```

The command ./vfvs\_prepare\_workunits.py will print the total number of work units. Please remember this number, as it is needed in the next section.&#x20;

