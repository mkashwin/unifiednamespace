# The command for building this image is 
#       docker build -t uns/spb_mapper:<version> -f ./Dockerfile ..
#       e.g. 
#       docker build -t uns/spb_mapper:v0.5.0 -f ./Dockerfile ..  
#       docker build -t uns/spb_mapper:latest -f ./Dockerfile .. 
# Run the build command in the folder 05_sparkplugb
# To run the docker file remember to mount a conf folder with the configurations
#       e.g.
#       docker run --name uns_spb_mapper -v <full path to conf>/:/app/conf uns/spb_mapper:v0.5.0 

# Use the official Python image
FROM python:3.11-slim-bullseye

# Set the environment variable for the entrypoint command
ENV UNS_MODULE="05_sparkplugb"


# Set the working directory in the container to /
WORKDIR /app

# Copy the contents of the project into the container
COPY ./${UNS_MODULE}/src ./src/
COPY ./${UNS_MODULE}/pyproject.toml ./
COPY ./${UNS_MODULE}/poetry.lock ./
COPY ./${UNS_MODULE}/README.md ./


# Need to do this because despite only installing main by poetry it looks for this folder
RUN mkdir ../02_mqtt-cluster
COPY ./02_mqtt-cluster/pyproject.toml /02_mqtt-cluster/
COPY ./02_mqtt-cluster/poetry.lock /02_mqtt-cluster/
COPY ./02_mqtt-cluster/README.md /02_mqtt-cluster/
COPY ./02_mqtt-cluster/src /02_mqtt-cluster/src

# Install the required dependencies for the project using poetry
RUN pip install poetry
RUN poetry add /02_mqtt-cluster -n  --lock
RUN poetry install --only main -n

# Mount the volume /conf
VOLUME /app/conf

# Set the Entrypoint script to run the uns_historian module
ENTRYPOINT ["poetry", "run", "uns_spb_mapper"]
