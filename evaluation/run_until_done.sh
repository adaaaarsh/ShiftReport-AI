#!/bin/zsh
# Re-run a judge until its output folder holds the target number of results.
# Free tiers have daily caps; judge.py stops cleanly at a cap and skips finished reports, so we
# just wait an hour and try again. Gives up after 72 tries (about 3 days).
# Usage: ./run_until_done.sh <judge-id> <output-folder-name> <target-count> <log-name>
cd "${0:A:h}"
judge=$1 dir=outputs/judge/$2 target=$3 log=outputs/logs/$4.log
export PYTHONUNBUFFERED=1
for try in {1..72}; do
  n=$(ls $dir 2>/dev/null | wc -l | tr -d ' ')
  [[ $n -ge $target ]] && { echo "DONE $judge: $n/$target ($(date))" >> $log; exit 0; }
  echo "TRY $try $judge: $n/$target ($(date))" >> $log
  .venv/bin/python judge.py --judges $judge >> $log 2>&1
  n2=$(ls $dir 2>/dev/null | wc -l | tr -d ' ')
  [[ $n2 -ge $target ]] || sleep 3600
done
echo "GAVE UP $judge after 72 tries" >> $log; exit 1
