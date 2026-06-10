#!/usr/bin/env python3
import os
import argparse
import shlex
import subprocess
from pathlib import Path

DEFAULT_WORKDIR = "/depot/cms/top/he614/cmseft/generation/genproductions/bin/MadGraph5_aMCatNLO"
DEFAULT_JOB_DIR = "cmsSlurmJobs_gridpack"
DEFAULT_RUNFILE = "Runcms_Submit_Gridpacks.sh"


def shquote(x):
    return shlex.quote(str(x))


def read_gridpack_commands(commands_file: Path):
    commands = []
    for raw in commands_file.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "gridpack_generation.sh" not in line:
            continue
        commands.append(line)
    return commands


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--commands", default="run_all_80_no_reweight_gridpacks.sh")
    parser.add_argument("--workdir", default=DEFAULT_WORKDIR,
                        help="Absolute MadGraph5_aMCatNLO directory to cd into inside each SLURM job.")
    parser.add_argument("--job-dir", default=DEFAULT_JOB_DIR)
    parser.add_argument("--runfile", default=DEFAULT_RUNFILE)
    parser.add_argument("--account", default="cms")
    parser.add_argument("--cpu", default="8")
    parser.add_argument("--mem", default="4000")
    parser.add_argument("--time", default="24:00:00")
    parser.add_argument("--scram-arch", default="slc7_amd64_gcc700")
    parser.add_argument("--cmssw-version", default="CMSSW_10_6_19")
    parser.add_argument("--submit", action="store_true")
    args = parser.parse_args()

    workdir = Path(args.workdir).resolve()
    commands_file = Path(args.commands)
    if not commands_file.is_absolute():
        commands_file = workdir / commands_file

    if not commands_file.exists():
        raise FileNotFoundError(f"Missing commands file: {commands_file}")

    commands = read_gridpack_commands(commands_file)
    if not commands:
        raise RuntimeError(f"No gridpack_generation.sh commands found in {commands_file}")

    job_dir = workdir / args.job_dir
    job_dir.mkdir(parents=True, exist_ok=True)

    runfile = workdir / args.runfile
    with runfile.open("w") as rf:
        rf.write("#!/usr/bin/env bash\n")
        rf.write("set -euo pipefail\n\n")

        for i, cmd in enumerate(commands):
            job_path = job_dir / f"SlurmJob_gridpack_{i:03d}.sh"
            with job_path.open("w") as sh:
                sh.write("#!/usr/bin/env bash\n")
                sh.write(f"#SBATCH -A {args.account}\n")
                sh.write("#SBATCH --ntasks=1\n")
                sh.write(f"#SBATCH --cpus-per-task={args.cpu}\n")
                sh.write(f"#SBATCH --mem-per-cpu={args.mem}\n")
                sh.write(f"#SBATCH --time={args.time}\n")
                sh.write(f"#SBATCH --job-name=gp_{i:03d}\n")
                sh.write(f"#SBATCH --output={job_dir}/gridpack_%j_{i:03d}.out\n")
                sh.write(f"#SBATCH --error={job_dir}/gridpack_%j_{i:03d}.err\n\n")

                #sh.write("set -euo pipefail\n\n")

                # Important: cd first, then define PRODHOME based on pwd.
                sh.write(f"cd {shquote(workdir)}\n\n")
                sh.write('PRODHOME="$(pwd)"\n')
                sh.write("export PRODHOME\n")
                sh.write(f'SCRAM_ARCH="{args.scram_arch}"\n')
                sh.write(f'CMSSW_VERSION="{args.cmssw_version}"\n')
                sh.write("export SCRAM_ARCH CMSSW_VERSION\n\n")

                # Avoid inheriting an interactive conda compiler/toolchain in gridpack jobs.
                sh.write("# Clean possible interactive environment pollution.\n")
                sh.write("conda deactivate 2>/dev/null || true\n")
                sh.write("unset CONDA_PREFIX CONDA_DEFAULT_ENV CONDA_SHLVL || true\n")
                sh.write("unset CC CXX FC F77 F90 CPP CFLAGS CXXFLAGS FFLAGS LDFLAGS || true\n")
                sh.write("hash -r\n\n")

                sh.write('echo "[INFO] HOST=$(hostname)"\n')
                sh.write('echo "[INFO] DATE=$(date)"\n')
                sh.write('echo "[INFO] PRODHOME=$PRODHOME"\n')
                sh.write('echo "[INFO] SCRAM_ARCH=$SCRAM_ARCH"\n')
                sh.write('echo "[INFO] CMSSW_VERSION=$CMSSW_VERSION"\n')
                sh.write(f'echo "[RUN] {cmd}"\n\n')

                sh.write(cmd + "\n")

            job_path.chmod(0o755)
            rf.write(f"sbatch {shquote(job_path)}\n")

    runfile.chmod(0o755)
    print(f"[OK] Created {len(commands)} SLURM jobs in: {job_dir}")
    print(f"[OK] Submit with: {runfile}")

    if args.submit:
        subprocess.check_call([str(runfile)])


if __name__ == "__main__":
    main()
