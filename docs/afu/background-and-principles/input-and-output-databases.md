# Input & Output Databases

The input and output ligand database are in the standard AdaptiveFlow format as described [here](broken-reference).&#x20;

## Input Ligand Databases

In AFVS, the ligands (fourth hierarchical level) in the input databases are stored as plain text files a ready-do-dock format. All docking programs supported so far by AdaptiveFlow support the PDBQT format, thus the PDBQT format is at the moment the only supported. The filename ending of each file has to be `.pdbqt`.  Each ligand in the PDBQT format only contains the SMILES, and no additional information.&#x20;

The output ligand databases of AFLP can directly be used with AFVS for the virtual screening procedures, provided that AFLP was set up to generate the output ligand database in the PDBQT format.&#x20;

### REAL Database of Enamine

We provide on the AdaptiveFlow the REAL database of Enamine in a ready-to-dock format, ready for direct employment with AFVS. It contains over 1.4 billion distinct molecules.&#x20;

It was prepared with AFLP, and can be downloaded here on the AdaptiveFlow homepage:&#x20;

* [https://adaptiveflow.org/real-library](https://adaptiveflow.org/real-library)

Specific subsets can be easily chosen on the website via an interactive interface.

## Output Databases

In AFVS, the output databases contain for each ligand a tar-archive, which contains all the docking output files for each ligand.&#x20;



