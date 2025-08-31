# Introduction

## General

VirtualFlow 2.0 is a versatile, parallel workflow platform for carrying out virtual screening related tasks on Linux-based clusters of any size which are managed by a batch system (resource manager).

Since resource managers can run on top of cloud computing platforms, VirtualFlow 2.0 is also ready to be directly deployed on cloud platforms like Amazon Web Services (AWS), Google's Cloud Platform (GCP), or Microsofts Azure. More information can be found in the section [Running VirtualFlow 2.0 in the Cloud](documentation/running-virtualflow-2.0-in-the-cloud.md).

## Modules

Currently, there exist three VirtualFlow 2.0 modules, [**VFLP 2.0 (**&#x56;irtualFlow 2.0 for Ligand Preparation)](vflp-2.0/introduction.md), [**VFVS 2.0 (**&#x56;irtualFlow 2.0 for Virtual Screenings)](vfvs-2.0/introduction.md) and [**VFU 2.0** (VirtualFlow Unity 2.0)](vfu-2.0/introduction.md). These three modules share a common core technology, and therefore also a number of features. The documentation therefore exists of four parts, a general part for all versions of VirtualFlow 2.0, and one part for each VFLP 2.0, VFVS 2.0 and VFU 2.0:

* [**VFLP 2.0:** VirtualFlow 2.0 for Ligand Preparation](vflp-2.0/introduction.md)
* [**VFVS 2.0:** VirtualFlow 2.0 for Virtual Screenings](vfvs-2.0/introduction.md)
* [**VFU 2.0**: VirtualFlow Unity 2.0](vfu-2.0/introduction.md)

Information for each VirtualFlow 2.0 module and how to use it is therefore distributed in two different parts of the documentation (for instance information about VFVS 2.0 and how to use it is found in the general part called VirtualFlow 2.0, as well as in the part of the documentation dedicated to VFVS 2.0). The general information is not duplicated in the more specific parts, therefore the general part is always relevant.

## Applications

VirtualFlow 2.0 can be used for many steps relevant in the drug discovery process, such as:

* **Ligand preparation (VFLP 2.0 & VFU 2.0)**
  * Preparation of general-purpose ligand databases, e.g. into a ready-to-dock format
  * Preparation of custom analog libraries based for hit/lead optimization\

* **Hit identification (VFVS 2.0 & VFU 2.0)**
  * By virtually screening privately or publicly available ligand libraries\

* **Hit/lead optimization (VFVS 2.0 & VFU 2.0)**
  * By screening custom libraries of analogs of certain hit/lead compounds\

* **Binding site identification of experimental hits (VFVS 2.0 & VFU 2.0)**
  * By carrying out extensive docking studies of the hit compounds

## Learning VirtualFlow 2.0

VirtualFlow 2.0 tries to make virtual screening-related tasks on computer clusters and cloud computing platforms as simple as possible. But because each cluster and computing platform is different, it still can take some time to learn everything you need to know. In particular, the following topics are relevant:&#x20;

* _Linux/Bash:_ You should be comfortable with using the Linux command line, in particular Bash. There are many online tutorials available, such as [this](https://www.tldp.org/LDP/Bash-Beginners-Guide/html/Bash-Beginners-Guide.html) one.
* _Linux Clusters/Resource Managers:_ You need to be comfortable with using the cluster you want to use (at the moment Slurm and AWS Batch are supported). Often, the institution which provides/manages the cluster regularly offers free user training sessions for beginners which one can take part in.
* _VirtualFlow 2.0_: You need to understand how VirtualFlow 2.0 works, and how to use it.

### How long does it take to learn using VirtualFlow 2.0?

If you are new to Linux, the command line, and/or computer clusters, and need to learn the basics, it might take a week or two to learn everything you need to know to use VirtualFlow 2.0 efficiently.

If you are already comfortable with the Linux command line and computer cluster or AWS, learning VirtualFlow 2.0 is relatively simple. However, it still will need some initial time (a few days) to understand how everything works and to be able to use it efficiently. But once you know everything, using VirtualFlow 2.0 will become a breeze.



