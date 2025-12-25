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
# Description: Slurm job file.
#
# Revision history:
# 2022-07-21  Original version
#
# ---------------------------------------------------------------------------

# Update the SBATCH section if needed for your particular Slurm
# installation. If a line starts with "##" (two #s) it will be 
# ignored

#SBATCH --job-name={{job_letter}}-{{workunit_id}}
#SBATCH --array {{array_start}}-{{array_end}}%{{slurm_array_job_throttle}}
##SBATCH --time=00-12:00:00
##SBATCH --mem-per-cpu=800M
##SBATCH --nodes=1
#SBATCH --cpus-per-task={{slurm_cpus}}
##SBATCH --partition={{slurm_partition}}
#SBATCH --output={{batch_workunit_base}}/%A_%a.out
#SBATCH --error={{batch_workunit_base}}/%A_%a.err
#SBATCH --account={{slurm_account}}


# If you are using a virtualenv, make sure the correct one 
# is being activated

source $HOME/afvs_env/bin/activate


# Job Information -- generally nothing in this
# section should be changed
##################################################################################

export AFVS_WORKUNIT={{workunit_id}}
export AFVS_JOB_STORAGE_MODE="{{ job_storage_mode }}"
export AFVS_CONFIG_JOB_BUCKET="{{ job_bucket }}"
export AFVS_CONFIG_JOB_OBJECT="{{ job_tgz }}"
export AFVS_WORKUNIT_SUBJOB=$SLURM_ARRAY_TASK_ID
export AFVS_TMP_PATH=/dev/shm
export AFVS_TOOLS_PATH=${PWD}/bin
export AFVS_VCPUS={{threads_to_use}}

##################################################################################

date +%s > {{batch_workunit_base}}/${AFVS_WORKUNIT_SUBJOB}.start
./templates/afvs_run.py
date +%s > {{batch_workunit_base}}/${AFVS_WORKUNIT_SUBJOB}.end



