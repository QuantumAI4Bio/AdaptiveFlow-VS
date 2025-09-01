# Monitoring the ATG Prescreen

The workflow on AWS can be monitored by the following command:

```
./vfvs_get_status.py 
```

This command currently only works for AWS, but not yet the Slurm version of AFVS.&#x20;

If a significant number of dockings failed, then something went wrong, and the problem needs to be resolved and the workflow prepared and run again.&#x20;

The ATG Prescreen is complete when all workunits have been successfully completed.&#x20;
