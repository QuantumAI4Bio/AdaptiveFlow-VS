# Preparing the Workflow

## General

To prepare AdaptiveFlow for a workflow, the following needs to be done:

* [Installation of the desired module of AdaptiveFlow](../installation/)
* [Preparation of the input-files folder](preparing-the-workflow.md#preparation-of-the-input-files-folder)
* [Preparation of the tools folder](preparing-the-workflow.md#preparation-of-the-tools-folder)
* [Preparation of the `workflow` and `output-files` folders](preparing-the-workflow.md#preparation-of-the-workflow-and-output-files-folders)

## Preparation of the `input-files` Folder

As described [here](../backgrounds-and-principles/directory-structure.md) in the _Background and Principles_ section, the `input-files` folder only contains the input files which are used by the external programs which process the ligands in the workflow. The only exception can be the input ligand database, which can be stored in some other centralized location (to be shareable by multiple independent AdaptiveFlow workflows). However, if it is stored in the AdaptiveFlow workflow folder, then the `input-files` folder is naturally the proper location. The location which is used is specified in the control file.

Currently, AFLP does not require the input-files folder as described here:

* [AFLP - Directory Structure - `input-files` folder](../../aflp/background-and-principles/directory-structure.md)

AFVS does require the `input-files` folder for docking input files, as described here:

* [AFVS - Preparing the Workflow - `input-files` folder](../../afvs/using-afvs/preparing-the-workflow.md#preparation-of-the-input-files-folder)

AFU - does not require the input-files folder as described here:

* AFU -

## Preparation of the `tools` Folder

The `tools` folder is only used by the user, not by the workflow. But it needs to be setup properly, as the `tools` folder is used to set up the `workflow` folder (see [below](preparing-the-workflow.md#preparation-of-the-workflow-and-output-files-folders)).

To prepare the `tools` folder of AdaptiveFlow, the following files have to be prepared:

* [The initial control file (`tools/templates/all.ctrl`)](broken-reference/)
* [The central task list (`tools/templates/todo.all`](broken-reference/))
* The batch template file ( tools/temlates/template1.slurm.sh for SLURM cluster or tools/temlates/template1.awsbatch.sh for AWS cloud)

The `tools` folder is the primary working directory of AdaptiveFlow. All AdaptiveFlow user commands (starting with `aflp_` and `afvs_`) have to be run within this directory.

### Initial Control-file

The initial control file `tools/templates/all.ctrl` needs to be set up. All parameters are explained in within the file itself.

{% hint style="info" %}
If one has the choice of submitting many small jobs (such as 1-CPU jobs), or fewer large jobs (e.g. multi-node jobs), the latter is generally preferable regarding the central task list. But this usually only becomes relevant with very large numbers of jobs.
{% endhint %}

Multiple different control files for different job-lines can be employed once the `workflow` folder was prepared ([see below](preparing-the-workflow.md#control-files)).

### Central Task List

The central task list `tools/templates/todo.all` needs to be set up.

The file contains the ligand collections which should be processed by the workflow. One ligand collection corresponds to one task for the workflow, even though one collection can contain any number of ligands. For each collection one line is used in the central task list, and it has the format:

`<tranch>_<collection name> <# of ligands in the collection>`

Regarding the databases which we provide, e.g. the REAL database of Enamine, a so called _collection lengths file_ (usually it has the name`length.all`) which contains the lengths of the collections is provided along with the database on the download page. The collection lengths file and the `todo.all` file have the same format. The `todo.all` file can be either the full `lengths.all` file (i.e. when screening the entire library), or a subset of it. If all of the collections in the file should be screened, the file can simply be copied to `tools/templates/todo.all`.

If one wants to screen only a subset of the collections of the database, one can do that by extracting the subset of the length file wants to screen, and store them in the `tools/templates/todo.all` file. The selection of subsets is most easily done with grep command.

For example, if one wants to screen all the collections of tranches with names which start with the letter "A", this can be done by the command:

```
grep "^A" length.all > tools/templates/todo.all
```

Here the caret symbol "^" indicates the beginning of a line, meaning that the letter "A" has to be at the beginning in order for a match to happen. For more detailed information about the grep command, see either the corresponding man-page (which can be accessed by running the command `man grep` or [here](http://man7.org/linux/man-pages/man1/grep.1.html) online), or other online resources such as [here](https://www.tldp.org/LDP/Bash-Beginners-Guide/html/sect_04_02.html).

### The Job File Template

AdaptiveFlow uses a job file template for the job it submits into the resource manager (batch system). The job template needs to be adjusted according to the one's preferences and according to the cluster requirements and constraints.

In particular the following settings in the job file template should set appropriately:

* Memory requirements
* Special settings required by the cluster
* Email notification settings

The following settings should be left unchanged, as they are handled internally by AdaptiveFlow and can be set partially in the control file.

* job name (can be partially set in the control file)
* partition (can be set in the control file)
* wall-time (can be set in the control file)
* number of nodes (can be set in the control file)
* number of cpus/gpus and job steps (can be set in the control file)
* input/output log files

Some clusters might require additional modules to be loaded, e.g. if OpenBabel which is used by AFLP should be loaded as a module, it needs to go into the job template (see also [AFLP - Installation - External Packages](../../aflp/installation/external-packages.md)).

## Preparation of the`workflow` and `output-files` Folders

### General

The `workflow` and `output-files` folders need to be prepared before the workflow can be started for the first time. This is done with the command `aflp_prepare_folders.py` `or afvs_ prepare_folders.py`. The preparation of the `workflow` folder is based on the current configuration/settings of the `tools` folder, therefore the `tools` folder needs to be set up at first.

{% hint style="info" %}
The command `aflp_prepare_folders.py` or `afvs_ prepare_folders.py` removes previously existing `output-files` and `workflow` folders if they are present, which can be the case if test runs were carried out before. Therefore this command has to be used with care as it can delete important files.
{% endhint %}

The preparation of the workflow folder by the command `aflp_prepare_folders.py` `or afvs_prepare_folders.py` does the following steps automatically:

* Deletion of previously existing `workflow` folders and files (if they exist)
* Creation of (new)`workflow` folders and files which consist of:
  * `workflow/workunits`
  * `workflow/config.json`
  * `workflow/collections.json`

The preparation of the workflow folder by the command `aflp_prepare_workunits.py` `or afvs_ prepare_workunits.py` does the following steps automatically:

* Deletion of previously existing `workunits` files (if they exist)
* Deletion of previously existing status files in the workflow folder (if they exist)
* Creation of (new) `workfunits` files
* Creation of (new) `workflow` statue files which include:
  * `workflow/status.json`
  * `workflow/status.todolists.json`
