#!/usr/bin/env python3
"""
Create many independent SLURM cmsRun NanoGEN jobs from gridpack tarballs.

Python 3.6 compatible.

Key protections/debugging:
  - one unique scratch RUNDIR per SLURM job, so ExternalLHEProducer's lheevent
    directory cannot collide across jobs
  - verbose bash tracing and environment dumps
  - cmsRun exit code is preserved
  - on failure, copy useful scratch artifacts back to the persistent output dir

Dim6top-specific changes relative to the BSMRef version:
  - sample prefix: ttbbllnunu_dim6top
  - accepted WCs: ctG, ctGI, cQq38, cQq18, cQu8, cQd8, ctq8, ctu8, ctd8, cQq13, cQq11, cQu1, cQd1, ctq1, ctu1, ctd1
  - output dir: nanogen_outputs_gridpacks_ttbbllnunu_dim6top
  - job dir: slurm_nanogen_gridpacks_dim6top
"""

# python3 Make_SlurmJobs_nanogen_from_gridpacks_total_per_gridpack_ttbbllnunu_dim6top.py \
#   --gridpack-glob '/depot/cms/top/he614/cmseft/generation/genproductions/bin/MadGraph5_aMCatNLO/ttbbllnunu_dim6top_*_slc7_amd64_gcc700_CMSSW_10_6_19_tarball.tar.xz' \
#   --total-events-per-gridpack 500000 --events-per-job 25000 --debug

import argparse
import glob
import re
import shlex
import subprocess
from pathlib import Path

DEFAULT_BASE = Path('/depot/cms/top/he614/cmseft/generation')
DEFAULT_CMSSW = DEFAULT_BASE / 'CMSSW_10_6_27' / 'src'
DEFAULT_CFG = DEFAULT_BASE / 'nanogen_cfg.py'
DEFAULT_JOB_DIR = DEFAULT_BASE / 'slurm_nanogen_gridpacks_dim6top'
DEFAULT_OUT_DIR = DEFAULT_BASE / 'nanogen_outputs_gridpacks_ttbbllnunu_dim6top'
DEFAULT_SAMPLE_PREFIX = 'ttbbllnunu_dim6top'
DEFAULT_GRIDPACK_DIR = DEFAULT_BASE / 'genproductions' / 'bin' / 'MadGraph5_aMCatNLO'


def shquote(x):
    return shlex.quote(str(x))


def safe_tag_from_tarball(path):
    name = path.name
    name = re.sub(r'_slc7_amd64_gcc700_CMSSW_10_6_19_tarball\.tar\.xz$', '', name)
    name = re.sub(r'_tarball\.tar\.xz$', '', name)
    name = re.sub(r'\.tar\.xz$', '', name)
    return re.sub(r'[^A-Za-z0-9_.+-]+', '_', name)



def gridpack_name_is_allowed(path, sample_prefix):
    """Accept only exact ttbbllnunu_dim6top_<WC>_<point> tarballs."""
    tag = safe_tag_from_tarball(path)
    allowed_wcs = (
        'ctG', 'ctGI',
        'cQq38', 'cQq18', 'cQu8', 'cQd8', 'ctq8', 'ctu8', 'ctd8',
        'cQq13', 'cQq11', 'cQu1', 'cQd1', 'ctq1', 'ctu1', 'ctd1'
    )
    allowed_points = ('m4', 'm2', 'p0', 'p2', 'p4')
    pattern = re.compile(r'^' + re.escape(sample_prefix) + r'_(' + '|'.join(map(re.escape, allowed_wcs)) + r')_(' + '|'.join(allowed_points) + r')$')
    return bool(pattern.match(tag))


def expected_output_root(out_dir, tag, job_index):
    """Return the expected persistent NanoGEN ROOT path for one job."""
    work_dir = out_dir / tag / 'job_{0:04d}'.format(job_index)
    return work_dir / 'nanoGen_{0}_job{1:04d}.root'.format(tag, job_index)


def output_root_is_good(path, min_bytes=1):
    """True if expected ROOT output already exists and is non-empty."""
    try:
        return path.is_file() and path.stat().st_size >= int(min_bytes)
    except OSError:
        return False


def write_job(job_path, base_dir, cmssw_src, cfg_template, gridpack, out_dir,
              tag, job_index, events_per_job, cpu, mem, time, account,
              scram_arch, debug):
    work_dir = out_dir / tag / 'job_{0:04d}'.format(job_index)
    output_root = work_dir / 'nanoGen_{0}_job{1:04d}.root'.format(tag, job_index)
    cfg_out = work_dir / 'nanogen_{0}_job{1:04d}_cfg.py'.format(tag, job_index)
    log_out = work_dir / 'cmsRun_{0}_job{1:04d}.log'.format(tag, job_index)
    debug_dir = work_dir / 'debug'

    stable = sum((i + 1) * ord(c) for i, c in enumerate(tag)) % 800000000
    stable_lhe = sum((i + 1) * ord(c) for i, c in enumerate(tag + '_lhe')) % 800000000
    seed1 = 100000 + job_index + stable
    seed2 = 200000 + job_index + stable_lhe
    bash_trace = 'set -x' if debug else ':'

    job_text = f"""#!/bin/bash
#SBATCH -A {account}
#SBATCH --ntasks=1
#SBATCH --cpus-per-task={cpu}
#SBATCH --mem-per-cpu={mem}
#SBATCH --time={time}
#SBATCH --job-name=nanogen_{tag[:40]}_{job_index:04d}
#SBATCH --output={job_path.with_suffix('.%j.out')}
#SBATCH --error={job_path.with_suffix('.%j.err')}

{bash_trace}

WORK_DIR={shquote(work_dir)}
DEBUG_DIR={shquote(debug_dir)}
CFG_OUT={shquote(cfg_out)}
LOG_OUT={shquote(log_out)}
OUTPUT_ROOT={shquote(output_root)}

mkdir -p "$WORK_DIR" "$DEBUG_DIR"

if [[ -n "${{SLURM_TMPDIR:-}}" ]]; then
  RUNDIR="${{SLURM_TMPDIR}}/nanogen_${{SLURM_JOB_ID:-nojobid}}_{tag}_job{job_index:04d}"
else
  RUNDIR="/tmp/${{USER:-he614}}/nanogen_${{SLURM_JOB_ID:-nojobid}}_{tag}_job{job_index:04d}"
fi

cleanup_debug() {{
  status=$?
  echo "[DEBUG] cleanup status=$status"
  echo "[DEBUG] final PWD=$(pwd)"
  echo "[DEBUG] RUNDIR=$RUNDIR"
  echo "[DEBUG] WORK_DIR=$WORK_DIR"
  df -h . "$WORK_DIR" 2>/dev/null || true
  echo "[DEBUG] listing WORK_DIR"
  find "$WORK_DIR" -maxdepth 3 -type f -printf "%p %s bytes\\n" 2>/dev/null | sort || true
  if [[ -d "$RUNDIR" ]]; then
    echo "[DEBUG] listing RUNDIR top-level"
    find "$RUNDIR" -maxdepth 4 -type f -printf "%p %s bytes\\n" 2>/dev/null | sort | tail -200 || true
    mkdir -p "$DEBUG_DIR/rundir_snapshot"
    find "$RUNDIR" -maxdepth 5 -type f \\( \\
      -name "*.log" -o -name "*.txt" -o -name "*.dat" -o -name "*.cfg" -o \\
      -name "*.py" -o -name "*.err" -o -name "*.out" -o -name "run.sh" -o \\
      -name "MGGenerationInfo.txt" -o -name "*.xml" \\
    \\) -size -20M -exec cp --parents -f {{}} "$DEBUG_DIR/rundir_snapshot/" \\; 2>/dev/null || true
  fi
  echo "[DEBUG] end cleanup status=$status"
  exit $status
}}
trap cleanup_debug EXIT

cd {shquote(base_dir)}
echo "[INFO] PWD=$(pwd)"
echo "[INFO] HOST=$(hostname)"
echo "[INFO] DATE=$(date)"
echo "[INFO] SLURM_JOB_ID=${{SLURM_JOB_ID:-NA}}"
echo "[INFO] SLURM_TMPDIR=${{SLURM_TMPDIR:-NA}}"
echo "[INFO] USER=${{USER:-NA}}"
echo "[INFO] GRIDPACK={gridpack}"
echo "[INFO] EVENTS={events_per_job}"
echo "[INFO] OUTPUT_ROOT=$OUTPUT_ROOT"
echo "[INFO] CFG_OUT=$CFG_OUT"

ulimit -a || true
ulimit -c unlimited || true

export SCRAM_ARCH={scram_arch}
source /cvmfs/cms.cern.ch/cmsset_default.sh
cd {shquote(cmssw_src)}
eval `scram runtime -sh`
cd {shquote(base_dir)}

echo "[INFO] CMSSW_BASE=$CMSSW_BASE"
echo "[INFO] SCRAM_ARCH=$SCRAM_ARCH"
echo "[INFO] which cmsRun=$(command -v cmsRun || true)"
echo "[INFO] which python=$(command -v python || true)"
echo "[INFO] which python3=$(command -v python3 || true)"

mkdir -p "$WORK_DIR"
cp {shquote(cfg_template)} "$CFG_OUT"

cat >> "$CFG_OUT" <<'EOF_CFG_OVERRIDE'

# ============================================================
# Per-job overrides appended by Make_SlurmJobs_nanogen_from_gridpacks.py
# ============================================================
process.externalLHEProducer.args = cms.vstring('{gridpack}')
process.externalLHEProducer.nEvents = cms.untracked.uint32({events_per_job})
process.maxEvents.input = cms.untracked.int32({events_per_job})
process.NANOAODGENoutput.fileName = cms.untracked.string('file:{output_root}')

if not hasattr(process, 'RandomNumberGeneratorService'):
    process.RandomNumberGeneratorService = cms.Service('RandomNumberGeneratorService')
process.RandomNumberGeneratorService.generator = cms.PSet(
    initialSeed = cms.untracked.uint32({seed1}),
    engineName = cms.untracked.string('HepJamesRandom')
)
process.RandomNumberGeneratorService.externalLHEProducer = cms.PSet(
    initialSeed = cms.untracked.uint32({seed2}),
    engineName = cms.untracked.string('HepJamesRandom')
)

# ============================================================
# Fixed EFT-point production: disable NanoAOD gen-weight table
# ============================================================
# These samples are generated directly at one EFT point, not from an LHE
# reweight scan.  The NanoGEN GenWeightsTableProducer can crash when it
# tries to interpret missing/irregular LHE reweight information from these
# fixed-point gridpacks.  Remove it from the NanoGEN sequence and drop any
# output commands referring to it.
try:
    if hasattr(process, 'genWeightsTable') and hasattr(process, 'nanogenSequence'):
        process.nanogenSequence.remove(process.genWeightsTable)
        print('[CFG] Removed genWeightsTable from process.nanogenSequence')
except Exception as _e:
    print('[CFG] genWeightsTable removal from nanogenSequence skipped:', _e)

try:
    if hasattr(process, 'genWeightsTable') and hasattr(process, 'nanoAOD_step'):
        process.nanoAOD_step.remove(process.genWeightsTable)
        print('[CFG] Removed genWeightsTable from process.nanoAOD_step')
except Exception as _e:
    print('[CFG] genWeightsTable removal from nanoAOD_step skipped:', _e)

try:
    _old_cmds = list(process.NANOAODGENoutput.outputCommands)
    process.NANOAODGENoutput.outputCommands = cms.untracked.vstring(
        [x for x in _old_cmds if 'genWeightsTable' not in x and 'genWeights' not in x]
    )
    print('[CFG] Removed genWeightsTable/genWeights output commands:',
          len(_old_cmds) - len(process.NANOAODGENoutput.outputCommands))
except Exception as _e:
    print('[CFG] genWeights output command cleanup skipped:', _e)

EOF_CFG_OVERRIDE

echo "[DEBUG] cfg override tail:"
tail -80 "$CFG_OUT"

rm -rf "$RUNDIR"
mkdir -p "$RUNDIR"
cd "$RUNDIR"
echo "[INFO] RUNDIR=$RUNDIR"
echo "[DEBUG] before cmsRun PWD=$(pwd)"
ls -al

set +e
cmsRun "$CFG_OUT" > "$LOG_OUT" 2>&1
cms_status=$?
set -e

echo "[INFO] cmsRun exit code=$cms_status"
echo "[DEBUG] cmsRun log tail:"
tail -200 "$LOG_OUT" || true

if [[ $cms_status -ne 0 ]]; then
  echo "[ERROR] cmsRun failed with exit code $cms_status"
  exit $cms_status
fi

if [[ ! -s "$OUTPUT_ROOT" ]]; then
  echo "[ERROR] Expected output ROOT missing or empty: $OUTPUT_ROOT"
  exit 90
fi

echo "[OK] Finished: $OUTPUT_ROOT"
"""
    job_path.write_text(job_text)
    job_path.chmod(0o755)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--gridpack-glob', default=None,
                        help='Glob matching the gridpack tarballs. Default is restricted to ttbbllnunu_dim6top_* tarballs.')
    parser.add_argument('--cfg-template', default=str(DEFAULT_CFG))
    parser.add_argument('--base-dir', default=str(DEFAULT_BASE))
    parser.add_argument('--cmssw-src', default=str(DEFAULT_CMSSW))
    parser.add_argument('--job-dir', default=str(DEFAULT_JOB_DIR))
    parser.add_argument('--out-dir', default=str(DEFAULT_OUT_DIR))
    parser.add_argument('--total-events-per-gridpack', type=int, default=20000,
                        help='Total NanoGEN events to produce for each gridpack.')
    parser.add_argument('--events-per-job', type=int, default=1000,
                        help='Maximum events per SLURM job.')
    parser.add_argument('--cpu', default='1')
    parser.add_argument('--mem', default='4000')
    parser.add_argument('--time', default='24:00:00')
    parser.add_argument('--account', default='cms')
    parser.add_argument('--scram-arch', default='slc7_amd64_gcc700')
    parser.add_argument('--sample-prefix', default=DEFAULT_SAMPLE_PREFIX,
                        help='Only accept tarballs named <sample-prefix>_<WC>_<m4|m2|p0|p2|p4>_...tar.xz')
    parser.add_argument('--debug', action='store_true',
                        help='Add bash set -x to generated jobs.')
    parser.add_argument('--missing-only', action='store_true',
                        help=('Only generate SLURM jobs whose expected output ROOT file '
                              'is missing or smaller than --min-output-bytes. Useful for '
                              'resubmitting failed/missing NanoGEN chunks without touching '
                              'completed jobs.'))
    parser.add_argument('--min-output-bytes', type=int, default=1,
                        help='Minimum file size for an existing output ROOT to count as complete.')
    parser.add_argument('--submit', action='store_true')
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()
    cmssw_src = Path(args.cmssw_src).resolve()
    cfg_template = Path(args.cfg_template).resolve()
    job_dir = Path(args.job_dir).resolve()
    out_dir = Path(args.out_dir).resolve()

    if not cfg_template.exists():
        raise FileNotFoundError('cfg template not found: {0}'.format(cfg_template))
    if not cmssw_src.exists():
        raise FileNotFoundError('CMSSW src not found: {0}'.format(cmssw_src))

    if args.gridpack_glob is None:
        args.gridpack_glob = str(DEFAULT_GRIDPACK_DIR / (args.sample_prefix + '_*_slc7_amd64_gcc700_CMSSW_10_6_19_tarball.tar.xz'))

    matched_gridpacks = sorted(Path(p).resolve() for p in glob.glob(args.gridpack_glob))
    gridpacks = [p for p in matched_gridpacks if gridpack_name_is_allowed(p, args.sample_prefix)]
    rejected_gridpacks = [p for p in matched_gridpacks if not gridpack_name_is_allowed(p, args.sample_prefix)]
    if rejected_gridpacks:
        print('[WARN] Ignored {0} tarballs not matching exact {1}_<WC>_<point> pattern'.format(
            len(rejected_gridpacks), args.sample_prefix
        ))
    if not gridpacks:
        raise RuntimeError('No allowed {0} gridpacks matched: {1}'.format(args.sample_prefix, args.gridpack_glob))

    job_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    runfile = job_dir / 'Runcms_Submit_NanoGEN_gridpacks.sh'

    if args.total_events_per_gridpack <= 0:
        raise ValueError('--total-events-per-gridpack must be positive')
    if args.events_per_job <= 0:
        raise ValueError('--events-per-job must be positive')

    event_chunks = []
    remaining = args.total_events_per_gridpack
    while remaining > 0:
        n_this = min(args.events_per_job, remaining)
        event_chunks.append(n_this)
        remaining -= n_this

    n_jobs = 0
    n_skipped_existing = 0
    missing_manifest = job_dir / 'missing_nanogen_jobs_manifest.txt'

    with runfile.open('w') as rf, missing_manifest.open('w') as mf:
        rf.write('#!/bin/bash\nset -e\n\n')
        mf.write('# tag job_index events expected_output_root gridpack\n')

        for gp in gridpacks:
            tag = safe_tag_from_tarball(gp)
            for j, events_this_job in enumerate(event_chunks):
                expected_root = expected_output_root(out_dir, tag, j)

                if args.missing_only and output_root_is_good(expected_root, args.min_output_bytes):
                    n_skipped_existing += 1
                    continue

                job_path = job_dir / 'SlurmJob_nanogen_{0}_job{1:04d}.sh'.format(tag, j)
                write_job(
                    job_path=job_path,
                    base_dir=base_dir,
                    cmssw_src=cmssw_src,
                    cfg_template=cfg_template,
                    gridpack=gp,
                    out_dir=out_dir,
                    tag=tag,
                    job_index=j,
                    events_per_job=events_this_job,
                    cpu=args.cpu,
                    mem=args.mem,
                    time=args.time,
                    account=args.account,
                    scram_arch=args.scram_arch,
                    debug=args.debug,
                )
                rf.write('sbatch {0}\n'.format(shquote(job_path)))
                mf.write('{0} {1:04d} {2} {3} {4}\n'.format(
                    tag, j, events_this_job, expected_root, gp
                ))
                n_jobs += 1
    runfile.chmod(0o755)

    print('[OK] Found gridpacks: {0}'.format(len(gridpacks)))
    print('[OK] Total events per gridpack: {0}'.format(args.total_events_per_gridpack))
    print('[OK] Max events per job: {0}'.format(args.events_per_job))
    print('[OK] Jobs per gridpack: {0}'.format(len(event_chunks)))
    print('[OK] Event chunks per gridpack: {0}{1}'.format(event_chunks[:5], ' ...' if len(event_chunks) > 5 else ''))
    print('[OK] Missing-only mode: {0}'.format('ON' if args.missing_only else 'OFF'))
    if args.missing_only:
        print('[OK] Existing completed outputs skipped: {0}'.format(n_skipped_existing))
        print('[OK] Minimum output bytes required: {0}'.format(args.min_output_bytes))
    print('[OK] Total SLURM jobs generated: {0}'.format(n_jobs))
    print('[OK] Job dir: {0}'.format(job_dir))
    print('[OK] Output dir: {0}'.format(out_dir))
    print('[OK] Missing/job manifest: {0}'.format(missing_manifest))
    print('[OK] Submit with: {0}'.format(runfile))

    if args.submit:
        subprocess.check_call([str(runfile)])


if __name__ == '__main__':
    main()
