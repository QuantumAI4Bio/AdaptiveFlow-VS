#!/usr/bin/env bash

# Copyright (C) 2019 Christoph Gorgulla
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
# Description: Google Cloud Batch task entrypoint.
#
#   Google Cloud Batch numbers the tasks of a job from zero. A workunit
#   whose subjob count exceeds gcp_batch_array_job_size is submitted as
#   several Batch jobs, each covering a consecutive window of subjobs, so
#   the task index alone does not identify the subjob. The submitter passes
#   the window's start as AFVS_SUBJOB_INDEX_OFFSET and this script adds the
#   two to recover the AFVS subjob ID.
#
# Revision history:
# 2026-11-18  Original version
#
# ---------------------------------------------------------------------------

set -euo pipefail

if [ -z "${BATCH_TASK_INDEX:-}" ]; then
	echo "BATCH_TASK_INDEX is not set; this entrypoint must run as a Google Cloud Batch task" >&2
	exit 1
fi

offset="${AFVS_SUBJOB_INDEX_OFFSET:-0}"

case "${BATCH_TASK_INDEX}" in
	''|*[!0-9]*)
		echo "BATCH_TASK_INDEX is not a non-negative integer: '${BATCH_TASK_INDEX}'" >&2
		exit 1
		;;
esac

case "${offset}" in
	''|*[!0-9]*)
		echo "AFVS_SUBJOB_INDEX_OFFSET is not a non-negative integer: '${offset}'" >&2
		exit 1
		;;
esac

export AFVS_WORKUNIT_SUBJOB=$(( BATCH_TASK_INDEX + offset ))

echo "AdaptiveFlow workunit ${AFVS_WORKUNIT:-unset} subjob ${AFVS_WORKUNIT_SUBJOB}" \
	"(task ${BATCH_TASK_INDEX} + offset ${offset}, attempt ${BATCH_TASK_RETRY_ATTEMPT:-0})"

df -h

cd /opt/af/tools/templates/
exec ./afvs_run.py
