# Input & Output Databases

The input and output ligand database are in the standard VirtualFlow 2.0 format as described [here](../../documentation/backgrounds-and-principles/input-and-output-databases.md).&#x20;

## Input Ligand Databases

In AFVS, the ligands (fourth hierarchical level) in the input databases are stored as plain text files a ready-do-dock format. Currently, The formats of ligands used by AFVS for screening include pdbqt, mol2, pdb, smi and sdf.

The output ligand databases of AFLP can directly be used by AFVS for the virtual screening procedures, provided that AFLP was set up to generate the output ligand database in the correct format.&#x20;

### REAL Database of Enamine

We provide on the VirtualFlow 2.0 the REAL database of Enamine in a ready-to-dock format, ready for direct employment with AFVS. It contains over 69 billion distinct molecules.&#x20;

It was prepared with AFLP, and can be downloaded here on the VirtualFlow 2.0 homepage:&#x20;

* [https://virtual-flow.org/real-library](https://virtual-flow.org/real-library)

Specific subsets can be easily chosen on the website via an interactive interface.

## Output Databases

In AFVS, the output databases contain for each ligand a tar-archive, which contains all the docking output files for each ligand.&#x20;



