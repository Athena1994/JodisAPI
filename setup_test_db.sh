
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

echo $SCRIPT_DIR

export PYTHONPATH="$SCRIPT_DIR/src"

python3 -m scripts.test_db