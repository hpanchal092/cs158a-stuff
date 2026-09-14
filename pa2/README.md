# Leader Election Assignment

To run the leader election process, adjust the configuration file to the proper
IP addresses and ports, then simply run the `myleprocess.py` with any python
installation. Press enter once all nodes are running. 

Ex:
```
$ python3 myleprocess.py
Reading config file...
Establishing server connection with message sender...

Press enter when everyone is ready...

Server connection with ('127.0.0.1', 51166) successfully established.
Establishing client connection with message recepient...
Client connection successfully established.
Starting process, my uuid=1e352378-8849-4320-8ee5-2a409b5a6f66
Sent: uuid=1e352378-8849-4320-8ee5-2a409b5a6f66, flag=0
Received: uuid=471547f1-af3a-45d5-95fa-c6314e5af9f7, flag=0, greater, 0
Sent: uuid=471547f1-af3a-45d5-95fa-c6314e5af9f7, flag=0
Received: uuid=f94b4040-bd94-4075-bef9-ed0c0443336e, flag=0, greater, 0
Sent: uuid=f94b4040-bd94-4075-bef9-ed0c0443336e, flag=0
Received: uuid=f94b4040-bd94-4075-bef9-ed0c0443336e, flag=1, greater, 1
Sent: uuid=f94b4040-bd94-4075-bef9-ed0c0443336e, flag=1
Leader is decided to f94b4040-bd94-4075-bef9-ed0c0443336e
```
