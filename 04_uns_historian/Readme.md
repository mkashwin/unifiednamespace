# Application to store messages to Historian 

It makes since to have the historian connect only to the corporate / cloud instance since the factory doesnt neccessarily need the history of all messages. The historian should  subscribe to '**#**' 


## The Logic for persisting the message into the historian
The historian will be persisting all the MQTT messages in the raw format directly after extracting the timestamp from the message
The message format is expected to be in JSON and should have an attribute `timestamp`
If this attribute is missing the application will use the current time 
```python
datetime.datetime.now()
```

### Tag extraction from Topic
Based on the topic tree as per the ISA-95 part 2 specifications
> \<enterprise\>/\<facility\>/\<area\>/\<line\>\<device\>

For each message recieved by the application we also parse the topic on which it is posted
The parent folders / topic names will be extracted and stored at database tags to facilitate indexes and faster searching for the message.
The final leaf topic name will be stored as field along with the timestamp and message 


### Tag extraction from message
TBD.


## Limitations 

