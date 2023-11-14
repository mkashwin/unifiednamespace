# The command for building this image is 
#       docker build -t uns/graphdb:<version> --build-arg GIT_HASH=<git hash or local> -f ./Dockerfile ..
#       e.g. 
#       docker build -t uns/graphdb:0.5.0 --build-arg GIT_HASH=local -f ./Dockerfile ..  
# Run the build command in the folder 03_uns_graphdb
# To run the docker file remember to mount a conf folder with the configurations. 
# Provide network if you are connecting to other services
#       e.g.
#       docker run --name uns_mqtt_graphdb -v <full path to conf>/:/app/conf --network=host uns/graphdb:<version> 

# Use the official Python image
FROM python:3.11-slim-bookworm

# Set the environment variable for the entrypoint command
# Don't buffer `stdout`
# Don't create `.pyc` files:
ENV UNS_MODULE="03_uns_graphdb" \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

LABEL org.opencontainers.image.source=https://github.com/mkashwin/unifiednamespace/tree/main/03_uns_graphdb
LABEL org.opencontainers.image.description="Stores MQTT messages to the graph database. Supports both UNS and SparkplugB"
LABEL org.opencontainers.image.licenses=MIT

# Set the working directory in the container to /
WORKDIR /app

# Copy the contents of the project into the container
COPY ./${UNS_MODULE}/pyproject.toml ./poetry.lock ./README.md ./
COPY ./02_mqtt-cluster/pyproject.toml /02_mqtt-cluster/poetry.lock ./02_mqtt-cluster/poetry.lock ./02_mqtt-cluster/README.md /02_mqtt-cluster/

COPY ./02_mqtt-cluster/src /02_mqtt-cluster/src
COPY ./${UNS_MODULE}/src ./src/



# Install pip & poetry
RUN  pip install --upgrade pip poetry

# create application user
RUN useradd --no-create-home --home /app uns_user && \
    chown -R uns_user /app 

# Install the required dependencies for the project using poetry as that user
RUN su uns_user -c "poetry lock --no-update \
    && poetry add /02_mqtt-cluster -n  --lock  \
    && poetry install --only main -n"

USER uns_user

ARG GIT_HASH
ENV GIT_HASH=${GIT_HASH:-dev}

# Mount the volume /conf
VOLUME /app/conf
# Set the Entrypoint script to run the uns_historian module
ENTRYPOINT ["poetry", "run", "uns_graphdb"]
