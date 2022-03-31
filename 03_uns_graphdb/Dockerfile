FROM python:3

ADD ./src/uns_graphdb/*.py /src/uns_graphdb
ADD ../02_mqtt-cluster/src/uns_mqtt/*.py  /src/uns_mqtt
ADD requirements.txt /

RUN pip install -r requirements.txt
CMD [ "python", "/src/uns_graphdb/uns_mqtt_graphdb.py" ]
