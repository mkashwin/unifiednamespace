CREATE TABLE unifiednamespace (
  time TIMESTAMPTZ NOT NULL,
  topic text NOT NULL,
  client_id text,
  mqtt_msg JSONB, 
  CONSTRAINT unique_event UNIQUE (time, topic, client_id, mqtt_msg)
);

SELECT create_hypertable('unifiednamespace','time'); 
