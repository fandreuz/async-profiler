set -eux

ORIGINAL_BRANCH=$(git rev-parse --abbrev-ref HEAD)
ASPROF_CMD=${ASPROF_CMD:--agentpath:./build/lib/libasyncProfiler.so=start,timeout=10,collapsed,file=/dev/null,event=cpu,interval=10ms}
ASPROF_INSTRUMENTATION_BRANCH=instrumenting-asprof
SAMPLES_COUNT_FILE=samples_count.txt

DIFF_OUTPUT_FILE=diff_${LEFT}_${RIGHT}.txt
rm -f $DIFF_OUTPUT_FILE diff_${LEFT}_${RIGHT}.svg $SAMPLES_COUNT_FILE

git checkout $LEFT
git checkout -b tmp-$LEFT
trap "git checkout $ORIGINAL_BRANCH && git branch -D tmp-$LEFT" EXIT
git merge --no-edit $ASPROF_INSTRUMENTATION_BRANCH

OUTPUT_FILE_1=processed_traces_${LEFT}.txt
OUTPUT_FILE=$OUTPUT_FILE_1 ASPROF_CMD=$ASPROF_CMD SAMPLES_COUNT_FILE=$SAMPLES_COUNT_FILE ./init-traces.sh
samples_count_1=$(cat $SAMPLES_COUNT_FILE)

git checkout $RIGHT
git checkout -b tmp-$RIGHT
trap "git checkout $ORIGINAL_BRANCH && git branch -D tmp-$LEFT && git branch -D tmp-$RIGHT" EXIT
git merge --no-edit $ASPROF_INSTRUMENTATION_BRANCH

OUTPUT_FILE_2=processed_traces_${RIGHT}.txt
OUTPUT_FILE=$OUTPUT_FILE_2 ASPROF_CMD=$ASPROF_CMD SAMPLES_COUNT_FILE=$SAMPLES_COUNT_FILE ./init-traces.sh
samples_count_2=$(cat $SAMPLES_COUNT_FILE)

samples_count_diff=$(($samples_count_1 - $samples_count_2))
if [ ${samples_count_diff#-} -gt 500 ]; then
    echo "Samples difference too high: $samples_count_1, $samples_count_2"
    exit 1
fi

git checkout $ASPROF_INSTRUMENTATION_BRANCH

python3 process-instrumentation/diff.py $OUTPUT_FILE_1 $OUTPUT_FILE_2 > $DIFF_OUTPUT_FILE
FlameGraph/flamegraph.pl $DIFF_OUTPUT_FILE > diff_${LEFT}_${RIGHT}.svg
