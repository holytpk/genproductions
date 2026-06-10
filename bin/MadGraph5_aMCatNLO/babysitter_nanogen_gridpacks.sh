#!/usr/bin/env bash
##############################################################################
# Babysit NanoGEN SLURM submissions.
#
# Purpose:
#   Submit many generated SlurmJob_nanogen_*.sh scripts without exceeding a
#   maximum number of live SLURM jobs for the current user.
#
# Typical use:
#   cd /depot/cms/top/he614/cmseft/generation
#   nohup ./babysitter_nanogen_gridpacks.sh \
#     --job-dir /depot/cms/top/he614/cmseft/generation/slurm_nanogen_gridpacks \
#     --max-jobs 4500 \
#     --sleep 60 \
#     > babysitter_nanogen.log 2>&1 &
#
# Monitor:
#   tail -f babysitter_nanogen.log
#   watch -n 30 'cat babysitter_nanogen_progress.txt; squeue -u $USER | wc -l'
##############################################################################

set -u

JOB_DIR="/depot/cms/top/he614/cmseft/generation/slurm_nanogen_gridpacks"
MAX_JOBS=4500
THRESHOLD=4500
SLEEP_SECONDS=60
START_INDEX=1
DRYRUN=0
PROGRESS_FILE="babysitter_nanogen_progress.txt"
STATE_FILE="babysitter_nanogen_state.txt"
SUBMITTED_LOG="babysitter_nanogen_submitted_jobs.log"

usage() {
  cat <<USAGE
Usage: $0 [options]

Options:
  --job-dir DIR        Directory containing SlurmJob_nanogen_*.sh
                       default: ${JOB_DIR}
  --max-jobs N         Maximum live jobs allowed for current user
                       default: ${MAX_JOBS}
  --threshold N        Submission threshold. Usually same as --max-jobs
                       default: ${THRESHOLD}
  --sleep N            Seconds between queue checks
                       default: ${SLEEP_SECONDS}
  --start-index N      1-based index into sorted job list to start from
                       default: ${START_INDEX}
  --progress-file F    Progress file
                       default: ${PROGRESS_FILE}
  --state-file F       State file recording next index
                       default: ${STATE_FILE}
  --dryrun             Print submissions but do not call sbatch
  -h, --help           Show this help

Example:
  nohup $0 --job-dir /depot/cms/top/he614/cmseft/generation/slurm_nanogen_gridpacks --max-jobs 4500 > babysitter_nanogen.log 2>&1 &
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --job-dir)
      JOB_DIR="$2"; shift 2 ;;
    --max-jobs)
      MAX_JOBS="$2"; THRESHOLD="$2"; shift 2 ;;
    --threshold)
      THRESHOLD="$2"; shift 2 ;;
    --sleep)
      SLEEP_SECONDS="$2"; shift 2 ;;
    --start-index)
      START_INDEX="$2"; shift 2 ;;
    --progress-file)
      PROGRESS_FILE="$2"; shift 2 ;;
    --state-file)
      STATE_FILE="$2"; shift 2 ;;
    --dryrun)
      DRYRUN=1; shift ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "[ERROR] Unknown option: $1" >&2
      usage
      exit 1 ;;
  esac
done

if [[ ! -d "$JOB_DIR" ]]; then
  echo "[ERROR] JOB_DIR does not exist: $JOB_DIR" >&2
  exit 1
fi

mapfile -t JOB_FILES < <(find "$JOB_DIR" -maxdepth 1 -type f -name 'SlurmJob_nanogen_*.sh' | sort -V)
TOTAL_JOBS="${#JOB_FILES[@]}"

if [[ "$TOTAL_JOBS" -eq 0 ]]; then
  echo "[ERROR] No SlurmJob_nanogen_*.sh files found in $JOB_DIR" >&2
  exit 1
fi

# Resume behavior: if state file exists, use it unless --start-index was explicitly set.
# The state file stores the next 1-based index to submit.
if [[ -f "$STATE_FILE" && "$START_INDEX" -eq 1 ]]; then
  saved_index=$(cat "$STATE_FILE" 2>/dev/null || echo 1)
  if [[ "$saved_index" =~ ^[0-9]+$ ]] && [[ "$saved_index" -ge 1 ]]; then
    START_INDEX="$saved_index"
  fi
fi

count="$START_INDEX"

get_job_count() {
  squeue -h -u "$(whoami)" | wc -l
}

update_progress_bar() {
  local submitted=$(( count - 1 ))
  if [[ "$submitted" -gt "$TOTAL_JOBS" ]]; then
    submitted="$TOTAL_JOBS"
  fi
  local progress
  progress=$(awk "BEGIN {printf \"%.2f\", (${submitted}/${TOTAL_JOBS})*100}")
  local bar_length=50
  local filled_length=$(( (bar_length * submitted) / TOTAL_JOBS ))
  local empty_length=$(( bar_length - filled_length ))
  local filled_bar empty_bar
  filled_bar=$(printf "%0.s#" $(seq 1 "$filled_length" 2>/dev/null))
  empty_bar=$(printf "%0.s-" $(seq 1 "$empty_length" 2>/dev/null))
  {
    echo "|${filled_bar}${empty_bar}| ${progress}%  (${submitted} / ${TOTAL_JOBS})"
    echo "next_index=${count}"
    echo "job_dir=${JOB_DIR}"
    echo "last_update=$(date)"
    echo "live_jobs=$(get_job_count)"
  } > "$PROGRESS_FILE"
  echo "$count" > "$STATE_FILE"
}

submit_one() {
  local job_script="$1"
  local ts
  ts=$(date '+%Y-%m-%d %H:%M:%S')
  if [[ "$DRYRUN" -eq 1 ]]; then
    echo "[$ts] [DRYRUN] sbatch $job_script"
    echo "[$ts] DRYRUN $job_script" >> "$SUBMITTED_LOG"
  else
    echo "[$ts] [SUBMIT] $job_script"
    sbatch_output=$(sbatch "$job_script" 2>&1)
    sbatch_status=$?
    echo "[$ts] $sbatch_output  $job_script" >> "$SUBMITTED_LOG"
    echo "[$ts] [SBATCH] $sbatch_output"
    if [[ "$sbatch_status" -ne 0 ]]; then
      echo "[$ts] [ERROR] sbatch failed for $job_script" >&2
      return "$sbatch_status"
    fi
  fi
}

echo "[INFO] Starting NanoGEN babysitter"
echo "[INFO] USER=$(whoami)"
echo "[INFO] JOB_DIR=$JOB_DIR"
echo "[INFO] TOTAL_JOBS=$TOTAL_JOBS"
echo "[INFO] START_INDEX=$START_INDEX"
echo "[INFO] MAX_JOBS=$MAX_JOBS"
echo "[INFO] THRESHOLD=$THRESHOLD"
echo "[INFO] SLEEP_SECONDS=$SLEEP_SECONDS"
echo "[INFO] PROGRESS_FILE=$PROGRESS_FILE"
echo "[INFO] STATE_FILE=$STATE_FILE"
echo "[INFO] SUBMITTED_LOG=$SUBMITTED_LOG"
echo "[INFO] DRYRUN=$DRYRUN"

update_progress_bar

while [[ "$count" -le "$TOTAL_JOBS" ]]; do
  current_jobs=$(get_job_count)
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] live_jobs=${current_jobs}; next=${count}/${TOTAL_JOBS}"

  if [[ "$current_jobs" -lt "$THRESHOLD" ]]; then
    jobs_to_submit=$(( THRESHOLD - current_jobs ))
    if [[ "$jobs_to_submit" -gt $(( TOTAL_JOBS - count + 1 )) ]]; then
      jobs_to_submit=$(( TOTAL_JOBS - count + 1 ))
    fi

    echo "[INFO] Submitting up to $jobs_to_submit jobs this round"

    for ((i=0; i<jobs_to_submit && count<=TOTAL_JOBS; i++)); do
      job_script="${JOB_FILES[$(( count - 1 ))]}"
      if [[ -f "$job_script" ]]; then
        submit_one "$job_script" || true
      else
        echo "[WARN] Missing job script at index $count: $job_script" >&2
      fi
      count=$(( count + 1 ))
      update_progress_bar
    done
  fi

  if [[ "$count" -le "$TOTAL_JOBS" ]]; then
    sleep "$SLEEP_SECONDS"
  fi
done

update_progress_bar
echo "[OK] All jobs have been submitted."
