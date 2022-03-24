import datetime
from config import settings

import json
import psycopg2
import logging

#Logger
LOGGER = logging.getLogger(__name__)


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
        # TODO support other authentications like cert based authentication
        try: 
            self.tsdb_conn = psycopg2.connect(
                                    host=hostname,
                                    port=port,
                                    database=database,
                                    user=user,
                                    password=password,
                                    sslmode = sslmode)
            self.tsdb_conn.set_session(autocommit=True)  
            self.tsdb_cursor = self.tsdb_conn.cursor()
            self.table = table
            LOGGER.debug("Successfully connected to the Historian DB")                          
        except psycopg2.Error as ex:
            LOGGER.error("Unable to connect to the Historian DB: %s", str(ex),stack_info=True, exc_info=True)    


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
            except Exception as ex:
                LOGGER.error("Error closing the cursor %s", str(ex),stack_info=True, exc_info=True)
    

    def persistMQTTmsg(self,
                       client_id:str, 
                       topic: str,
                       timestamp,
                       message: str,
                       ignored_attributes: dict = None):
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
        ignored_attributes: dict topic:attribute or topic:list(attribute)
            mapping of topic to attributes which should not be persisted
        """
        if timestamp is None:
            time = datetime.datetime.now()
        else :
            time = datetime.date.fromtimestamp(timestamp)

        sql_request = f"""INSERT INTO {self.table} ( time, topic, client_id, mqtt_msg )
                        VALUES (%s,%s,%s,%s)
                        RETURNING *;"""
        if (self.tsdb_cursor is not None):
            try:
                self.tsdb_cursor.execute(sql_request,(time, topic, client_id, message))
            except Exception as ex:
                LOGGER.error("Error persisting message to the database %s", str(ex),stack_info=True, exc_info=True)            
        else :
             LOGGER.error("Error persisting message to the database. Cursor is None")
             raise None
        #TODO
