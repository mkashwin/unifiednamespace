# The command for building this image is 
#       docker build -t uns/kafka_mapper:<version> -f ./Dockerfile ..
#       e.g. 
#       docker build -t uns/kafka_mapper:v0.5.0 -f ./Dockerfile ..  
#       docker build -t uns/kafka_mapper:latest -f ./Dockerfile .. 
# Run the build command in the folder 06_uns_kafka
# To run the docker file remember to mount a conf folder with the configurations
# Provide network if you are connecting to other services
#       e.g.
#       docker run --name uns_kafka_mapper -v <full path to conf>/:/app/conf  --network=host uns/kafka_mapper:v0.5.0 
# Use the official Python image
FROM python:3.12-alpine3.19

# Set the environment variable for the entrypoint command
ENV UNS_MODULE="06_uns_kafka"\
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

LABEL org.opencontainers.image.source=https://github.com/mkashwin/unifiednamespace/tree/main/06_uns_kafka
LABEL org.opencontainers.image.description="Listens to the UNS namespace, converts UNS topic to Kafka topic and publishes the message to Kafka"
LABEL org.opencontainers.image.licenses=MIT

# Set the working directory in the container to /
WORKDIR /app

# Copy the contents of the project into the container
COPY ./${UNS_MODULE}/pyproject.toml /${UNS_MODULE}/poetry.lock ./${UNS_MODULE}/README.md ./LICENSE* ./
COPY ./02_mqtt-cluster/pyproject.toml /02_mqtt-cluster/poetry.lock ./02_mqtt-cluster/poetry.lock ./02_mqtt-cluster/README.md /02_mqtt-cluster/

COPY ./02_mqtt-cluster/src /02_mqtt-cluster/src
COPY ./${UNS_MODULE}/src ./src/

# install minimalistic missing packages
RUN apk update && \ 
    apk add --no-cache  libffi-dev libc-dev gcc bash g++ make && \
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

# Mount the volume /conf
VOLUME /app/conf
# Set the Entrypoint script to run the uns_kafka module
ENTRYPOINT ["poetry", "run", "uns_kafka_mapper"]
