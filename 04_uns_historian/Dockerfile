FROM python:3

ADD ./src/uns_historian/*.py /src/uns_historian/
ADD ../02_mqtt-cluster/src/uns_mqtt/*.py  /src/uns_mqtt/
ADD requirements.txt /

RUN pip install -r requirements.txt
CMD [ "python", "/src/uns_historian/uns_mqtt_historian.py" ]
