#!/bin/bash
echo 'setting up environment variables'
sleep 1
unset NO_CREATE_TABLES
unset SAVE_AS_JSON
unset CONNECTION_STRING
set -a
source config.ini
set +a

if ! [ -z "$SAVE_AS_JSON" ]; then
    echo "----------SETTING TO SAVE AS JSON----------"
fi
mkdir -p data/crawljobs dbs logs
echo 'finished setting up environment variables'

# install virtual environment
echo "Installing Virtual Environment..." >&2
python3.6 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# create database tables
if [ -z "$NO_CREATE_TABLES" ]; then
    python create_table.py
fi

# Start the scrapyd process
nohup scrapyd > /dev/null 2>&1 &
status=$?
if [ $status -ne 0 ]
then
  echo "Failed to start scrapyd: $status"
  exit $status
else
  echo "scrapyd service started..."
fi

# Start the gunicorn process
gunicorn -b 0.0.0.0:$API_PORT start:app --daemon --error-logfile logs/gunicorn_error.logs --access-logfile logs/gunicorn_access.logs
status=$?
if [ $status -ne 0 ]
then
  echo "Failed to start gunicorn: $status"
  exit $status
else
  echo "gunicorn server started..."
fi

# Start the queue_check script
nohup $PWD/venv/bin/python queue_check.py > /dev/null 2>&1 &
status=$?
if [ $status -ne 0 ]
then
  echo "Failed to start queue_check script: $status"
  exit $status
else
  echo "queue_check script started..."
fi