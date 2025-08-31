# Directory Structure

The structure of the `output-files` folder is described [here](../../documentation/backgrounds-and-principles/directory-structure.md#the-output-files-folder)[ ](../../documentation/backgrounds-and-principles/directory-structure.md)about VirtualFlow 2.0 in general.

In the case of VFVS 2.0, the `output-files/incomplete` and `output-files/complete` folders. These folders contain for each docking scenario the following sub-folders:

* `results`
* `summaries`
* `logfiles`
* `ligand-lists`

The `results` folder contains the original docking output files of the docking programs in the VirtualFlow 2.0 database format as described [here](../../documentation/backgrounds-and-principles/input-and-output-databases.md).

The `summaries` folder contains summaries of the docking scores for each compound.&#x20;

The `log-files` folder contains the logging output files of the docking programs,.

The `ligand-lists` folder if enabled in the control file via the `keep_ligand_summary_logs` option contains some workflow-related information for each ligand, in particular which processing steps where successful and how long time each step has taken for each ligand.



