# The command for building this image is 
#       docker build -t uns/spb_mapper:<version> -f ./Dockerfile ..
#       e.g. 
#       docker build -t uns/spb_mapper:v0.5.0 -f ./Dockerfile ..  
#       docker build -t uns/spb_mapper:latest -f ./Dockerfile .. 
# Run the build command in the folder 05_sparkplugb
# To run the docker file remember to mount a conf folder with the configurations
# Provide network if you are connecting to other services
#       e.g.
#       docker run --name uns_spb_mapper -v <full path to conf>/:/app/conf  --network=host uns/spb_mapper:v0.5.0 
# Use the official Python image
FROM python:3.12-alpine3.19

# Set the environment variable for the entrypoint command
ENV UNS_MODULE="05_sparkplugb"\
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

LABEL org.opencontainers.image.source=https://github.com/mkashwin/unifiednamespace/tree/main/05_sparkplugb
LABEL org.opencontainers.image.description="Listens to the SparkplugB name space and translates them to UNS messages, then publishes to the UNS Namespace"
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
    apk add --no-cache libffi-dev libc-dev gcc && \
    apk upgrade --no-cache libexpat libcrypto3 libssl3 && \
    rm -rf /var/cache/apk/*

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
# Set the Entrypoint script to run the uns_sparkplugb module
ENTRYPOINT ["poetry", "run", "uns_spb_mapper"]
