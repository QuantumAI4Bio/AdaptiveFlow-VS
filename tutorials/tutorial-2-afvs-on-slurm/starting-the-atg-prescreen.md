# Starting the ATG Prescreen

Now we are ready to start the jobs using the `./afvs_submit_jobs.py` command. It is recommended to start by submitting a single work unit (job) to test whether all works well:

```
./afvs_submit_jobs.py 1 1
```

Afterward, the workflow can be monitored as described in the next section [monitoring-the-atg-prescreen.md](../tutorial-1-afvs-on-aws/monitoring-the-atg-prescreen.md "mention").

Once the first job is completed successfully, which might take 15-30 minutes, the remaining jobs can be submitted.&#x20;

```
./afvs_submit_jobs.py 2 439
```

Here we assumed that 439 is the number of work units (please see the previous section [setting-up-the-atg-prescreen.md](../tutorial-1-afvs-on-aws/setting-up-the-atg-prescreen.md "mention")on how you can obtain the correct number). The above command will submit all remaining work units that were prepared (2 to 439) in the previous section with the `afvs_prepare_workunits.py` command.&#x20;



