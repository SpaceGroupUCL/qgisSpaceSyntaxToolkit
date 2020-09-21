#/bin/sh
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd $DIR
cd ../esstoolkit/
git archive --format zip -o $DIR/esstoolkit.zip --prefix=esstoolkit/ HEAD