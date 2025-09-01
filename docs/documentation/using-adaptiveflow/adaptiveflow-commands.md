# AdaptiveFlow Commands

## Overview of Commands

AdaptiveFlow provides the following commands for users:

* `aflp_prepare_folders.py`
* `aflp_prepare_workunits.py`
* `aflp_run.py`
* `aflp_submit_jobs.py`
* `afvs_prepare_folders.py`
* `afvs_prepare_workunits.py`
* `afvs_submit_jobs.py`
* `afvs_verify_collections.py`

## Location

All AdaptiveFlow commands are all stored in the `tools` folder. These commands start with the prefix "`aflp_`" for the AFLP module and the prefix "`afvs_`" for the AFVS module. The `tools` folder is also the primary working directory for any user-command available in AdaptiveFlow, meaning that all AdaptiveFlow commands have to be executed while being in this folder.

## Executing Commands

In order to be able to execute the commands in the `tools` folder, they need to either prefixed with the `./` to be found by BASH, or their locations needs to be in the `PATH` variable. We do not recommend to put the absolute path of the `tools` folder into the PATH variable, because then these command are globally available. But different versions and different modules of AdaptiveFlow can be run in parallel, and they might use different versions of these commands. Therefore, it is best to use the local versions which are stored in the `tools` folder belonging to each workflow. However, one can put the current working directory into the `PATH` variable:

```
export PATH="$PATH:."
```

The current working directory should always be added at the right-most position of the `PATH` variable due to security and safety reasons (otherwise, commands in the current working directory can override important system commands). To permanently include the current working directory in the `PATH` variable, one can put the above line into the file `~/.bashrc` file.

## Help

Each command has a `-h` (help) option to display basic usage information.



