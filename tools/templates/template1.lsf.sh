#!/usr/bin/env bash

# Copyright (C) 2019 Christoph Gorgulla
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# This file is part of AdaptiveFlow.
#
# AdaptiveFlow is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# AdaptiveFlow is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with AdaptiveFlow.  If not, see <https://www.gnu.org/licenses/>.

# ---------------------------------------------------------------------------
#
# Description: LSF job file.
#
# ---------------------------------------------------------------------------

# Update the BSUB section if needed for your particular LSF
# installation. If a line starts with "##" (two #s) it will be
# ignored

#BSUB -J {{job_letter}}-{{workunit_id}}[{{array_start}}-{{array_end}}]%{{lsf_array_job_throttle}}
#BSUB -q {{lsf_queue}}
#BSUB -n {{lsf_cpus}}
#BSUB -R "span[hosts=1]"
#BSUB -R "rusage[mem={{lsf_memory}}]"
#BSUB -W {{lsf_walltime}}
#BSUB -o {{batch_workunit_base}}/%J_%I.out
#BSUB -e {{batch_workunit_base}}/%J_%I.err

# If you are using a virtualenv/conda env, make sure the correct one
# is being activated

conda activate afvs_env

# Configure your AWS-CLI settings
export AWS_PROFILE=
export AWS_SHARED_CREDENTIALS_FILE=
export AWS_CONFIG_FILE=

# LSF job array indices start at 1, but AFVS subjobs are numbered
# starting at 0 -- shift down by one to match
AFVS_SUBJOB_INDEX=$((LSB_JOBINDEX - 1))

# Job Information -- generally nothing in this
# section should be changed
##################################################################################

export AFVS_WORKUNIT={{workunit_id}}
export AFVS_JOB_STORAGE_MODE={{job_storage_mode}}
export AFVS_WORKUNIT_SUBJOB=${AFVS_SUBJOB_INDEX}
export AFVS_TMP_PATH=/dev/shm
export AFVS_CONFIG_JOB_TGZ={{job_tgz}}
export AFVS_TOOLS_PATH=${PWD}/bin
export AFVS_VCPUS={{threads_to_use}}

##################################################################################

date +%s > {{batch_workunit_base}}/${AFVS_WORKUNIT_SUBJOB}.start
./templates/afvs_run.py
date +%s > {{batch_workunit_base}}/${AFVS_WORKUNIT_SUBJOB}.end
