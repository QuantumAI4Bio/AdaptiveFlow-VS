---
description: 'First, we should download the tutorial files:'
---

# Screening the sparse library with AdaptiveFlow

wget https://adaptive-flow.ai/sites/adaptive-flow.ai/files/tutorials/AFVS\_GK.tar

Decompress the archive by using:\
\
`tar -xvf AFVS_GK.tar`

\
From the resulting folder, copy the following files to the AFVS folder:\
\
`cp -v -r ./AFVS_GK/input-files/qvina02_rigid_receptor1/ AFVS_GK/input-files/receptor/ ~/AFVS/input-files/`\
\
Upload the _Enamine\_REAL\_Space\_2022q12\_sparse.todo_ file, containing the sparse version of the AF library:\


{% file src="../../.gitbook/assets/Enamine_REAL_Space_2022q12_sparse.todo" %}

Next, we should copy the _Enamine\_REAL\_Space\_2022q12\_sparse.todo_ file to the AFVS folder, overwriting the todo.all file, using a command similar to the one below:\
\
`cp -v ~/Enamine_REAL_Space_2022q12_sparse.todo ./tools/templates/todo.all`\\

Next upload the _all.ctrl_ file:\
\\

{% file src="../../.gitbook/assets/all.ctrl" %}

and copy it to overwrite the file in the AFVS folder, using a command similar to the one below:\
\
`cp -v ~/all.ctrl ./tools/templates/all.ctrl`\
\
We are now ready to perform our screening campaign!\
\
Return to `/tools` folder and run:

`./afvs_prepare_folders.py` (with --overwrite if you retry)\
\
followed by:\
\
`./afvs_prepare_workunits.py`\
\
Depending on the number of generated workunits, adjust the numerical values in the following command:\
\
`./afvs_submit_jobs.py 1 2`\
\
Congratulations, your screen should now be running! You can monitor the status using 2 separate slurm commands, `sbatch` and `squeue`.
