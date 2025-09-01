# Directory Structure

## General

The directory structure of AFLP is the same as that for VirtualFlow 2.0 in general (as described [here](../../documentation/backgrounds-and-principles/directory-structure.md)).

## The `input-files` Folder

What is specific for AFLP is that the `input-files` folder does not contain anything, except possibly the input ligand collection,  which can also be stored at another location (as specifiable in the control file). The reason that the `input-files` folder does not need to contain anything is that the external programs which are used by AFLP do not need any input files except the ligands.
