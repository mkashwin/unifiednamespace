import datetime
import logging
import time

import psycopg2

# Logger
LOGGER = logging.getLogger(__name__)
MAX_RETRIES: int = 5
SLEEP_BTW_ATTEMPT = 10  # seconds to sleep between retries


class HistorianHandler:

    timescale_db_conn = None
    timescale_db_cursor = None

    def __init__(self, hostname: str, port: int, database: str, table: str,
                 user: str, password: str, sslmode: str):
        """
        Parameters
        -----------
        hostname: str,
        port:int,
        database:str,
        table:str,
        user: str,
        password: str,
        sslmode: str
        """
        self.hostname = hostname
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.sslmode = sslmode
        self.table = table

        self.connect()
        LOGGER.debug("Successfully connected to the Historian DB")

    def connect(self, retry: int = 0):
        """
        Connect to the postgres DB. Allow for reconnects tries up to MAX_RETRIES and sleep
        SLEEP_BTW_ATTEMPT seconds between retry attempts
        This is required because psycopg2 doesn't support reconnecting connections which time out / expire
        """
        if (self.timescale_db_conn is None):
            try:
                self.timescale_db_conn = psycopg2.connect(
                    host=self.hostname,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password,
                    sslmode=self.sslmode)
                self.timescale_db_conn.set_session(autocommit=True)
                return self.timescale_db_conn
            except psycopg2.OperationalError as ex:
                if (self.timescale_db_conn is None and retry >= MAX_RETRIES):
                    LOGGER.error("No. of retries exceeded %s",
                                 str(MAX_RETRIES),
                                 stack_info=True,
                                 exc_info=True)
                    raise ex
                else:
                    retry += 1
                    LOGGER.error("Error Connecting to %s. Error: %s",
                                 self.database,
                                 str(ex),
                                 stack_info=True,
                                 exc_info=True)
                    time.sleep(SLEEP_BTW_ATTEMPT)
                    self.connect(retry=retry)
            except Exception as ex:
                LOGGER.error(
                    "Error Connecting to %s. Unable to retry. Error:%s",
                    self.database,
                    str(ex),
                    stack_info=True,
                    exc_info=True)
                raise ex

    def getcursor(self):
        if (self.timescale_db_cursor is None
                or self.timescale_db_cursor.closed):
            if (self.timescale_db_conn is None):
                self.connect()
            self.timescale_db_cursor = self.timescale_db_conn.cursor()
        return self.timescale_db_cursor

    def close(self):
        if (self.timescale_db_cursor is not None):
            try:
                self.timescale_db_cursor.close()
            except Exception as ex:
                LOGGER.error("Error closing the cursor %s",
                             str(ex),
                             stack_info=True,
                             exc_info=True)
        # in case there was any error in closing the cursor, attempt closing the connection too
        if (self.timescale_db_conn is not None):
            try:
                self.timescale_db_conn.close()
                self.timescale_db_conn = None
            except Exception as ex:
                LOGGER.error("Error closing the connection %s",
                             str(ex),
                             stack_info=True,
                             exc_info=True)

    def persistMQTTmsg(self, client_id: str, topic: str, timestamp,
                       message: str):
        """
        Persists all nodes and the message as attributes to the leaf node
        ----------
        client_id:
            Identifier for the Subscriber
        topic: str
            The topic on which the message was sent
        timestamp
            The timestamp of the message received
        message: str
            The MQTT message. String is expected to be JSON formatted
        """
        if timestamp is None:
            _timestamp = datetime.datetime.now()
        else:
            _timestamp = datetime.date.fromtimestamp(timestamp)

        sql_cmd = f"""INSERT INTO {self.table} ( time, topic, client_id, mqtt_msg )
                        VALUES (%s,%s,%s,%s)
                        RETURNING *;"""

        def executeSQLcmd(retry: int = 0):
            """
            inline method to enable retry
            """
            try:
                with self.getcursor() as cursor:
                    cursor.execute(sql_cmd,
                                   (_timestamp, topic, client_id, message))
            except (psycopg2.DataError, psycopg2.OperationalError) as ex:
                # handle exception
                LOGGER.error(
                    "Error persisting message to the database. Error: %s",
                    str(ex),
                    stack_info=True,
                    exc_info=True)
                if (retry >= MAX_RETRIES):
                    raise ex
                else:
                    retry += 1
                    # Close the stale connection.
                    self.close()
                    time.sleep(SLEEP_BTW_ATTEMPT)
                    executeSQLcmd(retry)

        # ---------------------------------------------------------------------------------------------------
        executeSQLcmd()
