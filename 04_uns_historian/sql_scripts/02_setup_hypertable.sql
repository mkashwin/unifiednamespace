CREATE TABLE unifiednamespace (
  time TIMESTAMPTZ NOT NULL,
  topic text NOT NULL,
  client_id text,
  mqtt_msg JSONB
);

SELECT create_hypertable('unifiednamespace','time'); 
