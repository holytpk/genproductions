# genproductions
Generator fragments for MC production

The package includes the datacards used for various generators inclusing POWHEG, MG5_aMC@NLO, Sherpa, Phantom, Pythia...

Further details are reported in the twiki: https://twiki.cern.ch/twiki/bin/view/CMS/GeneratorMain#How_to_produce_gridpacks

Instructions on how to use the fragments are here https://twiki.cern.ch/twiki/bin/view/CMS/GitRepositoryForGenProduction

# Producing Custom SMEFTsim Samples with MadGraph

This guide walks you through generating gridpacks using a custom SMEFTsim model in MadGraph5_aMC@NLO, and producing NanoAODv9 samples with EFT weights using CMSSW.

## Requirements

- A CMS-compatible environment (e.g. Singularity container via `cmssw-cc7`)
- Access to the CMS `genproductions` repository
- A patched SMEFTsim UFO model (e.g. `SMEFTsim_topU3l_MwScheme_UFO_ctGpatched`)

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

Use Singularity (e.g. on LPC or CERN grid nodes):

```bash
cmssw-cc7
```

### 4. Make Gridpack Generation Script Executable

```bash
chmod 755 gridpack_generation.sh
```

### 5. Run the Gridpack Generation

```bash
./gridpack_generation.sh <card-prefix> <model-path>
```

For example:

```bash
./gridpack_generation.sh TT01j2lCARef addons/model/SMEFTsim_topU3l_MwScheme_UFO_ctGpatched
```

This command assumes you have the corresponding cards in:

```
addons/cards/SMEFTsim_topU3l_MwScheme_UFO_ctGpatched/TT01j2lCARef_*.dat
```

### Notes

- Make sure `TT01j2lCARef_run_card.dat`, `TT01j2lCARef_proc_card.dat`, and optionally `TT01j2lCARef_madspin_card.dat` are present in the specified card directory.
- MadGraph will automatically use the `madspin_card.dat` if present and compatible with the process.
- Ensure that your model UFO is compatible with the version of MadGraph you are using.

---

## Part 2: Produce EFT NanoAODv9 Samples with CMSSW

To generate NAOD files that include the EFT weights, you must use a patched CMSSW release with custom NanoAOD modifications:

### 1. Setup Environment and Base Release

```bash
cmsrel CMSSW_10_6_26
cd CMSSW_10_6_26/src
export SCRAM_ARCH=slc7_amd64_gcc700
cmsenv
```

### 2. Add and Patch NanoAOD

```bash
git cms-addpkg PhysicsTools/NanoAOD
cd PhysicsTools/NanoAOD/
git remote add eftfit https://github.com/GonzalezFJR/cmssw.git
git fetch eftfit
git cherry-pick c0901cfc459a8d5282ebb1bc74374903d29e3eee
git cherry-pick 4068e48b02b1fcb46949b3ebeac6a7b59062c2e0
git cherry-pick 76d0a24615c2b2b3aa7333c5aed5cc7bb6a7fd1d
```

### 3. Clone EFTGenReader

```bash
cd ../../
git clone https://github.com/TopEFT/EFTGenReader.git
```

### 4. Add NanoAODTools

```bash
cd PhysicsTools
git clone https://github.com/cms-nanoAOD/nanoAOD-tools.git NanoAODTools
```

### 5. Apply Custom Patches from mc_production

Clone the patch repo somewhere and replace the necessary files:

```bash
git clone https://github.com/hannahbnelson/mc_production.git
cd mc_production
cp nanogen_setup/GenWeightsTableProducer.cc ~/CMSSW_10_6_26/src/PhysicsTools/NanoAOD/plugins/GenWeightsTableProducer.cc
cp nanogen_setup/nanogen_cff.py ~/CMSSW_10_6_26/src/PhysicsTools/NanoAOD/python/nanogen_cff.py
cp nanogen_setup/globals_cff.py ~/CMSSW_10_6_26/src/PhysicsTools/NanoAOD/python/globals_cff.py
```

### 6. Compile Everything

```bash
cd ~/CMSSW_10_6_26/src
scram b -j 8
```

### Patch Summary
- `GenWeightsTableProducer.cc`: correctly reads EFT reweight points and supports DJR plots.
- `nanogen_cff.py`: aligns neutrino exclusion in GenJet definition with miniAOD.
- `globals_cff.py`: adds `mc_nMEPartonsFiltered` for DJR plotting support.

---

## Part 3: Generate NanoAOD with EFT Gridpack

### 1. Copy Your Gridpack Fragment

Create the appropriate directory and copy your fragment into place:

```bash
mkdir -p CMSSW_10_6_26/src/Configuration/GenProduction/python
cp pythia_fragment.py CMSSW_10_6_26/src/Configuration/GenProduction/python/pythia_fragment.py
```

> 🔧 **Reminder**: Edit the gridpack path in `pythia_fragment.py` to match the full path to your `.tar.xz` gridpack.

### 2. Run `cmsDriver.py` to Create the NanoGEN Config

```bash
cmsDriver.py Configuration/GenProduction/python/pythia_fragment.py \
  --python_filename nanogen_TT01j2lCARef_noEFT_cfg.py \
  --eventcontent NANOAODGEN \
  --customise Configuration/DataProcessing/Utils.addMonitoring \
  --datatier NANOAOD \
  --fileout file:nanogen_TT01j2lCARef_noEFT.root \
  --conditions 106X_upgrade2018_realistic_v4 \
  --beamspot Realistic25ns13TeVEarly2018Collision \
  --step LHE,GEN,NANOGEN \
  --geometry DB:Extended \
  --era Run2_2018 \
  --no_exec \
  --mc -n 500000 \
  --customise_commands "process.RandomNumberGeneratorService.externalLHEProducer.initialSeed=123; process.particleLevelSequence.remove(process.genParticles2HepMCHiggsVtx); process.particleLevelSequence.remove(process.rivetProducerHTXS); process.particleLevelTables.remove(process.HTXSCategoryTable)"
```

You can now run the generated config with:

```bash
cmsRun nanogen_TT01j2lCARef_noEFT_cfg.py
```

---

Hopefully this works. 



