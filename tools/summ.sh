#!/bin/bash
# usage: tools/summ.sh <suffix> <world>...   key lines of finished runs
SUF=$1; shift
for n in "$@"; do
  f=/tmp/sitl_test/${n}${SUF}.log
  echo "#### $n"
  [ -f "$f" ] || { echo "(no log)"; continue; }
  grep -E '=== (SEARCH|DELIVER|FIND_RETURN|ALIGN_RETURN|CORRIDOR_RETURN|HOME_LAND)|RELEASED|COMPLETE|ABORT|mission exit|Traceback|skipping' "$f" | cut -c1-150
done
