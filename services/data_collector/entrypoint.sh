#!/bin/sh

echo "Waiting for elasticsearch..."

# scan the port to see whether postgres database is ready or not
while ! nc -z ${ELASTIC_HOSTNAME} ${ELASTIC_PORT}; do
  sleep 0.1
done

echo "Mongo started"


echo "Start REST server on ${SERVER_LISTENING_IP}:${SERVER_LISTENING_PORT}"
uvicorn app.app:app --host ${SERVER_LISTENING_IP} --port ${SERVER_LISTENING_PORT} --workers ${SERVER_WORKERS_AMOUNT}
