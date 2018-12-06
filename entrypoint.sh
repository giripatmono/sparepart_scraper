#!/bin/bash
echo 'setting up environment variables'
sleep 1
set -a
source config.ini
set +a
echo 'finished setting up environment variables'

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
nohup python queue_check.py > /dev/null 2>&1 &
status=$?
if [ $status -ne 0 ]
then
  echo "Failed to start queue_check script: $status"
  exit $status
else
  echo "queue_check script started..."
fi


# Naive check runs checks once a minute to see if either of the processes exited.
# This illustrates part of the heavy lifting you need to do if you want to run
# more than one service in a container. The container exits with an error
# if it detects that either of the processes has exited.
# Otherwise it loops forever, waking up every 60 seconds

while sleep 60; do
  ps aux |grep scrapyd |grep -q -v grep
  PROCESS_1_STATUS=$?
  ps aux |grep gunicorn |grep -q -v grep
  PROCESS_2_STATUS=$?
  # If the greps above find anything, they exit with 0 status
  # If they are not both 0, then something is wrong
  if [ $PROCESS_1_STATUS -ne 0 -o $PROCESS_2_STATUS -ne 0 ]; then
    echo "One of the processes has already exited."
    # exit 1
  fi
done
