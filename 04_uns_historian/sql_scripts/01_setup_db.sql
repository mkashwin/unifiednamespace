CREATE database uns_historian;

\c uns_historian;

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Commenting this so that dbuser are created interactively with the
-- passwords not stored in the file

-- CREATE ROLE uns_dba 
-- CREATEDB
-- CREATEROLE
-- LOGIN 
-- PASSWORD 'uns_dba_password';

-- CREATE ROLE uns_dbuser 
-- CREATEDB
-- CREATEROLE
-- LOGIN 
-- PASSWORD 'uns_password';

ALTER DATABASE uns_historian OWNER TO uns_dbuser;