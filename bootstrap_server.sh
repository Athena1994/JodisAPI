#! /bin/sh

#flask --debug --app ./app/index run
#export FLASK_APP=./program/server/app/index.py
#export PYTHONPATH="media/SSD_Data/Coding/Trader"
#flask --debug run -h 0.0.0.0 -p 5000

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

echo $SCRIPT_DIR

export PYTHONPATH="$SCRIPT_DIR/src"

python3 -m src.app