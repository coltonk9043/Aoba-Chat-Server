import json
import logging
import socket
import threading

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

def encode(message):
    return (message + "\r\n").encode()

class AobaChatServer(socket.socket):
    client_names = {}
    client_sockets = []

    # Defines a function that will be called when CTRL+C is pressed.
    def signal_handler(self, sig, frame):
        for client in self.client_sockets:
            client.send(encode("DISCONNECT CHAT/1.0"))
        logging.info('Interrupt received, shutting down ...')

    def __init__(self):
        socket.socket.__init__(self)

        # Setup Logging
        logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.DEBUG, handlers=[logging.FileHandler("debug.log"), logging.StreamHandler()])

        #To silence- address occupied!!
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.bind(('0.0.0.0', 80))
        self.listen(5)

    def run(self):
        port = self.getsockname()[1]
        logging.info("Will wait for client connections at port " + str(port))
        logging.info("Waiting for incoming client connections...")
        try:
            self.accept_clients()
        except Exception as ex:
            logging.error(repr(ex))
        finally:
            logging.info("Shutting down server.")
            for client in self.client_sockets:
                client.close()
            self.close()

    def accept_clients(self):
        while True:
            (client_socket, _) = self.accept()
            
            # Get the registration from the client socket.
            registration = client_socket.recv(BUFFER_SIZE).decode()
            jsonResult = json.loads(registration) 

            # After decoding json, check to see if the action is connect, and then proceed with registration
            if("action" in jsonResult and "username" in jsonResult):
                if(jsonResult["action"] == "connect"):
                    self.client_sockets.append(client_socket) #Adding client to clients list
                    name = jsonResult["username"]
                    self.client_names[client_socket] = name

                    logging.info("Accepted connection from client address: " + client_socket.getsockname()[0])
                    logging.info("Connection to client established, waiting to receive messages from user '" + name + "'...")
                else:
                    client_socket.send(encode(json.dumps({ 'user': 'SERVER','message' : "400 Invalid registration"}, ensure_ascii=False)))
            else:
                client_socket.send(encode(json.dumps({ 'user': 'SERVER','message' : "400 Invalid registration"}, ensure_ascii=False)))

            #Receiving data from client
            newThread = threading.Thread(target = self.recieve, args=(client_socket,)) 
            newThread.start()

    def recieve(self, client):
        user = self.client_names[client]

        try:
            while 1:
                data = client.recv(BUFFER_SIZE)
                if data == '':
                    break

                #Message Received
                jsonResult = json.loads(data.decode()) 
                if("action" in jsonResult):
                    if(jsonResult["action"] == "disconnect"):
                        break
                    elif (jsonResult["action"] == "message"):
                        # If the message is empty, ignore it.
                        send_message = jsonResult["message"]
                        logging.info("<" + user + "> " + send_message)
                        if(send_message.startswith("/")):
                            client.send(encode(json.dumps({ 'user': "SERVER", 'message' : "You cannot send commands in global silly!"}, ensure_ascii=False)))
                        else:
                            self.broadcast(user, send_message)
        except ConnectionResetError as e:
            if user is not None:
                logging.info("Disconnecting " + user + " from the server.")
                self.client_sockets.remove(client)
                self.client_names.pop(user, 0)
                client.close()
            
    def broadcast(self, user, message):
        #Sending message to all clients
        for client in self.client_sockets:
            client.send(encode(json.dumps({ 'user': user, 'message' : message}, ensure_ascii=False)))


def main():
    server = AobaChatServer()
    server.run()

if __name__ == "__main__":
    main()
