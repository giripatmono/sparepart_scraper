#!/usr/bin/env bash

kill -9 `ps aux |grep gunicorn |grep -F -- $PWD"/venv" |grep 'start:app' | awk '{ print $2 }'`  # will kill all gunicorn workers
kill -9 `ps aux |grep scrapyd |grep -F -- $PWD"/venv" | grep -v grep | awk '{ print $2 }'`  # will kill all scrapyd process
kill -9 `ps aux |grep queue_check.py |grep -F -- $PWD"/venv" | awk '{ print $2 }'`  # will kill all queue_check process