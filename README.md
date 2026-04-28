# genproductions
Generator fragments for MC production

The package includes the datacards used for various generators inclusing POWHEG, MG5_aMC@NLO, Sherpa, Phantom, Pythia...

Further details are reported in the twiki: https://twiki.cern.ch/twiki/bin/view/CMS/GeneratorMain#How_to_produce_gridpacks

Instructions on how to use the fragments are here https://twiki.cern.ch/twiki/bin/view/CMS/GitRepositoryForGenProduction

# Producing Custom SMEFTsim Samples with MadGraph

This guide walks you through generating gridpacks using a custom SMEFTsim model in MadGraph5_aMC@NLO, and producing NanoAODv9 samples with EFT weights using CMSSW.

## Requirements

- A CMS-compatible environment, such as a Singularity container via `cmssw-cc7`
- Access to the CMS `genproductions` repository
- A patched SMEFTsim UFO model, for example `SMEFTsim_topU3l_MwScheme_UFO_ctGpatched`

---

## Part 1: Generate Gridpacks with MadGraph

### 1. Clone the Genproductions Repository and Checkout the Correct Branch

```bash
git clone https://github.com/cms-sw/genproductions.git
cd genproductions
git checkout mg265UL
```

### 2. Enter the MadGraph Directory

```bash
cd bin/MadGraph5_aMCatNLO
```

### 3. Enter a Clean CMS Environment

Use Singularity, for example on LPC or CERN grid nodes:

```bash
cmssw-cc7
```

### 4. Make the Gridpack Generation Script Executable

```bash
chmod 755 gridpack_generation.sh
```

### 5. Run the Gridpack Generation

```bash
./gridpack_generation.sh <card-prefix> <model-path>
```

For example:

```bash
./gridpack_generation.sh TT01j2lCARef addons/cards/SMEFTsim_topU3l_MwScheme_UFO_ctGpatched/TT01j2lCARef/
```

This command assumes you have the corresponding cards in:

```text
addons/cards/SMEFTsim_topU3l_MwScheme_UFO_ctGpatched/TT01j2lCARef_*.dat
```

### Notes

- Make sure `TT01j2lCARef_run_card.dat`, `TT01j2lCARef_proc_card.dat`, and optionally `TT01j2lCARef_madspin_card.dat` are present in the specified card directory.
- For EFT reweighting, make sure the corresponding reweight card is also present.
- MadGraph will automatically use the `madspin_card.dat` if present and compatible with the process.
- Ensure that your model UFO is compatible with the version of MadGraph you are using.

---

## Part 2: Produce EFT NanoAODv9 Samples with CMSSW

For this section, it is convenient to install CMSSW in a directory parallel to `genproductions`. You may not need the Singularity container from this point onward.

To generate NanoGEN files that retain EFT information, use a patched CMSSW release with custom NanoAOD modifications.

### 1. Set Up the Base Release

```bash
cd ..
export SCRAM_ARCH=slc7_amd64_gcc700

source /cvmfs/cms.cern.ch/cmsset_default.sh
if [ -r CMSSW_10_6_42/src ] ; then
  echo release CMSSW_10_6_42 already exists
else
  scram p CMSSW CMSSW_10_6_42
fi

cd CMSSW_10_6_42/src
eval `scram runtime -sh`
```

### 2. Add the Packages That Will Be Modified

```bash
git cms-addpkg GeneratorInterface/Core
git cms-addpkg PhysicsTools/NanoAOD
```

### 3. Pull the GeneratorInterface Header Fixes From the Custom Branch

Use the custom branch at:

```text
https://github.com/holytpk/cmssw/tree/production-Run2-EFT
```

Fetch the branch and copy over the needed header files:

```bash
git remote add holytpk https://github.com/holytpk/cmssw.git
git fetch holytpk production-Run2-EFT

git checkout holytpk/production-Run2-EFT --   GeneratorInterface/Core/interface/ConcurrentHadronizerFilter.h   GeneratorInterface/Core/interface/HadronizerFilter.h
```

### 4. Pull the NanoAOD EFT Changes From Rezza / TopEFT

The NanoAOD EFT weight support is not fully available in a plain CMSSW checkout. First pull the required `PhysicsTools/NanoAOD` changes from Rezza's CMSSW fork. These are the same EFT NanoAOD changes used in the TopEFT / mgprod-style setup.

Run this from inside your CMSSW `src` area:

```bash
cd CMSSW_10_6_42/src
eval `scram runtime -sh`

# Make sure the package exists in your local CMSSW area.
git cms-addpkg PhysicsTools/NanoAOD

# Pull the EFT NanoAOD changes from Rezza / GonzalezFJR.
cd PhysicsTools/NanoAOD
git remote add rezza https://github.com/GonzalezFJR/cmssw.git || true
git fetch rezza

# These cherry-picks are the standard EFT NanoAOD patches.
git cherry-pick c0901cfc459a8d5282ebb1bc74374903d29e3eee
git cherry-pick 4068e48b02b1fcb46949b3ebeac6a7b59062c2e0
git cherry-pick 76d0a24615c2b2b3aa7333c5aed5cc7bb6a7fd1d

cd ../..
```

If a cherry-pick has already been applied, resolve or skip it in the usual git way:

```bash
git status
git cherry-pick --skip
```

The `GenWeightsTableProducer.cc` code also expects the EFT helper classes. Clone `EFTGenReader` inside the CMSSW `src` directory:

```bash
cd CMSSW_10_6_42/src
git clone https://github.com/TopEFT/EFTGenReader.git
```

### 5. Pull the NanoGEN Setup Files From Hannah's `mc_production` Repository

Hannah's repository contains the production-side cards, models, gridpack scripts, and NanoGEN setup helpers used for this workflow. Clone it next to `genproductions` and your CMSSW release:

```bash
cd /path/to/your/workdir
git clone https://github.com/hannahbnelson/mc_production.git
cd mc_production
```

The repository layout includes the relevant production directories:

```text
cards/
gridpacks/
models/
nanogen_setup/
setup_commands/ttbarEFT_Run2/
gridpack_generation.sh
```

Copy Hannah's NanoGEN setup files into your CMSSW area after the Rezza cherry-picks. At minimum, use her `GenWeightsTableProducer.cc` replacement if you want the validated NanoGEN EFT-weight behavior from this workflow:

```bash
cd /path/to/your/workdir/mc_production

cp nanogen_setup/GenWeightsTableProducer.cc \
  /path/to/your/workdir/CMSSW_10_6_42/src/PhysicsTools/NanoAOD/plugins/GenWeightsTableProducer.cc
```

If your checkout contains additional validated NanoGEN helper files under `nanogen_setup/`, inspect them and copy only the files that correspond to your CMSSW release and workflow. Useful checks before building:

```bash
cd /path/to/your/workdir/CMSSW_10_6_42/src
git diff -- PhysicsTools/NanoAOD/plugins/GenWeightsTableProducer.cc
git status --short
```

### 6. Apply or Verify the Local NanoAOD EFT Files

After pulling from Rezza and copying Hannah's NanoGEN setup file, verify that the following files are present and consistent in your CMSSW area:

```text
PhysicsTools/NanoAOD/plugins/GenWeightsTableProducer.cc
PhysicsTools/NanoAOD/python/globals_cff.py
PhysicsTools/NanoAOD/python/nanogen_cff.py
GeneratorInterface/Core/interface/ConcurrentHadronizerFilter.h
GeneratorInterface/Core/interface/HadronizerFilter.h
```

If you already have validated local working copies of these files, compare them with `git diff` before overwriting them.

The two required upstream steps are:

1. Pull / cherry-pick the EFT NanoAOD changes from Rezza / GonzalezFJR.
2. Pull Hannah's `mc_production` repository and copy the NanoGEN setup file(s), especially `nanogen_setup/GenWeightsTableProducer.cc`.

### 7. Build CMSSW

```bash
scram b -j 8
cd ../..
```

---

## Part 3: Generate NanoAOD With the EFT Gridpack

### 1. Copy Your Gridpack Fragment and Any Custom Config Inputs

Create the appropriate directory and copy the fragment from `genproductions` into place:

```bash
mkdir -p CMSSW_10_6_42/src/Configuration/GenProduction/python
cp pythia_fragment.py CMSSW_10_6_42/src/Configuration/GenProduction/python/pythia_fragment.py
```

Edit the gridpack path in `pythia_fragment.py` so it points to the full path of your `.tar.xz` gridpack.

If you are also using a custom NanoGEN cfg or patched helper files, make sure they are copied into the CMSSW area consistently before running `cmsDriver.py`.

### 2. Run `cmsDriver.py` to Create the NanoGEN Config

```bash
cd CMSSW_10_6_42/src
eval `scram runtime -sh`

cmsDriver.py Configuration/GenProduction/python/pythia_fragment.py   --python_filename nanogen_TT01j2lCARef_noEFT_cfg.py   --eventcontent NANOAODGEN   --customise Configuration/DataProcessing/Utils.addMonitoring   --datatier NANOAOD   --fileout file:nanogen_TT01j2lCARef_noEFT.root   --conditions 106X_upgrade2018_realistic_v4   --beamspot Realistic25ns13TeVEarly2018Collision   --step LHE,GEN,NANOGEN   --geometry DB:Extended   --era Run2_2018   --no_exec   --mc -n 500000   --customise_commands "process.RandomNumberGeneratorService.externalLHEProducer.initialSeed=123; process.particleLevelSequence.remove(process.genParticles2HepMCHiggsVtx); process.particleLevelSequence.remove(process.rivetProducerHTXS); process.particleLevelTables.remove(process.HTXSCategoryTable)"
```

You can then run the generated config with:

```bash
cmsRun nanogen_TT01j2lCARef_noEFT_cfg.py
```

With the patches above, NanoGEN should retain EFT-related branches such as `EFTfitCoefficients`, `WCnames`, and `LHEReweightingWeight` without removing `genWeightsTable`.

---

## Part 4: Running NanoGEN with HTCondor

After generating your config and setting up your environment, you can run your NanoGEN job on HTCondor using the following helper scripts.

Assume the output file is written directly to:

```python
process.TFileService.fileName = 'file:/eos/user/l/lingqian/nanogen_TT01j2lCARef_noEFT.root'
```

So there is no need for `xrdcp` in the wrapper script.

You may have the following files:

```text
nanogen_TT01j2lCARef_noEFT_cfg.py
nanogen_TT01j2lCARef_noEFT_production_log.out
run_nanogen_TT01j2lCARef_noEFT.sh
submit_nanogen_TT01j2lCARef_noEFT.sh
CMSSW_10_6_26.tar.gz
```

You can also try generating these scripts using `make_condor_scripts.py`.

### Step 1: Make a CMSSW Tarball

```bash
tar --exclude-caches-all --exclude-vcs -zcf CMSSW_10_6_26.tar.gz CMSSW_10_6_26
```

### Step 2: Generate Job Scripts

Save the following code as `make_condor_scripts.py` and run it to produce both `run_nanogen_TT01j2lCARef_noEFT.sh` and `submit_nanogen_TT01j2lCARef_noEFT.sh`.

```python
with open("run_nanogen_TT01j2lCARef_noEFT.sh", "w") as f:
    f.write("""#!/bin/bash
echo "Starting job on $(date)"
echo "Running on: $(uname -a)"
echo "System software: $(lsb_release -a)"

tar -xf CMSSW_10_6_26.tar.gz
export SCRAM_ARCH=slc7_amd64_gcc700
cd CMSSW_10_6_26/src
scram b ProjectRename
eval `scram runtime -sh`
cd -

cmsRun nanogen_TT01j2lCARef_noEFT_cfg.py > nanogen_TT01j2lCARef_noEFT_production_log.out
""")

with open("submit_nanogen_TT01j2lCARef_noEFT.sh", "w") as f:
    f.write("""universe = vanilla
executable = run_nanogen_TT01j2lCARef_noEFT.sh
arguments  =
output     = condor.out
error      = condor.err
log        = condor.log
transfer_input_files = CMSSW_10_6_26.tar.gz, nanogen_TT01j2lCARef_noEFT_cfg.py
should_transfer_files = yes
when_to_transfer_output = ON_EXIT
+JobFlavour = "tomorrow"
queue
""")
```

Then make the wrapper executable:

```bash
chmod +x run_nanogen_TT01j2lCARef_noEFT.sh
```

Submit with:

```bash
condor_submit submit_nanogen_TT01j2lCARef_noEFT.sh
```

This setup runs `cmsRun` using the provided config and writes the output NanoGEN file directly to your EOS path.

Using all the tips above, you can find a working example under the `test_condor_parallel` directory. Modify the gridpack path in `pythia_fragment.py`, then run:

```bash
condor_submit submit_nanogen_TT01j2l_SM.jdl
```

If you are submitting from EOS space, you might need the `--spool` option. Please refer to the `TT01j2lCARef_minimal_cut` scripts.

# Computation of Spin Correlation Observables From the GenPart Collection, Histogramming, and Plotting Stage

Please check the `spin_corr_process_all.py` and `spin_corr_plot_histogram.py` scripts. The Python environment dependencies are described in `python_environment_dependencies.txt`.
