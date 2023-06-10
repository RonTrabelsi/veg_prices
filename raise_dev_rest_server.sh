APP_PATH=./services/data_collector
INTERPRETER_PATH=../../venv/bin/python

# Start server dependencies
docker-compose -f docker-compose-dev.yml up -d


# Set project as cwd
cd $APP_PATH

# Load env
export $(cat data_collector-dev.env | xargs)

# Print env
export 

echo "Waiting for elasticsearch..."

# Wait for ealsticsearch 
while ! nc -z ${ELASTIC_HOSTNAME} ${ELASTIC_PORT}; do
  sleep 0.1
done

echo "elasticsearch started"

# Start Dev server with the relevant venv
$INTERPRETER_PATH -c 'from app.app import app; import uvicorn ;uvicorn.run(app, host="0.0.0.0", port=8000)'
