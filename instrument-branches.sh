set -eux

ORIGINAL_BRANCH=$(git rev-parse --abbrev-ref HEAD)
ASPROF_CMD=${ASPROF_CMD:--agentpath:./build/lib/libasyncProfiler.so=start,timeout=10,collapsed,file=/dev/null,event=cpu,interval=10ms}
ASPROF_INSTRUMENTATION_BRANCH=instrumenting-asprof

git checkout $LEFT
git checkout -b tmp-$LEFT
trap "git checkout $ORIGINAL_BRANCH && git branch -D tmp-$LEFT" EXIT
git merge --no-edit $ASPROF_INSTRUMENTATION_BRANCH

OUTPUT_FILE_1=processed_traces_${LEFT}.txt

OUTPUT_FILE="dont-care1.txt" ASPROF_CMD=$ASPROF_CMD ./init-traces.sh
OUTPUT_FILE=$OUTPUT_FILE_1 ASPROF_CMD=$ASPROF_CMD ./init-traces.sh

git checkout $RIGHT
git checkout -b tmp-$RIGHT
trap "git checkout $ORIGINAL_BRANCH && git branch -D tmp-$LEFT && git branch -D tmp-$RIGHT" EXIT
git merge --no-edit $ASPROF_INSTRUMENTATION_BRANCH

OUTPUT_FILE_2=processed_traces_${RIGHT}.txt

OUTPUT_FILE="dont-care2.txt" ASPROF_CMD=$ASPROF_CMD ./init-traces.sh
OUTPUT_FILE=$OUTPUT_FILE_2 ASPROF_CMD=$ASPROF_CMD ./init-traces.sh

git checkout $ASPROF_INSTRUMENTATION_BRANCH

DIFF_OUTPUT_FILE=diff_${LEFT}_${RIGHT}.txt
python3 process-instrumentation/diff.py $OUTPUT_FILE_1 $OUTPUT_FILE_2 > $DIFF_OUTPUT_FILE
FlameGraph/flamegraph.pl $DIFF_OUTPUT_FILE > diff_${LEFT}_${RIGHT}.svg
