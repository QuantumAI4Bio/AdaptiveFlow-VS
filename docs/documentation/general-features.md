# General Features

The following describes the features of AdaptiveFlow in general. The features specific to each AdaptiveFlow module are described in the corresponding chapters:

* [AFLP - Features](../aflp/features.md)
* [AFVS - Features](../afvs/features.md)
* [AFU - Features](../afu/features.md)

## **Scaling Behavior**

AdaptiveFlow can be extremely fast due to its perfect scaling behavior (even when using a very large number of CPUs). There are virtually no bounds regarding the number of processors which can be utilized by AdaptiveFlow. We demonstrated a perfectly linear scaling behavior up to 5.6 million CPUs in the AWS Cloud, a new global record for parallel cloud computing.&#x20;

## Versatile Docking Methods Support

AdaptiveFlow supports 1500 unique docking methods. These include target-specific docking methods (e.g. for RNA and DNA), as well as consensus docking options to increase accuracy, and it has the ability to screen different types of ligands (such as small molecules and peptides). Moreover, AdaptiveFlow supports the latest deep learning- and GPU-based docking methods, allowing further speed-ups by up to two orders of magnitude. In addition, it supports some of the fastest CPU-based docking programs available such as QuickVina 2.

## Highly Efficient Ultra-large Virtual Screening

AdaptiveFlow supports multiple techniques that dramatically reduce computational costs, including a new method called Adaptive Target-Guided Virtual Screening (ATG-VS). By sampling a representative sparse version of the library, ATG-VS identifies the sections of the ultra-large chemical space that harbors the highest potential to engage the target site, leading to substantially reduced computational costs by up to a factor of 1000.

## **Error Robustness**

AdaptiveFlow is relatively robust regarding unexpected errors and interruptions, which often occur on computer clusters.&#x20;

## **Cluster Configuration**

AdaptiveFlow runs out-of-the-box Slurm clusters as well as AWS Batch clusters. The software can use almost any hardware configuration regarding the number of cores/CPUs, the number of sockets, the number of nodes, etc.&#x20;

## **Supported Batch system**

AdaptiveFlow currently supports the following batch system out of the box:

* SLURM
* AWS Batch (running in AWS)

## **Monitoring**

The workflow can be monitored in real-time in different ways during the execution. This allows to track the progress of the workflow, as well as to examine possible problems during or after the runtime:

* Real-time log files
* Using afvs\_get\_status.py (only AWS Batch at the moment)

## **Highly Automatized**

AdaptiveFlow can run fully automatically for any duration of time until it has processed all ligands specified in the input files.

## **Convenient Input and Output Formats**

The input and output ligand databases consist of hierarchical multilevel tar.gz-archives which are compressed. This compact format allows to easily handle vast amounts of ligands in an efficient and scalable manner.

## **Free & Libre Software**

AdaptiveFlow is licensed under the GNU GPL v2.0. Moreover, it is available at no costs. (The two terms of _free/libre_ software and open _source software_ are two different, but closely related concepts, see for instance [here](https://www.gnu.org/philosophy/open-source-misses-the-point.en.html).)



