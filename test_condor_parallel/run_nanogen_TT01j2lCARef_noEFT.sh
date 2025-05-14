#!/bin/bash
echo "Starting job on $(date)"
echo "Running on: $(hostname)"
echo "Working directory: $(pwd)"

echo "Seed: $NANOGEN_SEED"
echo "Output: $NANOGEN_OUTFILE"

# Setup CMSSW
tar -xf CMSSW_10_6_26.tar.gz 
cd CMSSW_10_6_26/src || exit 1
export VO_CMS_SW_DIR=/cvmfs/cms.cern.ch
source $VO_CMS_SW_DIR/cmsset_default.sh
eval `scramv1 runtime -sh`
cd -

# Run job
cmsRun nanogen_TT01j2lCARef_noEFT_cfg.py

# Copy to EOS
xrdcp -f $OUTROOT root://eosuser.cern.ch//eos/user/l/lingqian/EFT_FullRun2/nanogen_TT01j2lCARef_noEFT_test/$OUTROOT

# Only remove local copy if transfer succeeded
if [ $? -eq 0 ]; then
    echo "xrdcp successful, removing local file $OUTROOT"
    rm -f $OUTROOT
else
    echo "xrdcp failed, not removing $OUTROOT"
fi

echo "Job finished on $(date)"
