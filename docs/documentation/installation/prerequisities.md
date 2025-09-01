# Prerequisities

## Prerequisites

Described on this site are the general prerequisites, which are required for all modules of VirtualFlow 2.0. But in addition, each module of VirtualFlow 2.0 has individual prerequisites as described in the corresponding sections:

* ​[AFLP - Installation - Prerequisites](../../vflp-2.0/installation/prerequisities.md) ​
* ​[AFVS - Installation - Prerequisites](../../vfvs-2.0/installation/external-packages.md) ​
* [AFU - Installation - Prerequisites ​](../../vfu-2.0/installation/)

### Linux Cluster with Batch System <a href="#linux-cluster-with-batchsystem" id="linux-cluster-with-batchsystem"></a>

AFLP runs on Linux clusters which are managed by a batch system (resource manager), or cloud computing platforms on top of which a batch system is run. Currently, the following batch system is supported:

* SLURM
* AWS Batch

### Python <a href="#bash" id="bash"></a>

AFLP, AFVS, and VFU were only tested with Python 3.9.4 and higher. If the system Python is older than 3.9.4, normally the system admins of the Linux cluster can make a newer version available. Alternatively, one can compile a recent version of Python by oneself and install it locally (for instance in the home folder).&#x20;



