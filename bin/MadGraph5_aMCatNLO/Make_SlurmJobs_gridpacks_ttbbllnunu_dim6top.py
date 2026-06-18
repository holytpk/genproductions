#!/usr/bin/env python3
"""
Create one SLURM job per dim6top gridpack command, matching the working BSMRef
parallel style:
  - command file contains only gridpack commands
  - each SLURM job cd's to the MadGraph directory
  - each SLURM job sets PRODHOME/SCRAM_ARCH/CMSSW_VERSION
  - no global flock / serialization
  - existing final tarballs are skipped by default for retry-only submission

Usage:
  python3 Make_SlurmJobs_gridpacks_ttbbllnunu_dim6top.py \
    --commands addons/cards/dim6top/generated_no_reweight/run_all_gridpacks.sh \
    --workdir /depot/cms/top/he614/cmseft/generation/genproductions/bin/MadGraph5_aMCatNLO \
    --job-dir slurm_gridpacks_dim6top \
    --debug
"""
from __future__ import print_function

import argparse
import os
import re
import shlex
import subprocess
from pathlib import Path

DEFAULT_WORKDIR = "/depot/cms/top/he614/cmseft/generation/genproductions/bin/MadGraph5_aMCatNLO"
DEFAULT_JOB_DIR = "slurm_gridpacks_dim6top"
DEFAULT_RUNFILE = "Runcms_Submit_Gridpacks.sh"
DEFAULT_COMMANDS = "addons/cards/dim6top/generated_no_reweight/run_all_gridpacks.sh"
DEFAULT_SAMPLE_PREFIX = "ttbbllnunu_dim6top"

DIM6TOP_WCS = (
    "ctG", "ctGI", "cQq38", "cQq18", "cQu8", "cQd8", "ctq8", "ctu8", "ctd8",
    "cQq13", "cQq11", "cQu1", "cQd1", "ctq1", "ctu1", "ctd1",
)
POINTS = ("m4", "m2", "p0", "p2", "p4")


def shquote(x):
    return shlex.quote(str(x))


def unique_path(path):
    path = Path(path)
    if not path.exists():
        return path
    stem = path.with_suffix("")
    suffix = path.suffix
    for i in range(1, 1000):
        candidate = Path(str(stem) + "_retry{:02d}".format(i) + suffix)
        if not candidate.exists():
            return candidate
    raise RuntimeError("Could not find unused filename derived from {}".format(path))


def expected_name_re(sample_prefix):
    return re.compile(
        r"^" + re.escape(sample_prefix) + r"_(" + "|".join(re.escape(x) for x in DIM6TOP_WCS) +
        r")_(" + "|".join(POINTS) + r")$"
    )


def read_gridpack_commands(commands_file, sample_prefix):
    commands = []
    name_re = expected_name_re(sample_prefix)
    for raw in Path(commands_file).read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "gridpack_generation" not in line:
            continue
        if line.startswith("set ") or line.startswith("export ") or "PRODHOME=" in line:
            raise RuntimeError("Command file contains environment setup: {}".format(line))
        try:
            parts = shlex.split(line)
        except ValueError:
            continue
        if len(parts) < 3:
            continue
        gridpack_name = parts[1]
        card_dir = parts[2]
        if not name_re.match(gridpack_name):
            continue
        if sample_prefix not in card_dir:
            continue
        commands.append(line)
    return commands


def tarball_for_name(workdir, name, scram_arch, cmssw_version):
    return Path(workdir) / "{}_{}_{}_tarball.tar.xz".format(name, scram_arch, cmssw_version)


def sanitize_job_name(name, idx):
    s = re.sub(r"[^A-Za-z0-9_.+-]+", "_", name)
    return (s[:55] + "_{:03d}".format(idx))[:60]


def write_job(job_path, idx, cmd, workdir, account, partition, cpu, mem, time,
              scram_arch, cmssw_version, debug):
    parts = shlex.split(cmd)
    name = parts[1] if len(parts) >= 2 else "gridpack_{:03d}".format(idx)
    trace = "set -x" if debug else ":"
    partition_line = "#SBATCH --partition={}".format(partition) if partition else ""
    text = """#!/usr/bin/env bash
#SBATCH -A {account}
{partition_line}
#SBATCH --ntasks=1
#SBATCH --cpus-per-task={cpu}
#SBATCH --mem-per-cpu={mem}
#SBATCH --time={time}
#SBATCH --job-name=gp_{jobname}
#SBATCH --output={out}
#SBATCH --error={err}

# Keep this close to the BSMRef working style: no global lock, one independent job.
# set -euo pipefail
{trace}

cd {workdir_q}

PRODHOME="$(pwd)"
export PRODHOME
SCRAM_ARCH="{scram_arch}"
CMSSW_VERSION="{cmssw_version}"
export SCRAM_ARCH CMSSW_VERSION

# Avoid inheriting interactive conda/compiler pollution.
conda deactivate 2>/dev/null || true
unset CONDA_PREFIX CONDA_DEFAULT_ENV CONDA_SHLVL || true
unset CC CXX FC F77 F90 CPP CFLAGS CXXFLAGS FFLAGS LDFLAGS || true
hash -r || true

echo "[INFO] HOST=$(hostname)"
echo "[INFO] DATE=$(date)"
echo "[INFO] PWD=$(pwd)"
echo "[INFO] PRODHOME=$PRODHOME"
echo "[INFO] SCRAM_ARCH=$SCRAM_ARCH"
echo "[INFO] CMSSW_VERSION=$CMSSW_VERSION"
echo "[RUN] {cmd_echo}"

{cmd}

status=$?
echo "[INFO] gridpack command exit code=$status"
exit $status
""".format(
        account=account,
        partition_line=partition_line,
        cpu=cpu,
        mem=mem,
        time=time,
        jobname=sanitize_job_name(name, idx),
        out=str(job_path.with_suffix(".%j.out")),
        err=str(job_path.with_suffix(".%j.err")),
        trace=trace,
        workdir_q=shquote(workdir),
        scram_arch=scram_arch,
        cmssw_version=cmssw_version,
        cmd_echo=cmd.replace('"', '\\"'),
        cmd=cmd,
    )
    job_path.write_text(text)
    job_path.chmod(0o755)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--commands", default=DEFAULT_COMMANDS)
    parser.add_argument("--workdir", "--prodhome", dest="workdir", default=DEFAULT_WORKDIR,
                        help="Absolute MadGraph5_aMCatNLO directory to cd into inside each SLURM job")
    parser.add_argument("--job-dir", default=DEFAULT_JOB_DIR)
    parser.add_argument("--runfile", "--submit-file", dest="runfile", default=DEFAULT_RUNFILE)
    parser.add_argument("--account", default="cms")
    parser.add_argument("--partition", default="")
    parser.add_argument("--cpu", default="8")
    parser.add_argument("--mem", default="4000")
    parser.add_argument("--time", default="24:00:00")
    parser.add_argument("--scram-arch", default="slc7_amd64_gcc700")
    parser.add_argument("--cmssw-version", default="CMSSW_10_6_19")
    parser.add_argument("--sample-prefix", default=DEFAULT_SAMPLE_PREFIX)
    parser.add_argument("--force-existing-gridpacks", action="store_true",
                        help="Also create jobs for commands whose final tarball already exists")
    parser.add_argument("--overwrite-jobs", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--submit", action="store_true")
    args = parser.parse_args()

    workdir = Path(args.workdir).resolve()
    commands_file = Path(args.commands)
    if not commands_file.is_absolute():
        commands_file = workdir / commands_file
    if not commands_file.exists():
        raise IOError("Missing commands file: {}".format(commands_file))

    commands = read_gridpack_commands(commands_file, args.sample_prefix)
    if not commands:
        raise RuntimeError("No dim6top gridpack_generation commands found in {}".format(commands_file))

    job_dir = workdir / args.job_dir
    job_dir.mkdir(parents=True, exist_ok=True)

    runfile = workdir / args.runfile
    if runfile.exists() and not args.overwrite_jobs:
        runfile = unique_path(runfile)

    written = 0
    skipped = 0
    with runfile.open("w") as rf:
        #rf.write("#!/usr/bin/env bash\nset -euo pipefail\n\n")
        for i, cmd in enumerate(commands):
            parts = shlex.split(cmd)
            name = parts[1]
            tarball = tarball_for_name(workdir, name, args.scram_arch, args.cmssw_version)
            if tarball.exists() and not args.force_existing_gridpacks:
                print("[SKIP existing gridpack] {}".format(tarball))
                skipped += 1
                continue
            job_path = job_dir / "SlurmJob_gridpack_{}_job{:03d}.sh".format(name, i)
            if job_path.exists() and not args.overwrite_jobs:
                job_path = unique_path(job_path)
            write_job(job_path, i, cmd, str(workdir), args.account, args.partition,
                      args.cpu, args.mem, args.time, args.scram_arch, args.cmssw_version, args.debug)
            rf.write("sbatch {}\n".format(shquote(job_path)))
            written += 1
    runfile.chmod(0o755)

    print("[OK] Read commands: {}".format(len(commands)))
    print("[OK] Skipped existing gridpacks: {}".format(skipped))
    print("[OK] Created SLURM jobs: {}".format(written))
    print("[OK] Job dir: {}".format(job_dir))
    print("[OK] Submit with: {}".format(runfile))
    print("[OK] Parallel BSMRef-style submission: no global flock/serialization.")

    if args.submit:
        subprocess.check_call([str(runfile)])


if __name__ == "__main__":
    main()
