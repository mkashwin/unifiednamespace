###############################################################################
# Copyright (c) 2021 Ashwin Krishnan
#
# All rights reserved. This program and the accompanying materials
# are made available under the terms of MIT and  is provided "as is",
# without warranty of any kind, express or implied, including but
# not limited to the warranties of merchantability, fitness for a
# particular purpose and noninfringement. In no event shall the
# authors, contributors or copyright holders be liable for any claim,
# damages or other liability, whether in an action of contract,
# tort or otherwise, arising from, out of or in connection with the software
# or the use or other dealings in the software.
#
# Contributors:
#    -
###############################################################################

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
FROM python:3.12-alpine3.20

# Set the environment variable for the entrypoint command
# spell-checker:disable
ENV UNS_MODULE="03_uns_graphdb" \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1
# spell-checker:enable
LABEL org.opencontainers.image.source=https://github.com/mkashwin/unifiednamespace/tree/main/03_uns_graphdb
LABEL org.opencontainers.image.description="Stores MQTT messages to the graph database. Supports both UNS and SparkplugB"
LABEL org.opencontainers.image.licenses=MIT

# Set the working directory in the container to /
WORKDIR /app

# Copy the contents of the project into the container
COPY ./${UNS_MODULE}/pyproject.toml ./${UNS_MODULE}/poetry.lock ./${UNS_MODULE}/README.md ./LICENSE* ./
COPY ./02_mqtt-cluster/pyproject.toml /02_mqtt-cluster/poetry.lock ./02_mqtt-cluster/poetry.lock ./02_mqtt-cluster/README.md /02_mqtt-cluster/

COPY ./02_mqtt-cluster/src /02_mqtt-cluster/src
COPY ./${UNS_MODULE}/src ./src/

# install minimalistic missing packages & security fixes
RUN apk update && \ 
    apk add --no-cache libffi-dev libc-dev gcc && \
    apk upgrade --no-cache libexpat libcrypto3 libssl3 busybox ssl_client && \
    rm -rf /var/cache/apk/*

# Install pip & poetry
RUN  pip install  --no-cache-dir --upgrade pip poetry && \
    # create application user
    adduser --no-create-home --home /app --disabled-password uns_user && \
    chown -R uns_user /app && \
    # Install the required dependencies for the project using poetry as that user
    su uns_user -c "poetry lock --regenerate \
    && poetry add /02_mqtt-cluster -n  --lock  \
    && poetry install --only main -n"

USER uns_user

ARG GIT_HASH
ENV GIT_HASH=${GIT_HASH:-dev}

# Mount the volume /conf
VOLUME /app/conf
# Set the Entrypoint script to run the uns_historian module
ENTRYPOINT ["poetry", "run", "uns_graphdb"]
HEALTHCHECK --interval=60s --timeout=10s CMD ["poetry", "run",  "uns_graphdb_healthcheck"]