# External Packages

## Docking Programs

AdaptiveFlow supports many docking programs working on CPUs and GPUs. For some of the docking programs, the executable binary programs (for x86 the architecture) are included in the AFVS package, and thus don't need to to be installed (when x86 compatible compute nodes are used, which is normally the case). For other docking programs whose executable binary programs are not included in the AFVS package, an executable program needs to be put into the directory `/tools/bin.` Currently, the docking programs that are supported by AdaptiveFlow are listed below, with those require an external package highlighted in bold:

* [**AutoDock-GPU**](../supported-docking-programs-and-scoring-functions.md#autodock-gpu)
* [**AutoDock4/AutoDock-CPU**](../supported-docking-programs-and-scoring-functions.md#autodock4-autodock-cpu)
* [AutoDock-ZN](../supported-docking-programs-and-scoring-functions.md#autodock-zn)
* [AutoDockVina 1.2](../supported-docking-programs-and-scoring-functions.md#autodockvina-1.2)
* [AutoDockVina 1.1.2](../supported-docking-programs-and-scoring-functions.md#autodockvina-1.1.2)
* [**ADFR**](../supported-docking-programs-and-scoring-functions.md#adfr)
* [AutoDock Koto](../supported-docking-programs-and-scoring-functions.md#autodock-koto)
* [CovDock](../supported-docking-programs-and-scoring-functions.md#covdock)
* [GlideHTVS](../supported-docking-programs-and-scoring-functions.md#glidehtvs)
* [GlideSP](../supported-docking-programs-and-scoring-functions.md#glidesp)
* [GlideXP](../supported-docking-programs-and-scoring-functions.md#glidexp)
* [DOCK6.0](../supported-docking-programs-and-scoring-functions.md#dock6.0)
* [Flexx](../supported-docking-programs-and-scoring-functions.md#flexx)
* [**FitDock**](../supported-docking-programs-and-scoring-functions.md#fitdock)
* [**Gnina**](../supported-docking-programs-and-scoring-functions.md#gnina)
* [**GalaxyDock3**](../supported-docking-programs-and-scoring-functions.md#galaxydock3)
* [**GOLD**](../supported-docking-programs-and-scoring-functions.md#gold)
* [GWOVina](../supported-docking-programs-and-scoring-functions.md#gwovina)
* [**HDock**](../supported-docking-programs-and-scoring-functions.md#hdock)
* [idock](../supported-docking-programs-and-scoring-functions.md#idock)
* [**iGemDock**](../supported-docking-programs-and-scoring-functions.md#igemdock)
* [LeDock](../supported-docking-programs-and-scoring-functions.md#ledock)
* [**LigandFit**](../supported-docking-programs-and-scoring-functions.md#ligandfit)
* [LightDock](../supported-docking-programs-and-scoring-functions.md#lightdock)
* [**MDock**](../supported-docking-programs-and-scoring-functions.md#mdock)
* [**MCDock**](../supported-docking-programs-and-scoring-functions.md#mcdock)
* [Molegro](../supported-docking-programs-and-scoring-functions.md#molegro)
* [MpSDockZN](../supported-docking-programs-and-scoring-functions.md#mpsdockzn)
* [PSOVina](../supported-docking-programs-and-scoring-functions.md#psovina)
* [PLANTS](../supported-docking-programs-and-scoring-functions.md#plants)
* [QuickVina2](../supported-docking-programs-and-scoring-functions.md#quickvina2)
* [QuickVina-W](../supported-docking-programs-and-scoring-functions.md#quickvina-w)
* [**QuickVina-gpu**](../supported-docking-programs-and-scoring-functions.md#quickvina_gpu)
* [**QuickVina-W-gpu**](../supported-docking-programs-and-scoring-functions.md#quickvina-w-gpu)
* [rDock](../supported-docking-programs-and-scoring-functions.md#rdock)
* [Rosetta-Ligand](../supported-docking-programs-and-scoring-functions.md#rosetta-ligand)
* [RLDock](../supported-docking-programs-and-scoring-functions.md#rldock)
* [**SEED**](../supported-docking-programs-and-scoring-functions.md#seed)
* [SMINA](../supported-docking-programs-and-scoring-functions.md#smina)
* [VinaCarb](../supported-docking-programs-and-scoring-functions.md#vinacarb)
* [VinaXB16](../supported-docking-programs-and-scoring-functions.md#vinaxb16)
* [**Vina-Gpu**](../supported-docking-programs-and-scoring-functions.md#vina-gpu)
* [**Vina-Gpu-2.0**](../supported-docking-programs-and-scoring-functions.md#vina-gpu-2.0)

{% hint style="info" %}
The pre-compiled executables are the ones which are provided by the original creators of these programs. This means that the more efficient binaries might be obtained when recompiling them from the source code with settings optimized for the precise architecture which will be used.
{% endhint %}

When self-compiled binaries should be used by AFVS, the pre-compiled binaries in the `tools/bin` folder need to be replaced by the new binaries.

## Scoring functions

AdaptiveFlow supports various scoring functions which can be used to score and rank the compounds whose binding poses to the target have been docked by a docking program of interest. Currently, the following scoring functions that are supported by AdaptiveFlow are listed below, with those require an external package highlighted in bold:

* [NNScore2.0](../supported-docking-programs-and-scoring-functions.md#scoring-with-nnscore2.0)
* [**rf-score-vs**](../supported-docking-programs-and-scoring-functions.md#scoring-with-rf-score-vs)
* [smina](../supported-docking-programs-and-scoring-functions.md#scoring-with-smina)
* [**gnina**](../supported-docking-programs-and-scoring-functions.md#scoring-with-gnina)
* [AutoDock4](../supported-docking-programs-and-scoring-functions.md#scoring-with-autodock4)
* [Vinandro](../supported-docking-programs-and-scoring-functions.md#scoring-with-vinandro)
* [Vina](../supported-docking-programs-and-scoring-functions.md#scoring-with-vina)
