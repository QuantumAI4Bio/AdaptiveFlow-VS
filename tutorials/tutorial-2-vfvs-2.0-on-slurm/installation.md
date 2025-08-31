# Installation of VFVS

## Choosing the Installation Location

After setting up access to the supercomputing cluster, open up the command line interface (terminal in Linux or macOS, Command Prompt in Windows). At the command line, follow the instructions of the specific supercomputing cluster being used to log in to connect to the supercomputing cluster. Typically `ssh` is used to connect to the login node of the Slurm cluster.&#x20;

Once logged into and interfacing with the supercomputing cluster, enter the following command:

```
pwd
```

This shows the current folder, also known as the directory, where you are located. The first step is to navigate to the appropriate directory in the supercomputing cluster workspace where VirtualFlow will be installed.

VirtualFlow should be installed on **a fast shared scratch file system** rather than the home directory. The reasoning behind this and further information regarding the installation of VirtualFlow can be found within the "VirtualFlow" subsection located in the "[Installation](https://docs.virtual-flow.org/documentation/-LdE8RH9UN4HKpckqkX3/installation/vflp#installation-location)" section of the [documentation](https://app.gitbook.com/o/-LNuBCz49KX3ym-BKSfI/s/-LNuBCz54OweSMdPmK2T/).

After choosing the directory where you want VFVS and the workflow to be located, go to this directory. This can be done by entering the following command:

```
cd <installation directory>
```

Replace `<installation directory>`with the name of the folder (directory) that you chose.

## Setting up Python

VFVS requires Python 3.x (it has been tested with Python 3.9.4). Additionally, it requires packages to be installed that are not included at many sites. As a result, we recommend that you create a virtualenv for VFVS that can be used to run jobs.

Make sure that virtualenv is installed:

```
python3 -m pip install --user --upgrade virtualenv
```

Create a virtualenv (this example creates it under $HOME/vfvs\_env):

```
python3 -m virtualenv $HOME/vfvs_env
```

Enter the virtualenv and install needed packages

```
source $HOME/vfvs_env/bin/activate
python3 -m pip install boto3 pandas pyarrow jinja2
```

Alternatively, all the above steps can be performed using `conda` instead of `pip.` Further information on setting up a `conda` style environment can be found [here](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-with-commands).

To exit a virtual environment:

```
deactivate
```

When running VFVS commands, you should enter the virtualenv that you have set up using:

```
source $HOME/vfvs_env/bin/activate
```

Alternatively, all the above steps can be performed using `conda` instead of `pip.` Further information on setting up a `conda` style environment can be found [here](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-with-commands).

For the remainder of the tutorial and for future use of VFVS, **please ensure the virtual environment is activated**.

## Installing VFVS 2.0

After Python is set up, we can install VFVS 2.0. Normally this is done by cloning the GitHub repo, but for this tutorial, we provide a pre-configured folder for download which is available here:

On the AWS Batch login node, you can download it by running the following command:

```
wget https://virtual-flow.org/sites/virtual-flow.org/files/tutorials/VFVS%202%20-%20Tutorial%201%20-%20Preconfigured%20-%20Slurm.tar.gz
```

This preconfigured folder was prepared by:

* Cloning the GitHub repo (branch vfvs-2)
* Adding the docking input files to the `input-files` folder
* Configuring the `all.ctrl` file. The following parameters are changed compared to the template file in the VFVS GitHub repo:
  * `job_name`
  * `batchsystem`
  * `job_storage_mode`
  * `docking_scenario_names`&#x20;
  * `docking_scenario_programs`
  * `docking_scenario_replicas`
  * `docking_scenario_batchsizes`



## Installation of the AWS CLI

For VFVS to be able to access the ligand libraries stored in AWS Open Data, we need to install the AWS-CLI.&#x20;

{% hint style="info" %}
You will need to have an AWS Account. If you don't have one yet, you can create a free one here: [https://aws.amazon.com/](https://aws.amazon.com/)&#x20;

You will also need to create access keys for your username, e.g. the root user: [https://docs.aws.amazon.com/IAM/latest/UserGuide/id\_root-user\_manage\_add-key.html](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_root-user_manage_add-key.html)&#x20;
{% endhint %}

First, let's make sure that no prior version of AWS-CLI is installed:

```
sudo apt-get remove awscli
```

Next, download the archive:

```
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
```

When finished, simply unzip the archive:&#x20;

```
unzip awscliv2.zip
```

and install:&#x20;

```
sudo ./aws/install
```

If you don't have sudo rights, you will need to ask the cluster admins to install it for you.&#x20;

To check that your installation is successful, you can run:&#x20;

```
aws --version
```

The above command should generate an output similar to:&#x20;

```
aws-cli/2.15.1 Python/3.11.6 Linux/5.15.0-1031-gcp exe/x86_64.ubuntu.22 prompt/off
```

Next, you must configure AWS-CLI:

```
aws configure
```

You have to define the following (the keys should match the ones you use in your local version of aws-cli):&#x20;

```
AWS Access Key ID [None]:
AWS Secret Access Key [None]:
Default region name [None]:us-east-2
Default output format [None]:
```

Congratulations, you now have a fully configured version of VF2.0! We will now proceed to the next step, setting up a docking run.
