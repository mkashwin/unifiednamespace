#!/bin/bash
sed -i 's/  # noqa: ARG002//' 07_uns_graphql/src/uns_graphql/type/mqtt_event.py
sed -i 's/  # noqa: S311//' 07_uns_graphql/src/uns_graphql/subscriptions/mqtt.py
sed -i 's/  # noqa: F401//' 07_uns_graphql/src/uns_graphql/subscriptions/__init__.py
sed -i 's/  # noqa: E501//' 07_uns_graphql/src/uns_graphql/queries/graph.py
sed -i 's/  # noqa: S608//' 07_uns_graphql/src/uns_graphql/backend/historian.py
