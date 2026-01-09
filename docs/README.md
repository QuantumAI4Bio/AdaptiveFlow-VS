# Introduction

## General

AdaptiveFlow is a versatile, parallel workflow platform for carrying out virtual screening related tasks on Linux-based clusters of any size which are managed by a batch system (resource manager).

Since resource managers can run on top of cloud computing platforms, AdaptiveFlow is also ready to be directly deployed on cloud platforms like Amazon Web Services (AWS), Google's Cloud Platform (GCP), or Microsofts Azure. More information can be found in the section [Running AdaptiveFlow in the Cloud](documentation/running-adaptiveflow-in-the-cloud.md).

## Modules

Currently, there exist three AdaptiveFlow modules, [**AFLP (**&#x56;irtualFlow 2.0 for Ligand Preparation)](aflp/introduction.md), [**AFVS (**&#x56;irtualFlow 2.0 for Virtual Screenings)](afvs/introduction.md) and [**AFU** (AdaptiveFlow Unity)](afu/introduction.md). These three modules share a common core technology, and therefore also a number of features. The documentation therefore exists of four parts, a general part for all versions of AdaptiveFlow, and one part for each AFLP, AFVS and AFU:

* [**AFLP:** AdaptiveFlow for Ligand Preparation](aflp/introduction.md)
* [**AFVS:** AdaptiveFlow for Virtual Screenings](afvs/introduction.md)
* [**AFU**: AdaptiveFlow Unity](afu/introduction.md)

Information for each AdaptiveFlow module and how to use it is therefore distributed in two different parts of the documentation (for instance information about AFVS and how to use it is found in the general part called AdaptiveFlow, as well as in the part of the documentation dedicated to AFVS). The general information is not duplicated in the more specific parts, therefore the general part is always relevant.

## Applications

AdaptiveFlow can be used for many steps relevant in the drug discovery process, such as:

* **Ligand preparation (AFLP & AFU)**
  * Preparation of general-purpose ligand databases, e.g. into a ready-to-dock format
  * Preparation of custom analog libraries based for hit/lead optimization
* **Hit identification (AFVS & AFU)**
  * By virtually screening privately or publicly available ligand libraries
* **Hit/lead optimization (AFVS & AFU)**
  * By screening custom libraries of analogs of certain hit/lead compounds
* **Binding site identification of experimental hits (AFVS & AFU)**
  * By carrying out extensive docking studies of the hit compounds

## Learning AdaptiveFlow

AdaptiveFlow tries to make virtual screening-related tasks on computer clusters and cloud computing platforms as simple as possible. But because each cluster and computing platform is different, it still can take some time to learn everything you need to know. In particular, the following topics are relevant:

* _Linux/Bash:_ You should be comfortable with using the Linux command line, in particular Bash. There are many online tutorials available, such as [this](https://www.tldp.org/LDP/Bash-Beginners-Guide/html/Bash-Beginners-Guide.html) one.
* _Linux Clusters/Resource Managers:_ You need to be comfortable with using the cluster you want to use (at the moment Slurm and AWS Batch are supported). Often, the institution which provides/manages the cluster regularly offers free user training sessions for beginners which one can take part in.
* _AdaptiveFlow_: You need to understand how AdaptiveFlow works, and how to use it.

### How long does it take to learn using AdaptiveFlow?

If you are new to Linux, the command line, and/or computer clusters, and need to learn the basics, it might take a week or two to learn everything you need to know to use AdaptiveFlow efficiently.

If you are already comfortable with the Linux command line and computer cluster or AWS, learning AdaptiveFlow is relatively simple. However, it still will need some initial time (a few days) to understand how everything works and to be able to use it efficiently. But once you know everything, using AdaptiveFlow will become a breeze.
