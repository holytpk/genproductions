#!/bin/bash

# Configuration
NJOBS=5
EVENTS_PER_JOB=100000
CMSSW_TARBALL="CMSSW_10_6_26.tar.gz"
CFG_NAME="nanogen_TT01j2lCARef_noEFT_cfg.py"
EOS_DIR="root://eosuser.cern.ch//eos/user/l/lingqian/EFT_FullRun2"

# Create logs directory if not exists
mkdir -p logs

# Generate run_job.sh
cat << 'EOF' > run_job.sh
#!/bin/bash
SEED=$1
OUTNAME=$2

echo "Starting job with seed $SEED and output $OUTNAME"
tar -xf CMSSW_10_6_26.tar.gz
cd CMSSW_10_6_26/src || exit 1
export VO_CMS_SW_DIR=/cvmfs/cms.cern.ch
source $VO_CMS_SW_DIR/cmsset_default.sh
eval `scramv1 runtime -sh`
cd -

cmsRun nanogen_TT01j2lCARef_noEFT_cfg.py dummy $SEED $OUTNAME
xrdcp -f $OUTNAME $EOS_DIR/$OUTNAME
EOF
chmod +x run_job.sh

# Generate submit and condor files
for ((i=0; i<$NJOBS; i++)); do
    SEED=$((1000 + i))
    OUTFILE="nanogen_TT01j2lCARef_noEFT_${i}.root"

    cat << EOF > submit_job_${i}.sub
universe = vanilla
executable = run_job.sh
arguments = $SEED $OUTFILE
output = logs/job_${i}.out
error  = logs/job_${i}.err
log    = logs/job_${i}.log
transfer_input_files = $CFG_NAME, run_job.sh, $CMSSW_TARBALL
request_cpus = 1
request_memory = 2000M
+JobFlavour = "tomorrow"
queue 1
EOF

    echo "Submitting job $i with seed $SEED"
    condor_submit submit_job_${i}.sub
done
