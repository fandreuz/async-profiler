set -eux

ORIGINAL_BRANCH=$(git rev-parse --abbrev-ref HEAD)
ASPROF_CMD=${ASPROF_CMD:--agentpath:./build/lib/libasyncProfiler.so=start,timeout=10,collapsed,file=/dev/null,event=cpu,interval=10ms}

git checkout $1
git checkout -b tmp-$1
trap "git branch -D tmp-$1" EXIT
git merge --no-edit instrumenting-asprof

OUTPUT_FILE_1=processed_traces_$1.txt
OUTPUT_FILE=$OUTPUT_FILE_1 ASPROF_CMD=$ASPROF_CMD ./init-traces.sh

git checkout $2
git checkout -b tmp-$2
trap "git branch -D tmp-$1 && git branch -D tmp-$2" EXIT
git merge --no-edit instrumenting-asprof

OUTPUT_FILE_2=processed_traces_$2.txt
OUTPUT_FILE=$OUTPUT_FILE_2 ASPROF_CMD=$ASPROF_CMD ./init-traces.sh

DIFF_OUTPUT_FILE=diff_$1_$2.txt
python3 process-instrumentation/diff.py $OUTPUT_FILE_1 $OUTPUT_FILE_2 > $DIFF_OUTPUT_FILE
../FlameGraph/flamegraph.pl $DIFF_OUTPUT_FILE > diff_$1_$2.svg

git checkout $ORIGINAL_BRANCH
