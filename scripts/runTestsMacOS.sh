#/bin/sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd $DIR
cd ../

echo "- Utility Function tests"
./esstoolkit/tests/runtest_macos.sh esstoolkit.tests.test_utility_functions
echo "- Gate Transformer tests"
./esstoolkit/tests/runtest_macos.sh esstoolkit.tests.test_gate_transformer
echo "- Network Segmenter tests"
./esstoolkit/tests/runtest_macos.sh esstoolkit.tests.test_segmenter
echo "- Road Centerline Cleaner tests"
./esstoolkit/tests/runtest_macos.sh esstoolkit.tests.test_rcl_cleaner