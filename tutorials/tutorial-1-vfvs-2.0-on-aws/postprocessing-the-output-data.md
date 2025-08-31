# Postprocessing the ATG Primary Screen

To create the ranking of the screened ligand by docking score, we can run the following command:

```
./vfvs_get_top_results.py --top 10000 --download --scenario-name ds1
```

This will download the ranking containing the best 10000 ligands, and store the ranking file in the `../output-files` folder.&#x20;
