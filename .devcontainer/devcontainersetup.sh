#!/bin/bash
# This script is to be executed on creation of the dev container in order to create a working development environment
if [[ -z ${WORKSPACE_DEFAULT_PATH} ]]; then
	WORKSPACE_DEFAULT_PATH"$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
	exit 1
fi

# 1.0 setup the python environment
pip3 install --upgrade pip uv
uv python install --default 3.14
uv sync

# 2. create minimalistic secret files for all the modules.
# 2.1 Neo4j
# trunk-ignore(shellcheck/SC2312)
if [[ -n $(docker ps -aq -f name=uns_graphdb) ]]; then
	docker start uns_graphdb && docker exec -it uns_graphdb bash -c "rm /var/lib/neo4j/run/*"
else
	UNS_graphdb__username=neo4j
	UNS_graphdb__password=$(openssl rand -base64 32 | tr -dc '[:alnum:]' || true)
	echo "graphdb:
  username: ${UNS_graphdb__username}
  password: ${UNS_graphdb__password}
dynaconf_merge: true
  " >"${WORKSPACE_DEFAULT_PATH}"/03_uns_graphdb/conf/.secrets.yaml
	# 2.1.1 New instance of Graph DB used by 03_uns_graphdb
	sudo rm -rf "${HOME}"/neo4j

	docker run \
		--name uns_graphdb \
		-p7474:7474 -p7687:7687 \
		-d \
		-v "${HOME}"/neo4j/data:/data \
		-v "${HOME}"/neo4j/logs:/logs \
		-v "${HOME}"/neo4j/plugins:/plugins \
		-v "${HOME}"/neo4j/import:/var/lib/neo4j/import \
		-v "${HOME}"/neo4j/run:/var/lib/neo4j/run \
		--env NEO4J_AUTH="${UNS_graphdb__username}"/"${UNS_graphdb__password}" \
		--env apoc.export.file.enabled=true \
		--env apoc.import.file.enabled=true \
		--env apoc.import.file.use_neo4j_config=true \
		--env NEO4J_PLUGINS=\[\"apoc\"\] \
		neo4j:latest

fi

# trunk-ignore(shellcheck/SC2312)
if [[ -n $(docker ps -aq -f name=uns_timescaledb) ]]; then
	docker start uns_timescaledb
else
	POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -dc '[:alnum:]' || true)
	UNS_historian__username=uns_dbuser
	UNS_historian__password=$(openssl rand -base64 32 | tr -dc '[:alnum:]' || true)

	UNS_historian__database=uns_historian
	UNS_historian__table=unifiednamespace

	echo "historian:
  username: ${UNS_historian__username}
  password: ${UNS_historian__password}
dynaconf_merge: true
  # This password is for your reference if you ever need to login as postgres user
  # POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
  " >"${WORKSPACE_DEFAULT_PATH}"/04_uns_historian/conf/.secrets.yaml

	# 2.2.1 Historian DB used by 04_uns_historian
	sudo rm -rf "${HOME}"/timescaledb
	docker run \
		--name uns_timescaledb \
		-p 5432:5432 \
		-v "${HOME}"/timescaledb/data:/var/lib/postgresql/data \
		-d \
		-e POSTGRES_PASSWORD="${POSTGRES_PASSWORD}" \
		timescale/timescaledb:latest-pg16
	# 2.2.2 wait for docker to be up and running
	# first wait for the database to be running
	# Function to check if PostgreSQL is ready
	check_postgres_ready() {
		docker exec -it uns_timescaledb bash -c "pg_isready --username=postgres && psql --username=postgres --list"
	}
	# loop to check
	echo "Waiting for  timescaledb to start ."
	sleep 1
	# trunk-ignore(shellcheck/SC2078)
	while [[ "True" ]]; do
		if check_postgres_ready; then
			sleep 5
			break
		else
			echo -n .
			sleep 1
		fi
	done

	# 2.2.3 basic database setup needed for the historian ( create users, database, timeseries extension etc.)
	docker exec \
		-e PGPASSWORD="${POSTGRES_PASSWORD}" \
		-e UNS_historian__database="${UNS_historian__database}" \
		-e UNS_historian__username="${UNS_historian__username}" \
		-e UNS_historian__password="${UNS_historian__password}" \
		-e UNS_historian__table="${UNS_historian__table}" \
		-it uns_timescaledb \
		bash -c "
    echo \"CREATE DATABASE ${UNS_historian__database};\" | PGPASSWORD=${PGPASSWORD} psql -U postgres -p 5432
    echo \"CREATE EXTENSION IF NOT EXISTS timescaledb;\" | PGPASSWORD=${PGPASSWORD} psql -U postgres -p 5432 -d ${UNS_historian__database}
    echo \"CREATE ROLE ${UNS_historian__username} LOGIN PASSWORD '${UNS_historian__password}'; \" | PGPASSWORD=${PGPASSWORD} psql -U postgres -p 5432 -d ${UNS_historian__database}
    echo \"ALTER DATABASE ${UNS_historian__database} OWNER TO ${UNS_historian__username} ;\" | PGPASSWORD=${PGPASSWORD} psql -U postgres -p 5432 -d ${UNS_historian__database}
    
    echo \"
      CREATE TABLE ${UNS_historian__table} (
        time TIMESTAMPTZ NOT NULL,
        topic TEXT NOT NULL,
        client_id TEXT,
        mqtt_msg JSONB,
        CONSTRAINT unique_event UNIQUE (time, topic, client_id, mqtt_msg)
      );
      SELECT create_hypertable('${UNS_historian__table}', 'time');
    \" | PGPASSWORD=${UNS_historian__password} psql -U ${UNS_historian__username} -p 5432 -d ${UNS_historian__database}
    
  "
fi

# 2.3 MQTT used by all modules
# trunk-ignore(shellcheck/SC2312)
if [[ -n $(docker ps -aq -f name=uns_emqx_mqtt) ]]; then
	docker start uns_emqx_mqtt
else
	docker run -d \
		--name uns_emqx_mqtt \
		--restart unless-stopped \
		-p 1883:1883 \
		-p 1884:1884 \
		-p 8883:8883 \
		-p 8884:8884 \
		-p 8885:8885 \
		-p 8886:8886 \
		-p 8080:8080 \
		-p 8081:8081 \
		-p 8090:8090 \
		-p 8091:8091 \
		-p 18083:18083 \
		-e EMQX_NAME=emqx \
		-e EMQX_HOST=127.0.0.1 \
		-e EMQX_DASHBOARD__LISTENERS__HTTP__BIND=18083 \
		-e EMQX_NODE__COOKIE=emqxsecretcookie \
		-e EMQX_NODE__DATA_DIR=data \
		-e EMQX_LISTENERS__TCP__DEFAULT__BIND=0.0.0.0:1883 \
		-e EMQX_LISTENERS__TCP__DEFAULT__MAX_CONNECTIONS=1024000 \
		-e EMQX_LISTENERS__TCP__DEFAULT__ENABLE_AUTHN=false \
		-e EMQX_LISTENERS__TCP__AUTHENTICATED__BIND=0.0.0.0:1884 \
		-e EMQX_LISTENERS__TCP__AUTHENTICATED__MAX_CONNECTIONS=1024000 \
		-e EMQX_LISTENERS__TCP__AUTHENTICATED__ENABLE_AUTHN=true \
		-e EMQX_LISTENERS__SSL__DEFAULT__BIND=0.0.0.0:8883 \
		-e EMQX_LISTENERS__SSL__DEFAULT__MAX_CONNECTIONS=512000 \
		-e EMQX_LISTENERS__SSL__DEFAULT__ENABLE_AUTHN=false \
		-e EMQX_LISTENERS__SSL__DEFAULT__SSL_OPTIONS__CACERTFILE=/opt/emqx/etc/certs/ca/ca.crt \
		-e EMQX_LISTENERS__SSL__DEFAULT__SSL_OPTIONS__CERTFILE=/opt/emqx/etc/certs/server/server.crt \
		-e EMQX_LISTENERS__SSL__DEFAULT__SSL_OPTIONS__KEYFILE=/opt/emqx/etc/certs/server/server.key \
		-e EMQX_LISTENERS__SSL__DEFAULT__SSL_OPTIONS__VERIFY=verify_none \
		-e EMQX_LISTENERS__SSL__CLIENT_CERT__BIND=0.0.0.0:8884 \
		-e EMQX_LISTENERS__SSL__CLIENT_CERT__MAX_CONNECTIONS=512000 \
		-e EMQX_LISTENERS__SSL__CLIENT_CERT__ENABLE_AUTHN=false \
		-e EMQX_LISTENERS__SSL__CLIENT_CERT__SSL_OPTIONS__CACERTFILE=/opt/emqx/etc/certs/ca/ca.crt \
		-e EMQX_LISTENERS__SSL__CLIENT_CERT__SSL_OPTIONS__CERTFILE=/opt/emqx/etc/certs/server/server.crt \
		-e EMQX_LISTENERS__SSL__CLIENT_CERT__SSL_OPTIONS__KEYFILE=/opt/emqx/etc/certs/server/server.key \
		-e EMQX_LISTENERS__SSL__CLIENT_CERT__SSL_OPTIONS__VERIFY=verify_peer \
		-e EMQX_LISTENERS__SSL__CLIENT_CERT__SSL_OPTIONS__FAIL_IF_NO_PEER_CERT=true \
		-e EMQX_LISTENERS__SSL__AUTHENTICATED__BIND=0.0.0.0:8885 \
		-e EMQX_LISTENERS__SSL__AUTHENTICATED__MAX_CONNECTIONS=512000 \
		-e EMQX_LISTENERS__SSL__AUTHENTICATED__ENABLE_AUTHN=true \
		-e EMQX_LISTENERS__SSL__AUTHENTICATED__SSL_OPTIONS__CACERTFILE=/opt/emqx/etc/certs/ca/ca.crt \
		-e EMQX_LISTENERS__SSL__AUTHENTICATED__SSL_OPTIONS__CERTFILE=/opt/emqx/etc/certs/server/server.crt \
		-e EMQX_LISTENERS__SSL__AUTHENTICATED__SSL_OPTIONS__KEYFILE=/opt/emqx/etc/certs/server/server.key \
		-e EMQX_LISTENERS__SSL__AUTHENTICATED__SSL_OPTIONS__VERIFY=verify_none \
		-e EMQX_LISTENERS__SSL__UNAUTH_ALT__BIND=0.0.0.0:8886 \
		-e EMQX_LISTENERS__SSL__UNAUTH_ALT__MAX_CONNECTIONS=512000 \
		-e EMQX_LISTENERS__SSL__UNAUTH_ALT__ENABLE_AUTHN=false \
		-e EMQX_LISTENERS__SSL__UNAUTH_ALT__SSL_OPTIONS__CACERTFILE=/opt/emqx/etc/certs/ca/ca.crt \
		-e EMQX_LISTENERS__SSL__UNAUTH_ALT__SSL_OPTIONS__CERTFILE=/opt/emqx/etc/certs/server/server.crt \
		-e EMQX_LISTENERS__SSL__UNAUTH_ALT__SSL_OPTIONS__KEYFILE=/opt/emqx/etc/certs/server/server.key \
		-e EMQX_LISTENERS__SSL__UNAUTH_ALT__SSL_OPTIONS__VERIFY=verify_none \
		-e EMQX_LISTENERS__WS__DEFAULT__BIND=0.0.0.0:8080 \
		-e EMQX_LISTENERS__WS__DEFAULT__MAX_CONNECTIONS=1024000 \
		-e EMQX_LISTENERS__WS__DEFAULT__ENABLE_AUTHN=false \
		-e EMQX_LISTENERS__WS__DEFAULT__WEBSOCKET__MQTT_PATH=/mqtt \
		-e EMQX_LISTENERS__WSS__DEFAULT__BIND=0.0.0.0:8081 \
		-e EMQX_LISTENERS__WSS__DEFAULT__MAX_CONNECTIONS=512000 \
		-e EMQX_LISTENERS__WSS__DEFAULT__ENABLE_AUTHN=false \
		-e EMQX_LISTENERS__WSS__DEFAULT__WEBSOCKET__MQTT_PATH=/mqtt \
		-e EMQX_LISTENERS__WSS__DEFAULT__SSL_OPTIONS__CACERTFILE=/opt/emqx/etc/certs/ca/ca.crt \
		-e EMQX_LISTENERS__WSS__DEFAULT__SSL_OPTIONS__CERTFILE=/opt/emqx/etc/certs/server/server.crt \
		-e EMQX_LISTENERS__WSS__DEFAULT__SSL_OPTIONS__KEYFILE=/opt/emqx/etc/certs/server/server.key \
		-e EMQX_LISTENERS__WSS__DEFAULT__SSL_OPTIONS__VERIFY=verify_none \
		-e EMQX_LISTENERS__WS__AUTHENTICATED__BIND=0.0.0.0:8090 \
		-e EMQX_LISTENERS__WS__AUTHENTICATED__MAX_CONNECTIONS=1024000 \
		-e EMQX_LISTENERS__WS__AUTHENTICATED__ENABLE_AUTHN=true \
		-e EMQX_LISTENERS__WS__AUTHENTICATED__WEBSOCKET__MQTT_PATH=/mqtt \
		-e EMQX_LISTENERS__WSS__AUTHENTICATED__BIND=0.0.0.0:8091 \
		-e EMQX_LISTENERS__WSS__AUTHENTICATED__MAX_CONNECTIONS=512000 \
		-e EMQX_LISTENERS__WSS__AUTHENTICATED__ENABLE_AUTHN=true \
		-e EMQX_LISTENERS__WSS__AUTHENTICATED__WEBSOCKET__MQTT_PATH=/mqtt \
		-e EMQX_LISTENERS__WSS__AUTHENTICATED__SSL_OPTIONS__CACERTFILE=/opt/emqx/etc/certs/ca/ca.crt \
		-e EMQX_LISTENERS__WSS__AUTHENTICATED__SSL_OPTIONS__CERTFILE=/opt/emqx/etc/certs/server/server.crt \
		-e EMQX_LISTENERS__WSS__AUTHENTICATED__SSL_OPTIONS__KEYFILE=/opt/emqx/etc/certs/server/server.key \
		-e EMQX_LISTENERS__WSS__AUTHENTICATED__SSL_OPTIONS__VERIFY=verify_none \
		-e EMQX_AUTHENTICATION__1__MECHANISM=password_based \
		-e EMQX_AUTHENTICATION__1__BACKEND=built_in_database \
		-e EMQX_AUTHENTICATION__1__USER_ID_TYPE=username \
		-e EMQX_AUTHORIZATION__NO_MATCH=deny \
		-e EMQX_AUTHORIZATION__DENY_ACTION=disconnect \
		-e EMQX_AUTHORIZATION__SOURCES__1__TYPE=file \
		-e EMQX_AUTHORIZATION__SOURCES__1__ENABLE=true \
		-e EMQX_AUTHORIZATION__SOURCES__1__PATH=/opt/emqx/etc/acl.conf \
		-v "${WORKSPACE_DEFAULT_PATH}/02_mqtt-cluster/test/local_mqtt/certs:/opt/emqx/etc/certs:ro" \
		-v "${WORKSPACE_DEFAULT_PATH}/02_mqtt-cluster/test/local_mqtt/emqx-acl.conf:/opt/emqx/etc/acl.conf:ro" \
		-v "${WORKSPACE_DEFAULT_PATH}/02_mqtt-cluster/test/local_mqtt/emqx_user-import.csv:/opt/emqx/etc/auth-built-in-db-bootstrap.csv:ro" \
		emqx/emqx:latest
fi

# 2.4 Kafka used by 06_uns_kafka
# trunk-ignore(shellcheck/SC2312)
if [[ -n $(docker ps -aq -f name=uns_kafka) ]]; then
	docker start uns_kafka
else
	CLUSTER_ID=$(openssl rand -base64 32 | tr -dc '[:alnum:]' || true)
	docker run \
		--name uns_kafka \
		--env KAFKA_ADVERTISED_LISTENERS="PLAINTEXT://localhost:9092" \
		--env KAFKA_BROKER_ID=1 \
		--env KAFKA_LISTENER_SECURITY_PROTOCOL_MAP="PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT,CONTROLLER:PLAINTEXT" \
		--env KAFKA_ADVERTISED_LISTENERS="PLAINTEXT://localhost:29092,PLAINTEXT_HOST://localhost:9092" \
		--env KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 \
		--env KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS=0 \
		--env KAFKA_TRANSACTION_STATE_LOG_MIN_ISR=1 \
		--env KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR=1 \
		--env KAFKA_PROCESS_ROLES="broker,controller" \
		--env KAFKA_NODE_ID=1 \
		--env KAFKA_CONTROLLER_QUORUM_VOTERS="1@localhost:29093" \
		--env KAFKA_LISTENERS="PLAINTEXT://localhost:29092,CONTROLLER://localhost:29093,PLAINTEXT_HOST://0.0.0.0:9092" \
		--env KAFKA_INTER_BROKER_LISTENER_NAME="PLAINTEXT" \
		--env KAFKA_CONTROLLER_LISTENER_NAMES="CONTROLLER" \
		--env KAFKA_LOG_DIRS="/tmp/kraft-combined-logs" \
		--env CLUSTER_ID="${CLUSTER_ID}" \
		-p 9092:9092 \
		-d \
		apache/kafka:latest
fi

# 2.5 Merge the secret configurations of the other modules for graphQL service to successfully integrate with the back ends
# always created
INPUT_FILES=$(find "${WORKSPACE_DEFAULT_PATH}" -type f -not -path "${WORKSPACE_DEFAULT_PATH}/07_uns_graphql/*" -name ".secrets.yaml")

# Define the output file
OUTPUT_FILE=${WORKSPACE_DEFAULT_PATH}/07_uns_graphql/conf/.secrets.yaml

merge_command="docker run --rm -v \"/\":/workdir mikefarah/yq eval-all '. as \$item ireduce ({}; . * \$item )'"

# Iterate over the YAML files in the input directory
for yaml_file in ${INPUT_FILES}; do
	merge_command="${merge_command} /workdir${yaml_file}"
done
# Execute the merge command and write the output to the file
eval "${merge_command}" >"${OUTPUT_FILE}"

#install trunk
# trunk-ignore(shellcheck/SC2312)
curl https://get.trunk.io -fsSL | bash -s -- -y
trunk install
