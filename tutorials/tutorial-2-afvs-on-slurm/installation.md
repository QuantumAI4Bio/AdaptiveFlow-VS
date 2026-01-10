# Installation of AFVS

## Choosing the Installation Location

After setting up access to the supercomputing cluster, open up the command line interface (terminal in Linux or macOS, Command Prompt in Windows). At the command line, follow the instructions of the specific supercomputing cluster being used to log in to connect to the supercomputing cluster. Typically `ssh` is used to connect to the login node of the Slurm cluster.

Once logged into and interfacing with the supercomputing cluster, enter the following command:

```
pwd
```

This shows the current folder, also known as the directory, where you are located. The first step is to navigate to the appropriate directory in the supercomputing cluster workspace where AdaptiveFlow will be installed.

AdaptiveFlow should be installed on **a fast shared scratch file system** rather than the home directory. The reasoning behind this and further information regarding the installation of AdaptiveFlow can be found within the "AdaptiveFlow" subsection located in the "[Installation](installation.md)" section of the [documentation](https://app.gitbook.com/o/-LNuBCz49KX3ym-BKSfI/s/-LNuBCz54OweSMdPmK2T/).

After choosing the directory where you want AFVS and the workflow to be located, go to this directory. This can be done by entering the following command:

```
cd <installation directory>
```

Replace `<installation directory>`with the name of the folder (directory) that you chose.

## Setting up Python

AFVS requires Python 3.x (it has been tested with Python 3.9.4). Additionally, it requires packages to be installed that are not included at many sites. As a result, we recommend that you create a virtualenv for AFVS that can be used to run jobs.

Make sure that virtualenv is installed:

```
python3 -m pip install --user --upgrade virtualenv
```

Create a virtualenv (this example creates it under $HOME/afvs\_env):

```
python3 -m virtualenv $HOME/afvs_env
```

Enter the virtualenv and install needed packages

```
source $HOME/afvs_env/bin/activate
python3 -m pip install boto3 pandas pyarrow jinja2
```

Alternatively, all the above steps can be performed using `conda` instead of `pip.` Further information on setting up a `conda` style environment can be found [here](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-with-commands).

To exit a virtual environment:

```
deactivate
```

When running AFVS commands, you should enter the virtualenv that you have set up using:

```
source $HOME/afvs_env/bin/activate
```

Alternatively, all the above steps can be performed using `conda` instead of `pip.` Further information on setting up a `conda` style environment can be found [here](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-with-commands).

For the remainder of the tutorial and for future use of AFVS, **please ensure the virtual environment is activated**.

## Installing AFVS

After Python is set up, we can install AFVS. Normally this is done by cloning the GitHub repo, but for this tutorial, we provide a pre-configured folder for download which is available here:

On the AWS Batch login node, you can download it by running the following command:

```
wget https://adaptive-flow.ai/sites/adaptive-flow.ai/files/tutorials/AFVS%202%20-%20Tutorial%201%20-%20Preconfigured%20-%20Slurm.tar.gz
```

This preconfigured folder was prepared by:

* Cloning the [GitHub repo](https://github.com/LigandUniverse/AFVS/tree/develop)
* Adding the docking input files to the `input-files` folder
* Configuring the `all.ctrl` file. The following parameters are changed compared to the template file in the AFVS GitHub repo:
  * `job_name`
  * `batchsystem`
  * `job_storage_mode`
  * `docking_scenario_names`
  * `docking_scenario_programs`
  * `docking_scenario_replicas`
  * `docking_scenario_batchsizes`

## Installation of the AWS CLI

For AFVS to be able to access the ligand libraries stored in AWS Open Data, we need to install the AWS-CLI.

{% hint style="info" %}
You will need to have an AWS Account. If you don't have one yet, you can create a free one here: [https://aws.amazon.com/](https://aws.amazon.com/)

You will also need to create access keys for your username, e.g. the root user: [https://docs.aws.amazon.com/IAM/latest/UserGuide/id\_root-user\_manage\_add-key.html](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_root-user_manage_add-key.html)
{% endhint %}

First, let's make sure that no prior version of AWS-CLI is installed:

```
sudo apt-get remove awscli
```

Next, download the archive:

```
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
```

When finished, simply unzip the archive:

```
unzip awscliv2.zip
```

and install:

```
sudo ./aws/install
```

If you don't have sudo rights, you will need to ask the cluster admins to install it for you.

To check that your installation is successful, you can run:

```
aws --version
```

The above command should generate an output similar to:

```
aws-cli/2.15.1 Python/3.11.6 Linux/5.15.0-1031-gcp exe/x86_64.ubuntu.22 prompt/off
```

Next, you must configure AWS-CLI:

```
aws configure
```

You have to define the following (the keys should match the ones you use in your local version of aws-cli):

```
AWS Access Key ID [None]:
AWS Secret Access Key [None]:
Default region name [None]:us-east-2
Default output format [None]:
```

Congratulations, you now have a fully configured version of AdaptiveFlow! We will now proceed to the next step, setting up a docking run.
