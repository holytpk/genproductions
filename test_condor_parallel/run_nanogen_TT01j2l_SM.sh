#!/bin/bash
echo "Starting job on $(date)"
echo "Running on: $(hostname)"
echo "Working directory: $(pwd)"

echo "Seed: $NANOGEN_SEED"
echo "Output will be written to: $NANOGEN_OUTFILE"

# Check if output is on EOS
if [[ ! "$NANOGEN_OUTFILE" == /eos/* ]]; then
    echo "❌ Error: NANOGEN_OUTFILE must point to an /eos/ path."
    exit 1
fi

# Setup CMSSW
tar -xf CMSSW_10_6_26.tar.gz
cd CMSSW_10_6_26/src || exit 1
export VO_CMS_SW_DIR=/cvmfs/cms.cern.ch
source $VO_CMS_SW_DIR/cmsset_default.sh
eval `scramv1 runtime -sh`
cd -

# Make sure the output EOS directory exists
eosmkdir=$(dirname "$NANOGEN_OUTFILE" | sed 's|^/eos/||')
xrdfs root://eosuser.cern.ch mkdir -p "/${eosmkdir}"

# Run job — assumes output path is defined in cfg.py via $NANOGEN_OUTFILE
cmsRun nanogen_TT01j2l_SM_cfg.py
exitcode=$?

if [ $exitcode -eq 0 ]; then
    echo "✅ cmsRun completed successfully."
else
    echo "❌ cmsRun failed with exit code $exitcode"
fi

echo "Job finished on $(date)"
exit $exitcode
