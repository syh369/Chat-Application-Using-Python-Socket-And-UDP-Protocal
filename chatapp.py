import json
import sys
from socket import *
import threading

# Server class
class Server:
    def __init__(self):
        # Init Two tables:
        # "clients_table_in_server" stores clients info
        # "group_table_in_server" stores chat groups
        self.clients_table_in_server = dict()
        self.group_table_in_server = dict()

    # Respond function used by server to send ack to the target server or client
    def serverRespond(self, ack_msg, server_socket, target_ip, target_port):
        ack = f"header:\nack\nmsg:\n{ack_msg}"
        server_socket.sendto(ack.encode(), (target_ip, target_port))
        #print(f"Sent the ack: {ack_msg}")

    # Registraion process in server part
    def serverReg(self, send_socket, user_name, client_ip, client_port):
        self.clients_table_in_server[user_name] = {'client_ip': client_ip,
                                                   'client_port': client_port,
                                                   'status': 'Yes',
                                                   'mode': 'normal'}
        print(f">>> clients table updated")
        msg_tb = json.dumps(self.clients_table_in_server)
        msg = f"header:\nclient_table\ntable:\n{msg_tb}"
        #print(msg_tb)
        for client in self.clients_table_in_server.keys():
            client_ip = self.clients_table_in_server[client]['client_ip']
            client_port = self.clients_table_in_server[client]['client_port']
            send_socket.sendto(msg.encode(), (client_ip, client_port))

    # Deregistration process in server part
    def serverDereg(self, socket, user_name):
        self.clients_table_in_server[user_name]['status'] = 'No'
        print("clients table updated: De-registration")
        msg_tb = json.dumps(self.clients_table_in_server)
        msg = f"header:\nclient_table\ntable:\n{msg_tb}"
        #print(msg_tb)
        for client in self.clients_table_in_server.keys():
            client_ip = self.clients_table_in_server[client]['client_ip']
            client_port = self.clients_table_in_server[client]['client_port']
            socket.sendto(msg.encode(), (client_ip, client_port))

    # Create chat group process in server part
    def serverCreategroup(self, socket, group_name, user_name, client_ip, client_port):
        if group_name in self.group_table_in_server.keys():
            ack_msg = f"existed"
            self.serverRespond(ack_msg, socket, client_ip, client_port)
            print(f"[Client {user_name} creating group {group_name} failed, group already exists]")
        else:
            self.group_table_in_server[group_name] = []
            ack_msg = f"created"
            self.serverRespond(ack_msg, socket, client_ip, client_port)
            print(f"[Client {user_name} created group {group_name} successfully]")

    # List the list of chat groups created in server part
    def serverListgroups(self, socket, client_name, client_ip, client_port):
        group_list = list(self.group_table_in_server.keys())
        #for k in list(self.group_table_in_server.keys()):
        #    group_list.append(k)
        #print(group_list)
        ack_msg = json.dumps(group_list)
        self.serverRespond(ack_msg, socket, client_ip, client_port)
        print(f">>> [Client {client_name} requested listing groups, current groups:]")
        for n in group_list:
            print(f">>> {n}")

    # Join group in server part
    def serverJoingroup(self, socket, client_name, group_name, client_ip, client_port):
        if group_name not in self.group_table_in_server.keys():
            ack_msg = f"non_exist"
            self.serverRespond(ack_msg, socket, client_ip, client_port)
            print(f">>> [Client {client_name} joining group {group_name} failed, group does not exist]")
        else:
            self.group_table_in_server[group_name].append(client_name)
            self.clients_table_in_server[client_name]['mode'] = 'group'
            #print(self.clients_table_in_server)
            join_msg = ("joined", self.clients_table_in_server)
            ack_msg = json.dumps(join_msg)
            self.serverRespond(ack_msg, socket, client_ip, client_port)
            print(f">>> [Client {client_name} joined group {group_name}]")

    # "serverRequestACK" function takes an input argument which is usually a list that
    # stores the value that needed for request a ack from client/server. This function also
    # includes wait and retry mechanism mentioned in the document
    def serverRequestACK(self, args, target_ip, target_port):
        ack = False
        client_name = args[0]
        group_name = args[1]
        msg = args[2]
        s_socket = socket(AF_INET, SOCK_DGRAM)
        s_msg = f"header:\ngroupchat\ngroup:\n{group_name}\nclient:\n{client_name}\nmessage:\n{msg}"
        s_socket.sendto(s_msg.encode(), (target_ip, target_port))
        try:
            s_socket.settimeout(0.5)
            r_msg, addr = s_socket.recvfrom(1024)
            r_msg = r_msg.decode().splitlines()
            # print(r_msg)
            # msg_buf.append(r_msg[3])
            if r_msg[1] == "group_ack":
                ack = True
                s_socket.close()
                return ack
        except Exception:
            ack = False

        if not ack:
            for i in range(5):
                s_socket.sendto(s_msg.encode(), (target_ip, target_port))
                try:
                    s_socket.settimeout(0.5)
                    r_msg, addr = s_socket.recvfrom(1024)
                    r_msg = r_msg.decode().splitlines()
                    #msg_buf.append(r_msg[3])
                    if r_msg[1] == "group_ack":
                        ack = True
                        s_socket.close()
                        return ack
                except Exception:
                    ack = False
                    continue
            s_socket.close()
            return ack

    # List all members in the current group in server part
    def serverListmembers(self, socket, client_name, group_name, client_ip, client_port):
        member_list = self.group_table_in_server[group_name]
        print(member_list)
        ack_msg = json.dumps(member_list)
        self.serverRespond(ack_msg, socket, client_ip, client_port)
        print(f">>> [Client {client_name} requested listing members of group {group_name}:]")
        for m in member_list:
            print(f">>> {m}")

    # Leave the current group in the server part
    def serverLeave(self, socket, client_name, group_name, client_ip, client_port):
        ack_msg = f"confirm_leave"
        try:
            self.group_table_in_server[group_name].remove(client_name)
            self.clients_table_in_server[client_name]['mode'] = "normal"
            self.serverRespond(ack_msg, socket, client_ip, client_port)
        except Exception:
            print(f">>> client {client_name} is not in the group")

    # Send message in group chat in server part
    def serverGroupchat(self, socket, argument, client_ip, client_port):
        ack_msg = f"server_received"
        self.serverRespond(ack_msg, socket, client_ip, client_port)
        client_name = argument[0]
        group_name = argument[1]
        msg = argument[2]
        print(f">>> [Client {client_name} sent group message: {msg}]", end="\n>>> ")
        client_list = self.group_table_in_server[group_name]
        for c in client_list:
            if c == client_name:
                continue
            tc_ip = self.clients_table_in_server[c]['client_ip']
            tc_port = self.clients_table_in_server[c]['client_port']
            if not self.serverRequestACK(argument, tc_ip, tc_port):
                self.group_table_in_server[group_name].remove(c)
                print(f">>> [Client {client_name} not responsive, removed from group {group_name}]", end="\n>>> ")
                #print(f"New group list:{self.group_table_in_server[group_name]}")

    # "serverMode" is the main loop that calls all other methods in server class
    # This method will be called in the main.py to start a server.
    def serverMode(self, port):
        s_sockt = socket(AF_INET, SOCK_DGRAM)
        s_sockt.bind(('', port))
        print('>>> Server is online')

        while True:
            print(">>>", end="")
            msg_buf, c_addr = s_sockt.recvfrom(2048)
            #print("The current client address is:", c_addr)
            msg_buf = msg_buf.decode()
            lines = msg_buf.splitlines()
            header = lines[1]
            if header == "registration":
                ack_msg = f"reg_ack"
                self.serverRespond(ack_msg, s_sockt, c_addr[0], c_addr[1])
                user_name = lines[3]
                # user name exception
                if user_name in self.clients_table_in_server.keys():
                    continue
                self.serverReg(s_sockt, user_name, c_addr[0], c_addr[1])
            elif header == "dereg":
                ack_msg = f"dereg_ack"
                user_name = json.loads(lines[3])[0]
                self.serverRespond(ack_msg, s_sockt, c_addr[0], c_addr[1])
                self.serverDereg(s_sockt, user_name)
            elif header == "create":
                client_name = json.loads(lines[3])[0]
                group_name = json.loads(lines[3])[1]
                self.serverCreategroup(s_sockt, group_name, client_name, c_addr[0], c_addr[1])
                print(self.group_table_in_server)
            elif header == "list":
                client_name = json.loads(lines[3])[0]
                self.serverListgroups(s_sockt, client_name, c_addr[0], c_addr[1])
            elif header == "join":
                client_name = json.loads(lines[3])[0]
                group_name = json.loads(lines[3])[1]
                self.serverJoingroup(s_sockt, client_name, group_name, c_addr[0], c_addr[1])
            elif header == "send_group":
                args = json.loads(lines[3])
                self.serverGroupchat(s_sockt, args, c_addr[0], c_addr[1])
            elif header == "list_members":
                client_name = json.loads(lines[3])[0]
                group_name = json.loads(lines[3])[1]
                self.serverListmembers(s_sockt, client_name, group_name, c_addr[0], c_addr[1])
            elif header == "leave_group":
                client_name = json.loads(lines[3])[0]
                group_name = json.loads(lines[3])[1]
                self.serverLeave(s_sockt, client_name, group_name, c_addr[0], c_addr[1])

# Client class
class Client:
    def __init__(self):
        # Initiate 2 tables and 1 buffer
        # client_table_local stores all clients info in local
        # group_table_in_client stores all group info in local
        # private_message_buffer stores messages from private message
        # in group chat mode and will be shown after leaving the group
        self.client_table_local = dict()
        self.group_table_in_client = dict()
        self.private_message_buffer = []

    # Help check input client port if it is in the accepted range
    def client_check_info(self, client_port):
        check = False
        if client_port < 1024 or client_port > 65535:
            print("Error: The client port is not supported")
        else:
            check = True
        return check

    # Listener thread task: include receiving updated table from the server
    # private message or direct message
    # broadcasted group message
    def clientlisten(self, socket, client_name):
        while True:
            msg, sender_addr = socket.recvfrom(2048)
            msg = msg.decode()
            lines = msg.splitlines()
            header = lines[1]
            if header == "client_table":
                self.client_table_local = json.loads(lines[3])
                print("[Client table updated.]", end="\n>>> ")
                #print(self.client_table_local)
            elif header == "chat":
                    #print(f"sender:{sender_addr}")
                    sender_name = lines[3]
                    sender_msg = lines[5]
                    if self.client_table_local[client_name]['mode'] == 'normal':
                        print(f"{sender_name}: {sender_msg}", end="\n>>> ")
                    elif self.client_table_local[client_name]['mode'] == 'group':
                        self.private_message_buffer.append((sender_name, sender_msg))
                    chat_ack = f"header:\nchat_ack"
                    socket.sendto(chat_ack.encode(), sender_addr)
            elif header == "groupchat":
                group_ack = f"header:\ngroup_ack"
                socket.sendto(group_ack.encode(), sender_addr)
                group_name = lines[3]
                sender_name = lines[5]
                r_msg = lines[7]
                print(f"Group_Message {sender_name}: {r_msg}", end=f"\n>>> ({group_name}) ")

    # Registration process in client part
    def clientReg(self, send_skt, user_name, server_ip, server_port):
        header = 'registration'
        msg = f'header:\n{header}\nclient_name:\n{user_name}'
        send_skt.sendto(msg.encode(), (server_ip, server_port))
        resp, addr = send_skt.recvfrom(2048)
        resp = resp.decode()
        lines = resp.splitlines()
        ack = lines[3]
        if ack == "reg_ack":
            print(">>> [Welcome, You are registered.]", end="\n>>> ")
            #send_skt.close()

    # Deregistration process in client part
    def clientDereg(self, user_name, server_ip, server_port):
        dereg = False
        header = f"dereg"
        argument = [user_name]
        ack_msg = []
        ack = self.requestACK(argument, header, ack_msg, server_ip, server_port)
        if ack:
            dereg = True
            return dereg
        else:
            print("[Server not responding]")
            print("[Exiting]")
            sys.exit()

    # Direct chat process in client part
    def clientChat(self, target_user, msg, server_ip, server_port):
        if self.checkUsername(target_user):
            target_ip = self.client_table_local[target_user]['client_ip']
            target_port = self.client_table_local[target_user]['client_port']
            send_socket = socket(AF_INET, SOCK_DGRAM)
            send_socket.sendto(msg.encode(), (target_ip, target_port))
            print(f"target:{target_ip}:{target_port}")
            # Need time out to wait ack
            try:
                send_socket.settimeout(0.5)
                ack, addr = send_socket.recvfrom(1024)
                ack = ack.decode().splitlines()
                ack = ack[1]
                if ack == "chat_ack":
                    print(f"[Message received by {target_user}.]")
            except Exception as e:
                print(f"[No ACK from {target_user}, message not delivered]")
                header = f"dereg"
                argument = [target_user]
                ack_msg = []
                if not self.requestACK(argument, header, ack_msg, server_ip, server_port):
                    # for m in ack_msg:
                    #     print(m)
                    print("[Server not responding]")
                    print("[Exiting]")
                    send_socket.close()
                    sys.exit()
            send_socket.close()
        else:
            print(f"Error:[{target_user} could not be found]")

    # Create group for client part
    def createGroup(self, group_name, user_name, server_ip, server_port):
        if self.checkUsername(user_name):
            mode = self.client_table_local[user_name]['mode']
            if mode == "normal":
                header = "create"
                ack_msg = []
                argument = [user_name, group_name]
                ack = self.requestACK(argument, header, ack_msg, server_ip, server_port)
                if ack and ack_msg[0] == "existed":
                    print(f"[Group {group_name} already exists.]")
                elif ack and ack_msg[0] == "created":
                    print(f"[Group {group_name} created by Server.]")
                elif not ack:
                    print("[Server not responding]")
                    print("[Exiting]")
                    sys.exit()

    # List all groups for client part
    def clientListgroups(self, client_name, server_ip, server_port):
        header = "list"
        ack_msg = []
        argument = [client_name]
        ack = self.requestACK(argument, header, ack_msg, server_ip, server_port)
        if ack:
            print("[Available group chats:]")
            group_names = json.loads(ack_msg[0])
            for n in group_names:
                print(f">>> {n}")
        else:
            print("[Server not responding]")
            print("[Exiting]")
            sys.exit()

    # Join in a group chat for client part
    def clientJoingroup(self, client_name, group_name, server_ip, server_port):
        mode = self.client_table_local[client_name]['mode']
        if mode == "normal":
            header = "join"
            ack_msg = []
            argument = [client_name, group_name]
            ack = self.requestACK(argument, header, ack_msg, server_ip, server_port)
            if ack and ack_msg[0] == "non_exist":
                print(f"[Group {group_name} does not exist]")
            elif ack and json.loads(ack_msg[0])[0] == "joined":
                print(f"[Entered group {group_name} successfully]")
                self.client_table_local = json.loads(ack_msg[0])[1]
                #print(self.client_table_local)
            elif not ack:
                print("[Server not responding]")
                print("[Exiting]")
                sys.exit()
        #elif mode == "group":

    # "requestACK" function takes an input argument which is usually a list that
    # stores the value that needed for request a ack from client/server. This function also
    # includes wait and retry mechanism mentioned in the document
    def requestACK(self, argument, header, msg_buf, server_ip, server_port):
        if self.checkUsername(argument[0]):
            ack = False
            send_skt = socket(AF_INET, SOCK_DGRAM)
            argument = json.dumps(argument)
            s_msg = f"header:\n{header}\nargument:\n{argument}"
            send_skt.sendto(s_msg.encode(), (server_ip, server_port))
            try:
                send_skt.settimeout(0.5)
                r_msg, addr = send_skt.recvfrom(1024)
                r_msg = r_msg.decode().splitlines()
                #print(r_msg)
                msg_buf.append(r_msg[3])
                if r_msg[1] == "ack":
                    ack = True
                    send_skt.close()
                    return ack
            except Exception:
                ack = False

            if not ack:
                for i in range(5):
                    send_skt.sendto(s_msg.encode(), (server_ip, server_port))
                    try:
                        send_skt.settimeout(0.5)
                        r_msg, addr = send_skt.recvfrom(1024)
                        r_msg = r_msg.decode().splitlines()
                        msg_buf.append(r_msg[3])
                        if r_msg[1] == "ack":
                            ack = True
                            send_skt.close()
                            return ack
                    except Exception:
                        ack = False
                        continue
                #print("[Server not responding]")
                #print("[Exiting]")
                send_skt.close()
                return ack
        else:
            print(f"Error:[{argument} could not be found]")

    # Check if the input client name is in the table
    def checkUsername(self, name):
        try:
            if name in self.client_table_local.keys():
                return True
        except KeyError as e:
            print(e)
            return False

    # Send message in group chat mode for client part
    def clientGroupsendmsg(self, client_name, group_name, msg, server_ip, server_port):
        header = "send_group"
        args = [client_name, group_name, msg]
        msg_buf = []
        ack = self.requestACK(args, header, msg_buf, server_ip, server_port)
        if ack and msg_buf[0] == "server_received":
            print("[Message received by Server.]")
        elif not ack:
            print("[Server not responding]")
            print("[Exiting]")
            sys.exit()

    # List all current group member for client part
    def clientListMembers(self, client_name, group_name, server_ip, server_port):
        header = "list_members"
        ack_msg = []
        argument = [client_name, group_name]
        ack = self.requestACK(argument, header, ack_msg, server_ip, server_port)
        if ack:
            print(f">>> {group_name} [Members in the group {group_name}:]")
            member_names = json.loads(ack_msg[0])
            for m in member_names:
                print(f">>> {group_name} {m}")
        else:
            print(f">>> {group_name} [Server not responding]")
            print(f">>> {group_name} [Exiting]")
            sys.exit()

    # Leave the group for client part
    def clientLeave(self, client_name, group_name, server_ip, server_port):
        leave = False
        header = "leave_group"
        ack_msg = []
        argument = [client_name, group_name]
        ack = self.requestACK(argument, header, ack_msg, server_ip, server_port)
        if ack and ack_msg[0] == "confirm_leave":
            print(f">>> Leave group chat {group_name}:]")
            leave = True
            return leave
        elif not ack:
            print(f">>> {group_name} [Server not responding]")
            print(f">>> {group_name} [Exiting]")
            sys.exit()

    # Create group chat loop that will have specified prompt for the client part
    def clientGroupchat(self, client_name, group_name, server_ip, server_port):
        client_mode = self.client_table_local[client_name]['mode']
        while client_mode == "group":
            print(">>>", end=f" ({group_name}) ")
            temp = input()
            input_list = temp.split()
            try:
                header = input_list[0]
            except:
                print("Error: Invalid input, try input again")
                continue

            if header == "send_group":
                message = ""
                for i in range(1, len(input_list)):
                    message = message + input_list[i] + " "
                #msg_to_send = f'header:\n{header}\nuser:\n{client_name}\nmessage:\n{message}'
                self.clientGroupsendmsg(client_name, group_name, message, server_ip, server_port)
            elif header == "list_members":
                self.clientListMembers(client_name, group_name, server_ip, server_port)
            elif header == "leave_group":
                if self.clientLeave(client_name, group_name, server_ip, server_port):
                    # After leaving the group, print out all private messages received during
                    # group chat mode and break the group chat loop and return back to the main
                    # loop.
                    for tp in self.private_message_buffer:
                        p_msg = f">>> {tp[0]}: {tp[1]}"
                        print(p_msg)
                    break
                else:
                    continue
    # This is the main loop for client to perform all tasks mentioned in the documents.
    # This method will be called in the main.py to start a client.
    def clientMode(self, user_name, server_ip, server_port, client_port):
        if self.client_check_info(client_port):
            reg_socket = socket(AF_INET, SOCK_DGRAM)
            reg_socket.bind(("", client_port))
            self.clientReg(reg_socket, user_name, server_ip, server_port)
            # Multithreading
            listen = threading.Thread(target=self.clientlisten, args=(reg_socket,user_name))
            listen.start()
            print(f">>> [This is clinet {user_name} listening at port {client_port}]")
            while True:
                #client_mode = self.client_table_local[user_name]['mode']
                #if client_mode == "normal":
                print(">>>", end=" ")
                    #print(">>>", end=f" {user_name}")
                temp = input()
                input_list = temp.split()
                try:
                    header = input_list[0]
                except:
                    print("Error: Invalid input, try input again")
                    continue

                if header == "send":
                    target_user = input_list[1]
                    message = ""
                    for i in range(2, len(input_list)):
                        message = message + input_list[i] + " "
                    msg_to_send = f'header:\nchat\nuser:\n{user_name}\nmessage:\n{message}'
                    self.clientChat(target_user, msg_to_send, server_ip, server_port)
                    #c_socket.sendto(msg_to_send.encode(), (server_ip, server_port))
                    #print("message is sent")
                elif header == "dereg":
                    dereg_name = input_list[1]
                    if self.clientDereg(dereg_name, server_ip, server_port):
                        print("[You are Offline. Bye.]")
                        try:
                            reg_socket.close()
                            #listen.join()
                        except Exception:
                            sys.exit()
                elif header == "create_group":
                    group_name = input_list[1]
                    self.createGroup(group_name, user_name, server_ip, server_port)
                elif header == "list_groups":
                    self.clientListgroups(user_name, server_ip, server_port)
                elif header == "join_group":
                    group_name = input_list[1]
                    self.clientJoingroup(user_name, group_name, server_ip, server_port)
                    self.clientGroupchat(user_name, group_name, server_ip, server_port)
        else:
            print("Retry Input", end="\n")


# Initiate a new server and client class
s = Server()
c = Client()

if __name__ == '__main__':
    mode = sys.argv[1]
    # "-s" initiate a server
    if mode == "-s":
        s_port = int(sys.argv[2])
        s.serverMode(s_port)
    # "-c" initiate a client
    if mode == "-c":
        user_name = sys.argv[2]
        server_ip = sys.argv[3]
        server_port = int(sys.argv[4])
        client_port = int(sys.argv[5])

        c.clientMode(user_name, server_ip, server_port, client_port)