# Preparing the Workflow

## General

In addition to the general preparation which is required for any VirtualFlow 2.0 module as describe [here](../../documentation/installation/), for AFVS the `input-files` folder needs to be set up as described [below](preparing-the-workflow.md#preparation-of-the-input-files-folder). The exemplified step-by-step preparation can be found in the [Tutorials](broken-reference).

## Preparation of the `input-files` Folder

For using AFVS, a set of docking scenarios and scoring functions has to be set up by the user, and it can be any number of them. This is done in the `input-files` folder, which contains the following items:

* Configuration files for the docking programs
* Receptor structures
* Other files needed by the docking program
* Optional: Input ligand collection in ready-to-dock VirtualFlow 2.0 format (can also be located at another location, which can be specified in the control file)

### Docking Scenario Folders

Each docking scenario folder needs to have a file called `config.txt`, which is used by the configuration file used by all supported docking programs. For instance, for all the AutoDock Vina-based docking programs, this would be the config file which all these programs required.

Within these config files, also the receptor structure which is used by that docking scenario is specified. All files which are specified in these configuration files have to be relative paths with respect to the `tools` folder. This is the case because all docking programs are started by VirtualFlow 2.0 from the `tools` folder. For instance, if the receptor structure file `input-files/qvina_rigid_receptor1/receptor1.pdb` is specified in the docking program configuration file `input-files/qvina_rigid_receptor/config.txt`, then the path to the receptor which needs to be used would be `../input-files/qvina_rigid_receptor1/receptor1.pdb`.&#x20;

Examples of the `config.txt` for each docking program and scoring fucntion can be found [here](../supported-docking-programs-and-scoring-functions.md).

### Shared Folder for Receptor Structures

It is recommended to create a separate folder for the receptor structures, such as&#x20;

`input-files/receptors`

where all the receptor structures which are used are stored. Different docking scenarios can then make shared used of them. But theoretically, they can be stored also in docking scenario folders.

### Ligand Input Database

The ligand database to be used can be stored in any location, and the location can be specified in the control file.&#x20;

The required ligand input database can be prepared either from scratch with AFLP, or a ready-made database can be used. For virtual screenings, most users would use a ready-made database. For this purpose, we are providing the REAL database from Enamine, which can be downloaded here from the VirtualFlow website:&#x20;

* [https://virtual-flow.org/real-library](https://virtual-flow.org/real-library)

There, specific subsets of the database can be downloaded, as well as the required collection lengths file which is needed to set up the `tools` folder as described earlier [here](../../documentation/using-virtualflow-2.0/preparing-the-workflow.md#central-task-list) (i.e. this file can be used for the central task `todo.all` list which is used by VirtualFlow 2.0).



