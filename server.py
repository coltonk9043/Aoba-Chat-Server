import select
import signal
import sys
import socket
import json
import logging

# Consts
BUFFER_SIZE = 2048

DARKRED = "§4"
RED = "§c"
GOLD = "§6"
YELLOW = "§e"
GREEN = "§2"
LIME = "§a"
AQUA = "§b"
CYAN = "§3"
DARKBLUE = "§1"
BLUE = "§9"
MAGENTA = "§d"
PURPLE = "§5"
WHITE = "§f"
GRAY = "§7"
DARKGRAY = "§8"
BLACK = "§0"

""" Json Formatting
{
    "action": (connect/disconnect/message)

    if connect
    "username" : (username)

    if disconnect
    NOTHING!
	if(message)
    message: (message)
    to: (null / @user)
}

"""
# Variables
clients = {}

# Setup Logging
logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.DEBUG, handlers=[logging.FileHandler("debug.log"), logging.StreamHandler()])

def encode(message):
    return (message + "\r\n").encode()

# Defines a function that will be called when CTRL+C is pressed.
def signal_handler(sig, frame):
    for client in clients:
        client.send(encode("DISCONNECT CHAT/1.0"))
    logging.info('Interrupt received, shutting down ...')
    sys.exit(0)

# Main Function
def main():
    signal.signal(signal.SIGINT, signal_handler)
    # Binds the server socket to the local ip.
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSocket.bind(('0.0.0.0', 80))
    # Gets the port of the socket.
    port = serverSocket.getsockname()[1]
    serverSocket.listen(10)
    sockets_list = [serverSocket]
    
    logging.info("Will wait for client connections at port " + str(port))
    logging.info("Waiting for incoming client connections...")

    # Infinite loop to run whilst the application is active.
    while True:
        # Gets the sockets of which we are listening to from the select library.
        read_sockets, write_sockets, error_sockets = select.select(sockets_list, sockets_list, sockets_list)
        # For every socket that is in the read_sockets array.
        for readSocket in read_sockets:
            # If the read socket is the server socket, that means there is an incoming connection request.
            if readSocket == serverSocket:
                try:
                    # Accept the request
                    client_socket, client_address = serverSocket.accept()
                    # Fetch the registration request from the client that was connected.
                    registration = client_socket.recv(BUFFER_SIZE).decode()
                    jsonResult = json.loads(registration) 

                    if("action" in jsonResult and "username" in jsonResult):
                        if(jsonResult["action"] == "connect"):
                            # If all succeeds, adds it to the socket list.
                            sockets_list.append(client_socket)
                            # Adds the client's name to a list.
                            name = jsonResult["username"]
                            clients[client_socket] = name
                            logging.info("Accepted connection from client address: " + client_socket.getsockname())
                            logging.info("Connection to client established, waiting to receive messages from user '" + name + "'...")
                            client_socket.send(encode(json.dumps({ 'user': 'SERVER', 'message' : "200 Registration successful"}, ensure_ascii=False)))
                        else:
                            client_socket.send(encode(json.dumps({ 'user': 'SERVER','message' : "400 Invalid registration"}, ensure_ascii=False)))
                            continue
                except ValueError as valueError:
                    break
                except Exception as e:
                    logging.error("Exception occured in registration: " + registration + "\n\n" + repr(e))
            else:
                try:
                    # If a message is received from a client.
                    user = clients[readSocket]
                    message = readSocket.recv(BUFFER_SIZE).decode()
                    jsonResult = json.loads(message) 

                    if("action" in jsonResult):

                        if(jsonResult["action"] == "disconnect"):
                            logging.info("Disconnecting " + user + " from the server.")
                            sockets_list.remove(readSocket)
                            clients.pop(readSocket)
                        elif (jsonResult["action"] == "message"):
                            # If the message is empty, ignore it.
                            send_message = jsonResult["message"]
                            logging.info("<" + user + "> " + send_message)
                            for writeSocket in write_sockets:
                                sendUser = clients[writeSocket]
                                writeSocket.send(encode(json.dumps({ 'user': user, 'message' : send_message}, ensure_ascii=False)))
                except ConnectionResetError as e:
                    if user is not None:
                        logging.info("Disconnecting " + user + " from the server.")
                        sockets_list.remove(readSocket)
                        clients.pop(readSocket)
                except Exception as e: 
                    logging.error("Exception occured: " + repr(e))
# Runs the main function.
main()
