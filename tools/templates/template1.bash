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


# Job Information -- generally nothing in this
# section should be changed
##################################################################################

export AFVS_WORKUNIT={{workunit_id}}
export AFVS_JOB_STORAGE_MODE={{job_storage_mode}}
export AFVS_TMP_PATH=/dev/shm
export AFVS_CONFIG_JOB_TGZ={{job_tgz}}
export AFVS_TOOLS_PATH=${PWD}/bin
export AFVS_VCPUS={{threads_to_use}}

##################################################################################

for i in `seq 0 {{array_end}}`; do
	export AFVS_WORKUNIT_SUBJOB=${i}
	echo "Workunit ${AFVS_WORKUNIT}:${AFVS_WORKUNIT_SUBJOB}: output in {{batch_workunit_base}}/${AFVS_WORKUNIT_SUBJOB}.out"
	date +%s > {{batch_workunit_base}}/${AFVS_WORKUNIT_SUBJOB}.start
	./templates/afvs_run.py &> {{batch_workunit_base}}/${AFVS_WORKUNIT_SUBJOB}.out
	date +%s > {{batch_workunit_base}}/${AFVS_WORKUNIT_SUBJOB}.end
done
