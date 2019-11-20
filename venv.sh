#!/usr/bin/env bash
set -e
echo "Building virtual environment"
PYTHON=$(which python3)
# check minimum version
MIN=$($PYTHON -c "import sys;s=sys.version_info;print(1) if s[0]<3 or s[1]<6 else print(0)")
if [[ $MIN == 1 ]]; then
  echo "minimum python3 version not found"
  exit 1
fi

if [[ -d ./.venv ]]; then
  rm -rf ./.venv
fi

virtualenv --no-site-packages --python=$PYTHON ./.venv

source ./.venv/bin/activate && pip install -r requirements-frozen.txt -r requirements-dev.txt