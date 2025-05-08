# genproductions
Generator fragments for MC production

The package includes the datacards used for various generators inclusing POWHEG, MG5_aMC@NLO, Sherpa, Phantom, Pythia...

Further details are reported in the twiki: https://twiki.cern.ch/twiki/bin/view/CMS/GeneratorMain#How_to_produce_gridpacks

Instructions on how to use the fragments are here https://twiki.cern.ch/twiki/bin/view/CMS/GitRepositoryForGenProduction

# Producing Custom SMEFTsim Samples with MadGraph

This guide walks you through generating gridpacks using a custom SMEFTsim model in MadGraph5_aMC@NLO.

## Requirements

- A CMS-compatible environment (e.g. Singularity container via `cmssw-cc7`)
- Access to the CMS `genproductions` repository
- A patched SMEFTsim UFO model (e.g. `SMEFTsim_topU3l_MwScheme_UFO_ctGpatched`)

## Instructions

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

## Notes

- Make sure `TT01j2lCARef_run_card.dat`, `TT01j2lCARef_proc_card.dat`, and optionally `TT01j2lCARef_madspin_card.dat` are present in the specified card directory.
- MadGraph will automatically use the `madspin_card.dat` if present and compatible with the process.
- Ensure that your model UFO is compatible with the version of MadGraph you are using.


