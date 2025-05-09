# python make_condor_scripts.py TT01j2lCARef_noEFT
# - Ling May 9, 2025

import sys

template_run = """#!/bin/bash
set -e
echo "Starting job on $(date)"
echo "Running on: $(hostname)"
echo "System info: $(uname -a)"

source /cvmfs/cms.cern.ch/cmsset_default.sh
export SCRAM_ARCH=slc7_amd64_gcc700
cd ${{CMSSW_BASE}}/src
eval `scramv1 runtime -sh`

cd -
cmsRun nanogen_{proc}.py > nanogen_{proc}_production_log.out

# No xrdcp needed if output path is already set to EOS in cmsDriver config
"""

template_submit = """universe = vanilla
Executable = run_{proc}.sh
Output = job_{proc}.out
Error = job_{proc}.err
Log = job_{proc}.log
RequestMemory = 4000
+JobFlavour = "workday"
Queue
"""

if len(sys.argv) != 2:
    print("Usage: python make_condor_scripts.py <process_name>")
    sys.exit(1)

proc = sys.argv[1]

with open(f"run_{proc}.sh", "w") as fout:
    fout.write(template_run.format(proc=proc))

with open(f"submit_{proc}.sh", "w") as fout:
    fout.write(template_submit.format(proc=proc))

print(f"Generated run_{proc}.sh and submit_{proc}.sh")

