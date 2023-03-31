# Yuanhao Shen, ys3609
## CSEE4119_PA1

For PA1, I used python as the programming language for socket programming. The libraries or packages are all pre built-in python packages, includes: json, sys, socket, and threading. 

My application includes two classes:
- Server
- Client

There are two supported mode: 
- Normal mode: Client to client
- Group chat mode

## Normal Mode:

For the _Normal Mode_, a server need to be online before all the creation of clients. 

- Initiate a server

```sh
python3 chatapp.py -s 4000
```

This command will initate a server at current machine ip address at port 4000

After a initiation of a server, we can now initiate clients.

- Initiate a client

```sh
python3 chatapp.py -c localhost 4000 2000
```

This command will initate a client with target server ip address and target server port 4000 at local client port 2000.

Immediately enter this command into the client terminal, the client will start a registration process to the server, which will enter current client's address, registration status, and chat mode into the server. The server will store these info into a table and every client's behavior will update this table and server will broadcast this table to all registered(online) clients.

There are several command actions are supported for _Normal Mode_. 

- send: send direct message between clients
- dereg: dereg target clients from the server
- create_group: client create a chat group
- list_groups: request to lists all existed chat group
- join_group: client join a specific chat group

## Group chat mode

For group chat mode, the client should first create a chat group on the server. Then, after joining this created group, all members(clients) in this group will send message to the server. The server then broadcast the message to all the other clients in the group. During the group chat mode, the private message are saved in a buffer which later will shown after the client leave the group chat. For _Group Chat Mode_. sever instructions are supported:

- send_group: client send message to the server, then server broadcast the message to other clients in the group
- list_members: request list all current members in the chat group
- leave_group: client leave the chat group and return normal mode
- dereg: dereg a client if it doesn't send ack to the server or reply


## Test:

## Test-case 1:

1. Start server
2. start client x(the table should be sent from server to x)
3. start client y(the table should be sent from server to x and y)
4. start client z(the table should be sent from server to x and y and z)
5. chat x -> y, y->z, ... , x ->z (All combinations)
6. dereg x (the table should be sent to y, z. x should receive ’ack’)
7. chat y->x (this should fail, y should display that the message failed)
8. chat z->x (same as above)
9. y, z : exit

Result:

Server: 

```sh
(venv) imsyh16@Yuanhaos-Laptop programming_assignment % python3 chatapp.py -s 4000
>>> Server is online
>>> clients table updated
>>> clients table updated
>>> clients table updated
>>>clients table updated: De-registration
>>>clients table updated: De-registration
>>>clients table updated: De-registration
```

Client x: 

```sh
(venv) imsyh16@Yuanhaos-Laptop programming_assignment % python3 chatapp.py -c x localhost 4000 1600
>>> [Welcome, You are registered.]
>>> [Client table updated.]
>>> >>> [This is clinet x listening at port 1600]
>>> [Client table updated.]
>>> [Client table updated.]
>>> send y 1
target:127.0.0.1:1800
[Message received by y.]
>>> send z 2
target:127.0.0.1:2000
[Message received by z.]
>>> y: 3 
>>> z: 4 
>>> dereg x
[You are Offline. Bye.]
```

Client y: 

```sh
(venv) imsyh16@Yuanhaos-Laptop programming_assignment % python3 main.py -c y localhost 4000 1800   
>>> [Welcome, You are registered.]
>>> [Client table updated.]
>>> >>> [This is clinet y listening at port 1800]
>>> [Client table updated.]
>>> x: 1 
>>> send x 3
target:127.0.0.1:1600
[Message received by x.]
>>> send z 5
target:127.0.0.1:2000
[Message received by z.]
>>> z: 6 
>>> [Client table updated.]
>>> send x hi
target:127.0.0.1:1600
[No ACK from x, message not delivered]
>>> [Client table updated.]
>>> [Client table updated.]
>>> 
```

Client z: 

```sh
(venv) imsyh16@Yuanhaos-Laptop programming_assignment % python3 main.py -c z localhost 4000 2000   
>>> [Welcome, You are registered.]
>>> [Client table updated.]
>>> >>> [This is clinet z listening at port 2000]
>>> x: 2 
>>> send x 4
target:127.0.0.1:1600
[Message received by x.]
>>> y: 5 
>>> send y 6
target:127.0.0.1:1800
[Message received by y.]
>>> [Client table updated.]
>>> [Client table updated.]
>>> send x bye
target:127.0.0.1:1600
[No ACK from x, message not delivered]
>>> [Client table updated.]
>>> 
```

## Test-case 2:

1. start server
2. start client x (the table should be sent from server to x )
3. start client y (the table should be sent from server to x and y)
4. dereg y
5. server exit
6. send message x-> y (will fail with both y and server, so should make 5 attempts and exit)

Result:

Server: 

```sh
(venv) imsyh16@Yuanhaos-Laptop programming_assignment % python3 chatapp.py -s 4000
>>> Server is online
>>> clients table updated
>>> clients table updated
>>>clients table updated: De-registration
```

Client x: 

```sh
(venv) imsyh16@Yuanhaos-Laptop programming_assignment % python3 chatapp.py -c x localhost 4000 1600
>>> [Welcome, You are registered.]
>>> [Client table updated.]
>>> >>> [This is clinet x listening at port 1600]
>>> [Client table updated.]
>>> [Client table updated.]
>>> send y hello
target:127.0.0.1:1800
[No ACK from y, message not delivered]
[Server not responding]
[Exiting]
```

Client y: 

```sh
(venv) imsyh16@Yuanhaos-Laptop programming_assignment % python3 main.py -c y localhost 4000 1800   
>>> [Welcome, You are registered.]
>>> [Client table updated.]
>>> >>> [This is clinet y listening at port 1800]
>>> dereg y
[You are Offline. Bye.]
```

## Test-case 3:

- Start server
- Start client x (the table should be sent from server to x )
- start client y (the table should be sent from server to x and y)
- start client z (the table should be sent from server to x , y and z)
- Start client a (the table should be sent from server to x , y, z, and a)
- client x sends $ >>> create_group <group_name> command to the server
- clients y and z join <group_name>
- send group message x-> y,z , but a does not receive the message
- Send private message a-> z , z stores the message locally and does not display the message until after it
exits the chat room.

_Result_:
Server: 

```sh
(venv) imsyh16@Yuanhaos-Laptop programming_assignment % python3 chatapp.py -s 4000
>>> Server is online
>>> clients table updated
>>> clients table updated
>>> clients table updated
>>> clients table updated
>>>[Client x created group g1 successfully]
{'g1': []}
>>> [Client x joined group g1]
>>> [Client y joined group g1]
>>> [Client z joined group g1]
>>> [Client a requested listing groups, current groups:]
>>> g1
>>> [Client x sent group message: hello ]
>>> 
```

Client x:

```sh
(venv) imsyh16@Yuanhaos-Laptop programming_assignment % python3 chatapp.py -c x localhost 4000 1600
>>> [Welcome, You are registered.]
>>> [Client table updated.]
>>> >>> [This is clinet x listening at port 1600]
>>> [Client table updated.]
>>> [Client table updated.]
>>> [Client table updated.]
>>> create_group g1
[Group g1 created by Server.]
>>> join_group g1
[Entered group g1 successfully]
>>> (g1) send_group hello
[Message received by Server.]
>>> (g1) 
```

Client y:

```sh
(venv) imsyh16@Yuanhaos-Laptop programming_assignment % python3 main.py -c y localhost 4000 1800   
>>> [Welcome, You are registered.]
>>> [Client table updated.]
>>> >>> [This is clinet y listening at port 1800]
>>> [Client table updated.]
>>> [Client table updated.]
>>> join_group g1
[Entered group g1 successfully]
>>> (g1) Group_Message x: hello 
>>> (g1) 
```

Client z:

```sh
(venv) imsyh16@Yuanhaos-Laptop programming_assignment % python3 main.py -c z localhost 4000 2000   
>>> [Welcome, You are registered.]
>>> [Client table updated.]
>>> >>> [This is clinet z listening at port 2000]
>>> [Client table updated.]
>>> join_group g1
[Entered group g1 successfully]
>>> (g1) Group_Message x: hello 
>>> (g1) leave_group
>>> Leave group chat g1:]
>>> a: hi,im a 
>>> a: bye 
>>> 
```

Client a:

```sh
(venv) imsyh16@Yuanhaos-Laptop programming_assignment % python3 main.py -c a localhost 4000 2200   
>>> [Welcome, You are registered.]
>>> >>> [This is clinet a listening at port 2200]
>>> [Client table updated.]
>>> list_groups
[Available group chats:]
>>> g1
>>> send z hi,im a
target:127.0.0.1:2000
[Message received by z.]
>>> send z bye
target:127.0.0.1:2000
[Message received by z.]
>>> 
```

## Bugs/potential updates:

For my application, I have few details and bugs that could be improved in the future.
First, for the dereg process, I closed listening socket that passed to the another thread before exit the program. This close will raise a exception and I didn't handle this error gracely. However, this bug will not have huge effect on the exit of the dereg client program.

Second, I didn't inlcude the situation that a single client will be in multiple group chat. My application now can only handle a client that will enter a single group chat.




