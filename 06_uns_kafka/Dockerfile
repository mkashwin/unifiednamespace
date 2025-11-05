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
#       docker build -t uns/kafka_mapper:<version> --build-arg GIT_HASH=<git hash or local> -f ./Dockerfile ..
#       e.g. 
#       docker build -t uns/kafka_mapper:0.5.0 --build-arg GIT_HASH=local -f ./Dockerfile ..  
#       docker build -t uns/kafka_mapper:local --build-arg GIT_HASH=local -f ./Dockerfile ..  
# Run the build command in the folder 06_uns_kafka
# To run the docker file remember to mount a conf folder with the configurations
# Provide network if you are connecting to other services
#       e.g.
#       docker run --name uns_kafka_mapper -v <full path to conf>/:/app/conf  --network=host uns/kafka_mapper:v0.5.0 
# Use the official Python image
FROM python:3.14-alpine3.22

# Set the environment variable for the entrypoint command
# spell-checker:disable
ENV UNS_MODULE="06_uns_kafka"\
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LIBRDKAFKA_VER="2.12.1"
# spell-checker:enable
LABEL org.opencontainers.image.source=https://github.com/mkashwin/unifiednamespace/tree/main/06_uns_kafka
LABEL org.opencontainers.image.description="Listens to the UNS namespace, converts UNS topic to Kafka topic and publishes the message to Kafka"
LABEL org.opencontainers.image.licenses=MIT

# Set the working directory in the container to /
WORKDIR /app

# Copy the contents of the project into the container
COPY ./${UNS_MODULE}/pyproject.toml ./${UNS_MODULE}/uv.lock ./${UNS_MODULE}/README.md ./LICENSE* ./
COPY ./02_mqtt-cluster/pyproject.toml /02_mqtt-cluster/uv.lock ./02_mqtt-cluster/uv.lock ./02_mqtt-cluster/README.md /02_mqtt-cluster/

COPY ./02_mqtt-cluster/src /02_mqtt-cluster/src
COPY ./${UNS_MODULE}/src ./src/

# install minimalistic missing packages & security fixes
# trunk-ignore(hadolint/DL3003)
# trunk-ignore(trivy/DS013)
RUN apk update && \ 
    apk add --no-cache  libffi-dev libc-dev gcc bash g++ make && \
    apk upgrade --no-cache libexpat libcrypto3 libssl3 busybox ssl_client && \
    rm -rf /var/cache/apk/* && \
    # Need to install https://github.com/confluentinc/librdkafka/releases/tag/v${LIBRDKAFKA_VER} as alpine does not have this version   
    wget -q https://github.com/confluentinc/librdkafka/archive/refs/tags/v${LIBRDKAFKA_VER}.zip && \
    unzip -o v${LIBRDKAFKA_VER}.zip && \
    cd  librdkafka-${LIBRDKAFKA_VER} && \
    bash -c "./configure --install-deps --disable-gssapi --disable-lz4-ext --enable-static && \
    ./configure --prefix /usr && \
    make && \
    make install" && \
    cd .. && \
    rm v${LIBRDKAFKA_VER}.zip && \
    rm -rf librdkafka-${LIBRDKAFKA_VER}

# Install pip & uv
RUN  pip install  --no-cache-dir --upgrade pip uv && \
    # create application user
    adduser --no-create-home --home /app --disabled-password uns_user && \
    chown -R uns_user /app && \
    # Install the required dependencies for the project using uv as that user
    su uns_user -c "uv lock  \
    && uv add /02_mqtt-cluster -n \
    && uv sync --group main --compile-bytecode"

USER uns_user

ARG GIT_HASH
ENV GIT_HASH=${GIT_HASH:-dev}

# Mount the volume /conf
VOLUME /app/conf
# Set the Entrypoint script to run the uns_kafka module
ENTRYPOINT ["uv", "run", "uns_kafka_mapper"]
HEALTHCHECK --interval=60s --timeout=10s CMD ["uv", "run",  "uns_kafka_healthcheck"]