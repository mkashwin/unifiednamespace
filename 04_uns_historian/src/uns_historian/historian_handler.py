from curses.ascii import FF
import datetime
import time
from config import settings

import json
import psycopg2
import logging

#Logger
LOGGER = logging.getLogger(__name__)
MAX_RETRIES:int = 5
SLEEP_BTW_ATTEMPT = 10 # seconds to sleep between retries 

class HistorianHandler:

    tsdb_conn = None
    tsdb_cursor = None

    def __init__(self, hostname: str, port:int, database:str, table:str, user: str, password: str, sslmode:str):
        """
        Parameters
        -----------
        hostname: str, 
        port:int, 
        database:str, 
        table:str, 
        user: str,
        password: str
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


    def connect(self, retry:int = 0):
        """
        Connect to the postgres DB. Allow for reconnects tries up to MAX_RETRIES and sleep
        SLEEP_BTW_ATTEMPT seconds between retry attempts 
        This is required because psycopg2 doesn't support reconnecting connections which time out / expire
        """
        if ( self.tsdb_conn is None ):
            try:
                self.tsdb_conn = psycopg2.connect(
                                    host=self.hostname,
                                    port=self.port,
                                    database=self.database,
                                    user=self.user,
                                    password=self.password,
                                    sslmode = self.sslmode)
                self.tsdb_conn.set_session(autocommit=True) 
                return self.tsdb_conn
            except psycopg2.OperationalError as ex:
                if(self.tsdb_conn is None and retry >= MAX_RETRIES ):
                    LOGGER.error("No. of retries exceeded %s", MAX_RETRIES,stack_info=True, exc_info=True)
                    raise ex
                else :
                    retry += 1
                    LOGGER.error("Error Connecting to %s. Error:", self.database, str(ex))
                    time.sleep(SLEEP_BTW_ATTEMPT)
                    self.connect(retry=retry)
            except Exception as ex:
                LOGGER.error("Error Connecting to %s. Unable to retry. Error:", self.database, str(ex))
                raise ex

    def getcursor(self):
        if(self.tsdb_cursor is None or self.tsdb_cursor.closed) :
            if(self.tsdb_conn is None):
                self.connect()
            self.tsdb_cursor = self.tsdb_conn.cursor()
        return self.tsdb_cursor

    def close(self):
        if(self.tsdb_cursor is not None):
            try:
                self.tsdb_cursor.close()
            except Exception as ex:
                LOGGER.error("Error closing the cursor %s", str(ex),stack_info=True, exc_info=True)
        # in case there was any error in closing the cursor, attempt closing the connection too
        if(self.tsdb_conn is not None):
            try:
                self.tsdb_conn.close()
                self.tsdb_conn = None
            except Exception as ex:
                LOGGER.error("Error closing the connection %s", str(ex),stack_info=True, exc_info=True)
    

    def persistMQTTmsg(self,
                       client_id:str, 
                       topic: str,
                       timestamp,
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
        else :
            _timestamp = datetime.date.fromtimestamp(timestamp)

        sql_cmd = f"""INSERT INTO {self.table} ( time, topic, client_id, mqtt_msg )
                        VALUES (%s,%s,%s,%s)
                        RETURNING *;"""
        executeSQLcmd()

        def executeSQLcmd(retry: int = 0 ) :
            with self.getcursor() as (cursor, ex):
                if(ex) :
                    #handle exception
                    LOGGER.error("Error persisting message to the database. Error: %s", str(ex),stack_info=True, exc_info=True)
                    if (retry >= MAX_RETRIES):
                        raise ex
                    else :
                        retry +=1
                        ##Close the stale connection.
                        self.close()
                        time.sleep(SLEEP_BTW_ATTEMPT)
                        executeSQLcmd(retry)
                else :
                    cursor.execute(sql_cmd,(_timestamp, topic, client_id, message))                  
