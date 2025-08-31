# Local installation and deployment of HPC-toolkit

Extensive documentation for HPC-toolkit can be found at: \
\
`https://cloud.google.com/hpc-toolkit/docs/setup/configure-environment`\
\
Please consult the page before for further information.\
\
Clone the HPC-toolkit repository: \
\
`git clone git@github.com:GoogleCloudPlatform/hpc-toolkit.git`\
\
A local folder will be created. Use the cd command to enter the folder: \
\
`cd hpc-toolkit`\
\
and run `make`

Create a `.yaml` file (that contains the infrastructure you want to deploy). An example of a yaml file can be found below:&#x20;

Please pay special attention to editing the following: \
\
\- instance image (ensure that your image has `Python 3.9.x` or above) if you change the current value\
\- region and zone\
\- disk size and type for the controller and compute nodes \
\- disk size and type for the `Filestore` instance (optional)\
\- content of the startup script&#x20;

{% file src="../../.gitbook/assets/test_tutorial_gitbook.yaml" %}
Example of a .yaml file that can be used to define and deploy infrastructure
{% endfile %}

After you have made the desired changes to your yaml file, to deploy, simply run the following command: \
\
`./ghpc create test_tutorial_gitbook.yaml -l ERROR --vars project_id=your_project_ID`\
\
After the yaml file has been validated, you will be prompted to follow the terraform instructions to deploy your infrastructure, namely:\
\
`To deploy, run the following commands:` \
`terraform -chdir=hpc-ubuntu-2204/primary init` \
`terraform -chdir=hpc-ubuntu-2204/primary validate` \
`terraform -chdir=hpc-ubuntu-2204/primary apply`\
\
To destroy, simply use the following command: \
\
`terraform -chdir=hpc-ubuntu-2204/primary destroy -auto-approve`
