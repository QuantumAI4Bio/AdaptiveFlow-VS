---
description: >-
  This is the first tutorial for VirtualFlow for Virtual Screening 2.0 (VFVS
  2.0).
---

# Introduction

## Aims

VFVS is one of the modules of VirtualFlow, dedicated to carrying out the virtual screening procedures.

This tutorial will demonstrate the following:

1. [How VFVS 2.0 can be installed](installation.md)
2. [How the ATG Prescreen is prepared](setting-up-the-atg-prescreen.md)
3. [How the ATG Prescreen is started](starting-the-atg-prescreen.md)
4. [How the ATG Prescreen is monitored](monitoring-the-atg-prescreen.md)
5. [How the ATG Prescreen is postprocessed](postprocessing-the-atg-prescreen.md)
6. [How the ATG Primary Screen is prepared](preparing-the-atg-primary-screen.md)
7. [How the ATG primary screen is started](running-the-atg-primary-screen.md)
8. [How the ATG primary screen is postprocessed](postprocessing-the-output-data.md)

This tutorial covers the basic functionality of VFVS 2.0. Further information regarding specific aspects of VFVS can be found in the [documentation](https://app.gitbook.com/o/-LNuBCz49KX3ym-BKSfI/s/5gQohH1mDa6hgZMywzds/).

## The Target

The target structure in this tutorial is human glucokinase (GK), and the purpose of the screening is to find activating compounds (see [Petit _et al._](http://scripts.iucr.org/cgi-bin/paper?S0907444911036729) for background information). The structure used has the following protein data bank identification (PDB ID): 4NO7 ([https://www.rcsb.org/structure/4NO7](https://www.rcsb.org/structure/4NO7)).&#x20;

![Human glucokinase (GK). The structure shown has PDB ID 4NO7.](<../.gitbook/assets/Screenshot at 2019-03-18 08-06-11.png>)

## Docking Scenarios

The files in this tutorial come with two pre-configured docking scenarios:

1. [QuickVina 2](https://academic.oup.com/bioinformatics/article/31/13/2214/195750) with exhaustiveness set to 1
2. [Smina Vinardo](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0155183) with exhaustiveness set to 1

All other docking parameters are the same for both docking programs.

The pre-configured docking box is shown below:

![](<../.gitbook/assets/Screenshot at 2019-03-18 08-02-56.png>)

![](<../.gitbook/assets/Screenshot at 2019-03-18 08-03-10.png>)

![](<../.gitbook/assets/Screenshot at 2019-03-18 08-03-18.png>)

Details on how to prepare the docking input files for Autodock Vina-based programs can for example be found at [http://vina.scripps.edu](http://vina.scripps.edu/).&#x20;





