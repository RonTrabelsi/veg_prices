#!/bin/sh

echo "Waiting for elasticsearch..."

# Wait for ealsticsearch 
while ! nc -z ${ELASTIC_HOSTNAME} ${ELASTIC_PORT}; do
  sleep 0.1
done

echo "elasticsearch started"

echo "Start periodic scraper service..."
python -m src.main
