# Postprocessing the ATG Prescreen

After the ATG Prescreen has been carried out, the results have to be postprocessed, and the input files for the ATG Primary Screen created.

Before postprocessing the results, we need to download two additional files:&#x20;

* Enamine\_REAL\_Space\_2022q12.tranches.parquet
* Enamine\_REAL\_Space\_2022q12.collections.parquet

They have to be stored in the home folder, because the processing scripts expect them there. The two files can be downloaded and stored in the home folder by using the commands:

```
aws s3 cp s3://<your AWS bucket access point ID>/Enamine_REAL_Space_2022q12.tranches.parquet ~/
aws s3 cp s3://<your AWS bucket access point ID>/Enamine_REAL_Space_2022q12.collections.parquet ~/
```

The postprocessing can be done using the command:

```
./vfvs_postprocess_atg-prescreen.sh
```

In more detail, the command does the following, in order:

1. **Ligand Ranking File:** Creation of a single file containing all the ligands IDs that were screened in the ATG Prescreen (one per line) together with their final docking score, ranked by docking score. For each docking scenario, the file will be stored in the folder `../output-files/<docking scenario name>.ranking.complete.csv.gz`
2. **Reduced ranking file:** Ligand ranking file with only a few of the columns of the full ranking file, for more efficient postprocessing in several of the subsequent steps. For each docking scenario, the file will be stored in `../output-files/<docking scenario name>.ranking.subset-1.csv.gz`
3. **Sparse Metrics File:** Creation of a file that contains the average docking scores for each tranche. For the preparation of this file, the _Docking Score File_ from step 1 is needed.&#x20;

The files that the command creates are stored in the folder `../output-files`.&#x20;
