# Supported docking programs and scoring functions

AFVS supports many docking programs and scoring functions that run on both CPUs and GPUs. For using docking programs and scoring functions on GPUs, please modify the job submission file (`/tools/templates/template1.slurm.sh`) to indicate access to GPU nodes for running docking. To use a specific docking program or a scoring function of interest, the following modification may be required:

1. Properly install the executable binary programs.
2. Modify the `all.ctrl` file located in the `tools/templates` directory to specify the format of the ligands to be screened and the name of the docking program to be used.
3. Create the configuration file (`config.txt`) to provide the parameters required by the docking program to dock. Examples of how the config.txt file looks like for each docking program are displayed in [the AdaptiveFlow github repository](../../tools/templates/DOCKING_SOFTWARE_NOTES.md).

## AutoDock-GPU

1. The AutoDock\_GPU executable program (of name 'autodock\_gpu') should be placed in the`/tools/bin` directory. The corresponding executable program needs to be compiled based on the user’s system using the instructions described [here](https://github.com/ccsb-scripps/AutoDock-GPU).
2. In `all.ctrl` file, set

```
ligand_library_format=pdbqt
docking_scenario_programs=autodock_gpu
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## AutoDock4/AutoDock-CPU

1. The autodock4 executable program (of name 'autodock\_cpu') should be placed in the`/tools/bin`directory. The corresponding executable program needs to be compiled based on the user’s system using the instructions described [here](https://github.com/ccsb-scripps/AutoDock-GPU).
2. In `all.ctrl` file, set

```
ligand_library_format=pdbqt
docking_scenario_programs=autodock_cpu
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## AutoDock-ZN

1. Installation of the external docking program is not required.
2. In `all.ctrl` file, set

```
ligand_library_format=pdbqt
docking_scenario_programs=AutodockZN
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## AutoDockVina 1.2

1. Installation of the external docking program not required.
2. In `all.ctrl` file, set

```
ligand_library_format=pdbqt
docking_scenario_programs=AutodockVina_1.2
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## AutoDockVina 1.1.2

1. Installation of the external docking program is not required.
2. In `all.ctrl` file, set

```
ligand_library_format=pdbqt
docking_scenario_programs=AutodockVina_1.1.2
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## ADFR

1. The ADFR executable program (of name adfr) should be placed in the`/tools/bin` directory. The corresponding executable program needs to be compiled based on the user’s system using the instructions described [here](https://ccsb.scripps.edu/adfr/downloads/).
2. In `all.ctrl` file, set

```
ligand_library_format=pdbqt
docking_scenario_programs=adfr
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## AutoDock Koto

1. Installation of the external docking program is not required.
2. In `all.ctrl` file, set

```
ligand_library_format=pdbqt
docking_scenario_programs=autodock_koto
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## CovDock

1. Installation of the external docking program is not required.
2. In `all.ctrl` file, set

```
ligand_library_format=pdbqt
docking_scenario_programs=CovDock
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## GlideHTVS

1. Installation of the external docking program not required.
2. In `all.ctrl` file, set

```
ligand_library_format=smi
docking_scenario_programs=GlideHTVS
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## GlideSP

1. Installation of the external docking program is not required.
2. In `all.ctrl` file, set

```
ligand_library_format=smi
docking_scenario_programs=GlideSP
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## GlideXP

1. Installation of the external docking program is not required.
2. In `all.ctrl` file, set

```
ligand_library_format=smi
docking_scenario_programs=GlideXP
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## DOCK6.0

1. Installation of the external docking program is not required.
2. In `all.ctrl` file, set

```
ligand_library_format=mol2
docking_scenario_programs=dock6
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## Flexx

1. Installation of the external docking program is not required.
2. In `all.ctrl` file, set

```
ligand_library_format=mol2
docking_scenario_programs=flexx
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## FitDock

1. The FitDock executable program (of name 'FitDock') should be placed in the`/tools/bin` directory.
2. In `all.ctrl` file, set

```
ligand_library_format=mol2
docking_scenario_programs=FitDock
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## Gnina

1. The Gnina executable program (of name 'Gnina') should be placed in the`/tools/bin` directory.
2. In `all.ctrl` file, set

```
ligand_library_format=pdbqt
docking_scenario_programs=gnina
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## GalaxyDock3

1. The GalaxyDock3 executable program (of name 'GalaxyDock3') should be placed in the`/tools/bin` directory.
2. In `all.ctrl` file, set

```
ligand_library_format=mol2
docking_scenario_programs=GalaxyDock3
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## GOLD

1. The GOLD executable program (of name 'gold\_auto') should be placed in the`/tools/bin` directory.
2. In `all.ctrl` file, set

```
ligand_library_format=mol2
docking_scenario_programs=gold
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## GWOVina

1. Installation of the external docking program is not required.
2. In `all.ctrl` file, set

```
ligand_library_format=pdbqt
docking_scenario_programs=gwovina
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## HDock

1. The HDock executable program (of name 'hdock') and the createpl executable program (of name 'createpl') should be placed in the`/tools/bin` directory.
2. In `all.ctrl` file, set

```
ligand_library_format=pdb
docking_scenario_programs=HDock
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## idock

1. Installation of the external docking program is not required.
2. In `all.ctrl` file, set

```
ligand_library_format=pdbqt
docking_scenario_programs=idock
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## iGemDock

1. The iGemDock executable program (of name 'mod\_ga') should be placed in the`/tools/bin` directory.
2. In `all.ctrl` file, set

```
ligand_library_format=mol2
docking_scenario_programs=iGemDock
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## LeDock

1. Installation of the external docking program is not required.
2. In `all.ctrl` file, set

```
ligand_library_format=mol2
docking_scenario_programs=ledock
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## LigandFit

1. The LigandFit executable program (of name 'ligandfit') should be placed in the`/tools/bin`directory.
2. In `all.ctrl` file, set

```
ligand_library_format=pdb
docking_scenario_programs=LigandFit
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## LightDock

1. Installation of the external docking program is not required.
2. In `all.ctrl` file, set

```
ligand_library_format=pdb
docking_scenario_programs=LightDock
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## MDock

1. The MDock executable program (of name 'MDock\_linux') should be placed in the`/tools/bin` directory.
2. In `all.ctrl` file, set

```
ligand_library_format=mol2
docking_scenario_programs=M-Dock
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## MCDock

1. The MCDock executable program (of name 'mcdock') should be placed in the`/tools/bin` directory.
2. In `all.ctrl` file, set

```
ligand_library_format=xyz
docking_scenario_programs=MCDock
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## Molegro

1. Installation of the external docking program is not required.
2. In `all.ctrl` file, set

```
ligand_library_format=mol2
docking_scenario_programs=Molegro
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## MpSDockZN

1. Installation of the external docking program is not required.
2. In `all.ctrl` file, set

```
ligand_library_format=mol2
docking_scenario_programs=MpSDockZN
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## PSOVina

1. Installation of the external docking program is not required.
2. In `all.ctrl` file, set

```
ligand_library_format=pdbqt
docking_scenario_programs=PSOVina
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## PLANTS

1. Installation of the external docking program is not required.
2. In `all.ctrl` file, set

```
ligand_library_format=mol2
docking_scenario_programs=plants
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## QuickVina2

1. Installation of the external docking program is not required.
2. In `all.ctrl` file, set

```
ligand_library_format=pdbqt
docking_scenario_programs=qvina
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## QuickVina-W

1. Installation of the external docking program is not required.
2. In `all.ctrl` file, set

```
ligand_library_format=pdbqt
docking_scenario_programs=qvina_w
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## QuickVina\_gpu

1. The qvina\_gpu executable program (of name 'qvina\_gpu') should be placed in the`/tools/bin` directory. Instructions for compilation can be found [here](https://github.com/DeltaGroupNJUPT/QuickVina2-GPU).
2. In `all.ctrl` file, set

```
ligand_library_format=pdbqt
docking_scenario_programs=qvina_gpu
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## QuickVina-W-gpu

1. The QuickVina-W-gpu executable program (of name 'qvina\_w\_gpu') should be placed in the`/tools/bin` directory.
2. In `all.ctrl` file, set

```
ligand_library_format=pdbqt
docking_scenario_programs=qvina_w_gpu
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## rDock

1. The key word 'rbdock' must be able to activate the program (see [download instructions](https://rdock.sourceforge.net/), or, download with conda: conda install -c bioconda rdock)
2. In `all.ctrl` file, set

```
ligand_library_format=mol2
docking_scenario_programs=rDock
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## Rosetta-Ligand

1. Please ensure that obabel is loaded into the environment (module load openbabel for Slurm)
2. In `all.ctrl` file, set

```
ligand_library_format=sdf
docking_scenario_programs=rosetta-ligand
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## RLDock

1. Installation of the external docking program is not required.
2. In `all.ctrl` file, set

```
ligand_library_format=mol2
docking_scenario_programs=RLDock
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## SEED

1. The SEED executable program (of name 'seed4') should be placed in the`/tools/bin` directory. In addtion, AmberTools needs to be loaded in order to use SEED.
2. In `all.ctrl` file, set

```
ligand_library_format=mol2
docking_scenario_programs=SEED
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## SMINA

1. Installation of the external docking program is not required.
2. In `all.ctrl` file, set

```
ligand_library_format=pdbqt
docking_scenario_programs=smina
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## VinaCarb

1. Installation of the external docking program is not required.
2. In `all.ctrl` file, set

```
ligand_library_format=pdbqt
docking_scenario_programs=nina_carb
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## VinaXB16

1. Installation of the external docking program is not required.
2. In `all.ctrl` file, set

```
ligand_library_format=pdbqt
docking_scenario_programs=vina_xb
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## Vina-Gpu

1. The qvina\_gpu executable program (of name 'qvina\_w\_gpu') should be placed in the`/tools/bin` directory. Instructions for compilation can be found [here](https://github.com/DeltaGroupNJUPT/Vina-GPU).
2. In `all.ctrl` file, set

```
ligand_library_format=pdbqt
docking_scenario_programs=qvina_w_gpu
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## Vina-Gpu-2.0

1. The qvina\_gpu executable program (of name 'qvina\_w\_gpu') should be placed in the`/tools/bin` directory. Instructions for compilation can be found [here](https://github.com/DeltaGroupNJUPT/Vina-GPU).
2. In `all.ctrl` file, set

```
ligand_library_format=pdbqt
docking_scenario_programs=qvina_w_gpu
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## Scoring with NNScore2.0

1. Installation of the external docking program is not required.
2. In `all.ctrl` file, set

```
ligand_library_format=pdbqt
docking_scenario_programs=nnscore2.0
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## Scoring with rf-score-vs

1. The rf-score-vs executable program (of name 'rf-score-vs') should be placed in the`/tools/bin` directory.
2. In `all.ctrl` file, set

```
ligand_library_format=pdbqt
docking_scenario_programs=rf-score-vs
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## Scoring with smina

1. Installation of the external docking program is not required.
2. In `all.ctrl` file, set

```
ligand_library_format=pdbqt
docking_scenario_programs=smina_scoring
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## Scoring with gnina

1. The gnina executable program (of name 'gnina') should be placed in the`/tools/bin` directory.
2. In `all.ctrl` file, set

```
ligand_library_format=pdbqt
docking_scenario_programs=gnina_scoring
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## Scoring with AutoDock4

1. Installation of the external docking program is not required.
2. In `all.ctrl` file, set

```
ligand_library_format=pdbqt
docking_scenario_programs=ad4_scoring
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## Scoring with Vinandro

1. Installation of the external docking program is not required.
2. In `all.ctrl` file, set

```
ligand_library_format=pdbqt
docking_scenario_programs=vinandro_scoring
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).

## Scoring with vina

1. Installation of the external docking program is not required.
2. In `all.ctrl` file, set

```
ligand_library_format=pdbqt
docking_scenario_programs=vina_scoring
```

3. For an example of the`config.txt` file, please refer to [the AdativeFlow github repository](https://github.com/Liganduniverse/AFVS/blob/develop/tools/templates/DOCKING_SOFTWARE_NOTES.md).
