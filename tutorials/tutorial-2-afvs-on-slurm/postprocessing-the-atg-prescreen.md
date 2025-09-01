# \* Postprocessing the ATG Prescreen

After the ATG Prescreen has been carried out, the results have to be postprocessed, and the input files for the ATG Primary Screen created.

The postprocessing can be done using the command

```
./afvs_postprocess_atg-prescreen.sh 10000
```

The argument(s) that are passed to the command are the number of ligands (screening size) that should be screened in the ATG Primary Screen. Multiple numbers can be specified, causing the command to create multiple todo files for each of these numbers. We only specified one screening size of 10000, meaning that around 10000 ligands (the most promising 10000) would be screened in the ATG Primary Screen. The 10000 ligands will be the ones corresponding to the tranches that were most active in the ATG Prescreen. The command calculates the activity (average docking score) of each tranche of the library that was screened in the ATG Prescreen.&#x20;

In more detail, the command does the following, in order:

1. **Docking Score File:** Creation of a single file containing all the ligands that were screened in the ATG Prescreen (one per line) together with their final docking score.&#x20;
2. **Sparse Metrics File:** Creation of a file that contains the average docking scores for each tranche. For the preparation of this file, the Docking Score File is needed.&#x20;
3. **Todo File:** Creation of one or more todo files for the ATG Primary Screens. One todo file is created for each screening size that is passed to the command. For the preparation of this file, the Sparse Metrics File is needed.&#x20;

The files that the command creates are stored in the folder `../output-files`.&#x20;
