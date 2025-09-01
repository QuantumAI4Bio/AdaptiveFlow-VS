# Installation of AFVS

## Setting up AWS Batch

AFVS on AWS uses an AWS Batch cluster and workload manager. Instructions on how to create the AWS Batch cluster, and how to access the AWS Batch login node can be found [here](https://github.com/AdaptiveFlow/AFVS/blob/afvs-2/README-AWS.md#getting-started-with-adaptiveflow) on the AFVS GitHub page.

{% hint style="info" %}
You will need to have an AWS Account. If you don't have one yet, you can create a free one here: [https://aws.amazon.com/](https://aws.amazon.com/)&#x20;
{% endhint %}

## Setting up SSH

To log in to the AWS Batch login node via ssh, follow the instructions [here](https://github.com/AdaptiveFlow/AFVS/blob/afvs-2/README-AWS.md#login-to-the-main-instance). You will land in the home directory of the AWS Batch login node.&#x20;

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
python3 -m pip install boto3 pandas pyarrow jinja2 ipython
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

After Python is set up, we can install AFVS. Normally this is done by cloning the GitHub repo, but for this tutorial, we provide a pre-configured folder for download. On the AWS Batch login node, you can download it by running the following command:

```
wget https://adaptiveflow.org/sites/adaptiveflow.org/files/tutorials/AFVS2_Tutorial1_Preconfigured_AWS_20240421.tar.gz
```

This preconfigured folder was prepared by:

* Cloning the GitHub repo (branch afvs-2)
* Adding the docking input files to the `input-files` folder
* Configuring the `all.ctrl` file. The following parameters are changed compared to the template file in the AFVS GitHub repo:
  * `job_name`
  * `docking_scenario_names`&#x20;
  * `docking_scenario_programs`
  * `docking_scenario_replicas`
  * `docking_scenario_batchsizes`

