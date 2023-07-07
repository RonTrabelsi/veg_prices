#!/bin/sh

echo "Waiting for elasticsearch..."

# Wait for ealsticsearch 
while ! nc -z ${ELASTIC_HOSTNAME} ${ELASTIC_PORT}; do
  sleep 0.1
done

echo "elasticsearch started"


echo "Start scraper REST server on ${SERVER_LISTENING_IP}:${SERVER_LISTENING_PORT}"
uvicorn src.app:app --host ${SERVER_LISTENING_IP} --port ${SERVER_LISTENING_PORT} --workers ${SERVER_WORKERS_AMOUNT}
