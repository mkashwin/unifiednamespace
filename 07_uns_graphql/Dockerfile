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
#       docker build -t uns/graphql:<version> --build-arg GIT_HASH=<git hash or local> -f ./Dockerfile ..
#       e.g. 
#       docker build -t uns/graphql:0.5.0 --build-arg GIT_HASH=local -f ./Dockerfile ..  
#       docker build -t uns/graphql:local --build-arg GIT_HASH=local -f ./Dockerfile .. 
# Run the build command in the folder 07_uns_graphql
# To run the docker file remember to mount a conf folder with the configurations
# Provide network if you are connecting to other services
#       e.g.
#       docker run --name uns_graphql -v <full path to conf>/:/app/conf  --network=host uns/graphql:v0.5.0 
# Use the official Python image
FROM python:3.12-alpine3.20

# Set the environment variable for the entrypoint command
# spell-checker:disable
ENV UNS_MODULE="07_uns_graphql"\
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LIBRDKAFKA_VER="2.11.1"
# spell-checker:enable
LABEL org.opencontainers.image.source=https://github.com/mkashwin/unifiednamespace/tree/main/07_uns_graphql
LABEL org.opencontainers.image.description="Provide GraphQL capabilities for the UNS across all data sources"
LABEL org.opencontainers.image.licenses=MIT

# Set the working directory in the container to /
WORKDIR /app

# Copy the contents of the project into the container
COPY ./${UNS_MODULE}/pyproject.toml ./${UNS_MODULE}/uv.lock ./${UNS_MODULE}/README.md ./LICENSE* ./
COPY ./02_mqtt-cluster/pyproject.toml /02_mqtt-cluster/uv.lock ./02_mqtt-cluster/uv.lock ./02_mqtt-cluster/README.md /02_mqtt-cluster/

COPY ./02_mqtt-cluster/src /02_mqtt-cluster/src
COPY ./${UNS_MODULE}/src ./src/

# install minimalistic missing packages & security fixes
RUN apk update && \ 
    apk add --no-cache  libffi-dev libc-dev gcc bash g++ make musl-dev rust cargo && \
    apk upgrade --no-cache libexpat libcrypto3 libssl3 busybox ssl_client krb5-libs && \
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
    && uv sync --group main"

USER uns_user

ARG GIT_HASH
ENV GIT_HASH=${GIT_HASH:-dev}
# expose port
EXPOSE 8000

# Mount the volume /conf
VOLUME /app/conf
# Set the Entrypoint script to run the uns_graphql module using uvicorn
ENTRYPOINT ["uv", "run", "uvicorn", "uns_graphql.uns_graphql_app:UNSGraphql.app", "--host", "0.0.0.0", "--port", "8000"]
HEALTHCHECK --interval=60s --timeout=10s CMD ["uv", "run",  "uns_graphql_healthcheck", "--port", "8000"]