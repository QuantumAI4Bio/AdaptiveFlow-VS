# Setting up the ATG Prescreen&#x20;

## Going to the AdaptiveFlow Working Directory

In order to set up the workflow, go to the folder `AFVS/tools` This is the working directory of AdaptiveFlow, where all the commands to run the software are started. Enter the following command to go to this folder:

```
cd AFVS/tools
```

## Preparing the `all.ctrl` Configuration File

From the `tools` folder, go to the `templates` folder. Enter the following command:

```
cd templates/
```

In the `templates` folder, there is a file called `all.ctrl`. Enter the following command to make sure it is there:

```
ls
```

The file `all.ctrl` needs to be edited.  It needs to be edited according to the cluster/batch system that will be used. There are two possible options for cluster/batch systems: Slurm and AWS Batch. This tutorial will focus on AWS Batch.&#x20;

To edit the `all.ctrl` file in the command line, use a command line editor. The two common editors are `nano` or `vim`. To use vim, enter the following command:

```
vim all.ctrl
```

This command will show the contents of the `all.ctrl` file within the command line interface. To continue editing the `all.ctrl` file in `vim`, please refer to other resources to learn specific `vim` editor commands. The following instructions require you to be comfortable with editing a file using a command line editor.&#x20;

All the options for editing are documented in the `all.ctrl` file itself. Edit the following portions of the preconfigured file:

* **object\_store\_data\_bucket**\
  Bucket name for the input collection data. In this tutorial, we use the Enamine REAL Space with 69B molecules. To obtain  the bucket, you need to request access on the following page of the AdaptiveFlow homepage (at the bottom of the page): [https://adaptiveflow.org/real-space-2022q12](https://adaptiveflow.org/real-space-2022q12)\
  \
  After registration, you will receive an email typically within one working day, with the access information. Please note that an AWS Account is needed to get access to the library. If you do not have an AWS account, you might want to create one. Access to the library is free, and there are no costs associated with downloading/accessing it via AWS.&#x20;
* **object\_store\_job\_bucket**\
  The bucket of your AWS account where you want the output data to be stored. If you don't have an S3 bucket yet, you will need to create one in your AWS Account. More information can be found here: [https://aws.amazon.com/s3/](https://aws.amazon.com/s3/)&#x20;

## Preparing the `workflow` Folder

Once the `all.ctrl` has been edited, return back to the `tools` directory. Enter the following command:

```
cd ..
```

All other files required to start the AdaptiveFlow Workflow are already set up. Further information on these other preconfigured files can be found in the [documentation](https://app.gitbook.com/o/-LNuBCz49KX3ym-BKSfI/s/-LNuBCz54OweSMdPmK2T/).&#x20;

To prepare the `workflow` and `output-files` folders, enter the following command:

```
./afvs_prepare_folders.py
```

**Warning**: If you have previously set up the `workflow` and `output-files` folders in this directory then the above command will let you know that it already exists. If you are sure you want to delete the existing data, then run with `--overwrite`.

Note that when you run the above command the workflow is set up using the state of `all.ctrl` and `todo.all` at that time. Changes to those files in the `tools/templates` folder after this point will not be used by the workflow unless `afvs_prepare_folders.py` is run again before the workflow is started.&#x20;

AFVS can process billions of ligands, and in order to process these efficiently it is helpful to segment this work into smaller chunks. A work unit is a segment of work that contains many 'subjobs' that are the actual execution elements. Often a work unit will have many subjobs and each subjob will contain about 60 minutes worth of computation.&#x20;

After preparing the folders in the previous section, the Workflow can be initiated with the following sequence of commands. First, enter the following command:

```
./afvs_prepare_workunits.py
```

Pay attention to how many work units are generated. The **final line of output** of the above command (displayed in the command line interface) will provide **the number of work units** generated.

Then we need to prepare the docker images:

```
./afvs_build_docker.sh
```

It can happen that this command requires to be run as root, depending on your specific setup. Please try `sudo ./afvs_build_docker.sh` in case the above command fails.&#x20;
