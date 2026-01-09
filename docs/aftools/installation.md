# Installation

## AFTools

The AFTools package can be installed anywhere on the system. This can be done by going to the desired installation directory, and then by downloading the archive from the GitHub repository:

```
wget https://github.com/LigandUniverse/AFTools/archive/master.tar.gz
```

Afterward, it can be extracted:

```
tar -xvzf master.tar.gz
mv AFTools-master AFTools
```

The executable files of AFTools are located in the folder `AFTools/bin/`

To make these commands more conveniently available, one can include the directory into the Linux PATH variable:

```
export PATH="<parent folder>/AFTools/bin:$PATH"
```

where `<parent folder>` is the folder in which the AFTools folder is located. To make the above change of the PATH variable permanent (enduring restarts) and global (available in any newly started terminal), it can be placed at the end of the `~/.bashrc` file in the home directory.

## OpenBabel

AFLP requires OpenBabel to be installed, as it uses the command obabel command of this package.

OpenBabel can be installed locally in the home directory, or by system admins globally, or might be available as a module on the computer cluster. This information can be found often on the website of the computer cluster. If it is not installed, then contacting the admins of the cluster often is the way to go forward, since it is usually quite simple for them to install the package on the cluster.

The critical thing is that the `obabel` command is in the PATH and thus executable from anywhere.
