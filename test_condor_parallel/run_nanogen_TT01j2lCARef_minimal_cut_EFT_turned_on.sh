#!/bin/bash
echo "Starting job on $(date)"
echo "Running on: $(hostname)"
echo "Working directory: $(pwd)"

echo "Seed: ${NANOGEN_SEED:-unset}"
echo "Output local file: ${NANOGEN_OUTFILE:-unset}"

if [ ! -f CMSSW_10_6_26.tar.gz ]; then
    echo "Missing CMSSW_10_6_26.tar.gz in working directory"
    exit 10
fi

tar -xf CMSSW_10_6_26.tar.gz || exit 11
cd CMSSW_10_6_26/src || exit 12
export VO_CMS_SW_DIR=/cvmfs/cms.cern.ch
source $VO_CMS_SW_DIR/cmsset_default.sh || exit 13
eval "$(scramv1 runtime -sh)" || exit 14
cd - >/dev/null || exit 15

echo "Contents before cmsRun:"
ls -lh

cmsRun nanogen_TT01j2lCARef_minimal_cut_EFT_turned_on_cfg.py
exitcode=$?

echo "cmsRun exit code: $exitcode"
echo "Contents after cmsRun:"
ls -lh
echo "ROOT files in working directory:"
ls -lh *.root 2>/dev/null || echo "(none)"

echo "Job finished on $(date)"
exit $exitcode
