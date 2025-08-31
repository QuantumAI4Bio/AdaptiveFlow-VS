# Monitoring the ATG Prescreen

At present, the only way to monitor progress of jobs will be to check status through the [Slurm scheduler commands](https://slurm.schedmd.com/quickstart.html). This will be extended in the future to more natively track progress towards completion. Among the slurm commands for monitoring is the `squeue` command.&#x20;

All outputs for successful docking are stored within the `../output-files` folder.

For debugging, the slurm errors are contained within the `../workflow/workunits` folder.

If a significant number of dockings or jobs failed, then something went wrong, and the problem needs to be resolved and the workflow prepared and run again.&#x20;

The ATG Prescreen is complete when all workunits/jobs have been successfully completed.&#x20;
