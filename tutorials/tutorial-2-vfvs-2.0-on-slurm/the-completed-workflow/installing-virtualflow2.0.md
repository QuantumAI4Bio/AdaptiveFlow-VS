# Installing VirtualFlow2.0

After you have logged in to your compute node, begin by cloning the vfvs-2 branch and enter the newly created directory: \


`git clone -b vfvs-2 https://github.com/VirtualFlow/VFVS/`

`cd VFVS`

Create and activate a python virtual environment (all work should be done inside the virtual env):\
\
`python3 -m virtualenv $HOME/vfvs_env` \
`source $HOME/vfvs_env/bin/activate`

Install various packages needed for VirtualFlow2.0:\
\
`python3 -m pip install boto3 pandas pyarrow jinja2`

After installation is complete, install AWS-CLI: \
\
First, let's make sure that no prior version of AWS-CLI is installed:\
\
`sudo apt-get remove awscli`

Next, download the archive:\
\
`curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"`\
\
When finished, simply unzip the archive: \
\
`unzip awscliv2.zip`\
\
and install: \
\
`sudo ./aws/install`\
\
To check that your installation is successful, you can run: \
\
`aws --version`

The above command should generate an output similar to: \
\
`aws-cli/2.15.1 Python/3.11.6 Linux/5.15.0-1031-gcp exe/x86_64.ubuntu.22 prompt/off`\
\
Next you must configure AWS-CLI:\
\
`aws configure`\
\
You have to define the following (the keys should match the ones you use in your local version of aws-cli):&#x20;

`AWS Access Key ID [None]:`\
`AWS Secret Access Key [None]:`\
`Default region name [None]: us-east-2`\
`Default output format [None]:`\
\
Congratulations, you now have a fully configured version of VF2.0! We will now proceed to the next step, setting up a docking run.



\
