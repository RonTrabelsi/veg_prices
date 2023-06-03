#!/bin/sh

echo "Waiting for mongo..."

# scan the port to see whether postgres database is ready or not
while ! nc -z ${MONGO_HOSTNAME} ${MONGO_PORT}; do
  sleep 0.1
done

echo "Mongo started"


echo "Start REST server on ${SERVER_LISTENING_IP}:${SERVER_LISTENING_PORT}"
uvicorn app.router:app --host ${SERVER_LISTENING_IP} --port ${SERVER_LISTENING_PORT}
