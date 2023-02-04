# The command for building this image is 
#       docker build -t uns/historian:<version> -f ./Dockerfile ..
#       e.g. 
#       docker build -t uns/historian:v0.5.0 -f ./Dockerfile ..  
# Run the build command in the folder 04_uns_historian
# To run the docker file remember to mount a conf folder with the configurations
#       e.g.
#       docker run --name uns_mqtt_historian -v <full path to conf>/:/app/conf uns/historian:v0.5.0 


# Use the official Python image
FROM python:3.11-slim-bullseye

# Set the environment variable for the entrypoint command
ENV UNS_MODULE="04_uns_historian"


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
RUN pip install --upgrade pip
RUN pip install --upgrade poetry
RUN poetry add /02_mqtt-cluster -n  --lock
RUN poetry install --only main -n

# Mount the volume /conf
VOLUME /app/conf

# Set the Entrypoint script to run the uns_historian module
ENTRYPOINT ["poetry", "run", "uns_historian"]
