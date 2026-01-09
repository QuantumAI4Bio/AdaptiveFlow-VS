# Running AdaptiveFlow in the Cloud

## **Introduction**

Due to its flexible architecture, AdaptiveFlow is able to not only run on Linux computer clusters and supercomputers, but also runs natively on cloud computing platforms such as

* Google Cloud Platform
* Amazon Web Services
* Microsoft Azure

This is due to the circumstance that AdaptiveFlow operates by using SLURM resource managers, and SLURM batch systems are able to run on many cloud computing platforms as the three mentioned above.

## **Google Cloud Platform (GCP)**

To run AdaptiveFlow on the Google Cloud Platform, we recommend to use the GCP version of the Slurm resource manager, which runs out of the box on the GCP. To get started with Slurm on the GCP, we recommend the following page:

* [https://cloud.google.com/blog/products/compute/hpc-made-easy-announcing-new-features-for-slurm-on-gcp](https://cloud.google.com/blog/products/compute/hpc-made-easy-announcing-new-features-for-slurm-on-gcp)

After the Slurm cluster is running on the GCP, one can use AdaptiveFlow as on any other Linux cluster.

For large-scale computations using many virtual machines, a fast shared cluster file system is needed. We recommend to use either [Lustre](https://cloud.google.com/blog/products/storage-data-transfer/introducing-lustre-file-system-cloud-deployment-manager-scripts) or [Elastifile](https://cloud.google.com/blog/products/storage-data-transfer/scale-storage-out-with-new-elastifile-cloud-file-service-for-gcp) for this purpose.

## Amazon Web Services (AWS)

To run AdaptiveFlow on Amazon Web Services, we recommend to use AWS ParallelCluster, which allows to run SGE, TORQE, and Slurm resource managers conveniently in on AWS. All three of them are supported by AdaptiveFlow, but we recommend to use Slurm, as it is most common and modern, and best supported resource manager. We recommend the following page to get started with AWS ParallelCluster.

* [https://aws.amazon.com/blogs/opensource/aws-parallelcluster/](https://aws.amazon.com/blogs/opensource/aws-parallelcluster/)

After the Slurm cluster is running on AWS, one can use AdaptiveFlow as on any other Linux cluster.

For large-scale computations using many virtual machines, a fast shared cluster file system is needed. We recommend to use [FSx for Lustre](https://aws.amazon.com/fsx/lustre/) for this purpose.
