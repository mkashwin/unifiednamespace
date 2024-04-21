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
#       docker build -t uns/graphql:<version> -f ./Dockerfile ..
#       e.g. 
#       docker build -t uns/graphql:v0.5.0 -f ./Dockerfile ..  
#       docker build -t uns/graphql:latest -f ./Dockerfile .. 
# Run the build command in the folder 07_uns_graphql
# To run the docker file remember to mount a conf folder with the configurations
# Provide network if you are connecting to other services
#       e.g.
#       docker run --name uns_graphql -v <full path to conf>/:/app/conf  --network=host uns/graphql:v0.5.0 
# Use the official Python image
FROM python:3.12-alpine3.19

# Set the environment variable for the entrypoint command
ENV UNS_MODULE="07_uns_graphql"\
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

LABEL org.opencontainers.image.source=https://github.com/mkashwin/unifiednamespace/tree/main/07_uns_graphql
LABEL org.opencontainers.image.description="Provide GraphQL capabilities for the UNS across all data sources"
LABEL org.opencontainers.image.licenses=MIT

# Set the working directory in the container to /
WORKDIR /app

# Copy the contents of the project into the container
COPY ./${UNS_MODULE}/pyproject.toml ./${UNS_MODULE}/poetry.lock ./${UNS_MODULE}/README.md ./LICENSE* ./
COPY ./02_mqtt-cluster/pyproject.toml /02_mqtt-cluster/poetry.lock ./02_mqtt-cluster/poetry.lock ./02_mqtt-cluster/README.md /02_mqtt-cluster/

COPY ./02_mqtt-cluster/src /02_mqtt-cluster/src
COPY ./${UNS_MODULE}/src ./src/

# install minimalistic missing packages
RUN apk update && \ 
    apk add --no-cache  libffi-dev libc-dev gcc bash g++ make musl-dev rust cargo && \
    apk upgrade --no-cache libexpat libcrypto3 libssl3 && \
    rm -rf /var/cache/apk/* && \
    # Need to install https://github.com/confluentinc/librdkafka/tree/v2.3.0 as alpine does not have this version   
    wget -q https://github.com/confluentinc/librdkafka/archive/refs/tags/v2.3.0.zip && \
    unzip -o v2.3.0.zip && \
    cd  librdkafka-2.3.0 && \
    bash -c "./configure && \
    ./configure --prefix /usr && \
    make && \
    make install" && \
    cd .. && \
    rm v2.3.0.zip && \
    rm -rf librdkafka-2.3.0

# Install pip & poetry
RUN  pip install --upgrade pip poetry && \
    # create application user
    adduser --home /app --disabled-password uns_user && \
    chown -R uns_user /app && \
    # Install the required dependencies for the project using poetry as that user
    su uns_user -c "poetry lock --no-update \
    && poetry add /02_mqtt-cluster -n  --lock  \
    && poetry install --only main -n"

USER uns_user

ARG GIT_HASH
ENV GIT_HASH=${GIT_HASH:-dev}
# expose port
EXPOSE 8000

# Mount the volume /conf
VOLUME /app/conf
# Set the Entrypoint script to run the uns_graphql module using uvicorn
ENTRYPOINT ["poetry", "run", "uvicorn", "uns_graphql.uns_graphql_app:UNSGraphql.app", "--host", "0.0.0.0", "--port", "8000"]
