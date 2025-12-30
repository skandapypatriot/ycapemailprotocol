import socket
import threading
import json
import sqlite3
import os
import time
from cryptography import fernet

try:
    import msvcrt
except Exception:
    msvcrt = None
import secrets

"""
YCAP Email Protocol Server Implementation

This module implements the YCAP email server.
It handles client connections, manages the email database, and processes YCAP protocol commands.
"""

def invert_dictionary(dic):
    """Invert a dictionary mapping.
    
    Args:
        dic (dict): Dictionary to invert
        
    Returns:
        dict: Inverted mapping where values become keys and keys become values
    """
    return {v: k for k, v in dic.items()}
        
class Server:
    """YCAP Server implementation.
    
    Handles client connections, manages email database, and processes YCAP protocol commands.
    Uses SQLite for persistent storage and supports multiple simultaneous client connections.
    """
    
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 10 ** 7)
        self.db = sqlite3.connect("mails.db", check_same_thread=False)
        try:
            self.s.bind((host, port))
        except:
            ConnectionError("Port blocked or Please check firewall")
        self.connections = {}
        self.c = self.db.cursor()
        # Ensure mail table exists
        self.c.execute("""
        CREATE TABLE IF NOT EXISTS mail (
            id TEXT PRIMARY KEY,
            from_ TEXT,
            to_ TEXT,
            type_ TEXT,
            data TEXT
        )
        """)
        self.c.execute("""
     CREATE TABLE IF NOT EXISTS "users" (
	        "username"	TEXT,
	        "password"	TEXT NOT NULL,
	        PRIMARY KEY("username")
)
        """)
        self.db.commit()
        self.running = True
        self.client_threads = []
    
    def login(self, connection, email):
        credentials = json.loads(connection.recv(1024)).get("credentials")
        password = self.fernet_for_AGkey.decrypt(credentials).decode()
        try:
            password_real = self.c.execute("SELECT password FROM users WHERE username=?", [email]).fetchall()[0][0]
        except:
            return False
        if password == password_real:
            return True
        else:
            return False
        

    def signup(self, email_username:str, password):
        if not email_username.endswith("^ycap.com"):
            email_username += "^ycap.com"
        self.c.execute("INSERT INTO users (username, password) VALUES (?,?)", [email_username, password])
        self.db.commit()
        del email_username
        del password

    def start_listening(self):
        while self.running:
            try:
                self.s.listen()
                connection, addr = self.s.accept()
                print(f"Got connection from {addr}")
                
                email = connection.recv(1024).decode()
                super_secret_key = fernet.Fernet.generate_key()
                defaut_YCAP_key = os.popen("echo %YCAP_KEY%").read()
                fernet_YCAP = fernet.Fernet(defaut_YCAP_key)
                self.fernet_for_AGkey = fernet.Fernet(super_secret_key)
                connection.send(fernet_YCAP.encrypt(super_secret_key))

                if self.login(connection, email) == True:
                    connection.send(json.dumps(["USER SECURELY VERIFIED"]).encode())
                    salt = secrets.token_hex(8)  
                    self.connections.update({salt: [connection, email]})
                    connection.send(str(salt).encode())
                    # Start client handler thread for this connection
                    t = threading.Thread(target=self.handle_client, args=(salt,), daemon=True)
                    t.start()
                    self.client_threads.append(t)

                else:
                    connection.send(json.dumps(["404:-USER NOT FOUND"]).encode())
                    response = json.loads(connection.recv(1024).decode())
                    if response[0] == "SIGN UP":
                        credentials_e = json.loads(connection.recv(1024))
                        credentials = []
                        for i in credentials_e:
                            credentials.append(self.fernet_for_AGkey.decrypt(i).decode())
                        self.signup(credentials[0],  credentials[1])
                        salt = secrets.token_hex(8)
                        self.connections.update({salt: [connection, email]})
                        connection.send(str(salt).encode())
                        t = threading.Thread(target=self.handle_client, args=(salt,), daemon=True)
                        t.start()
                        self.client_threads.append(t)
                    else:
                        connection.close()
            except Exception as e:
                print(f"Error in start_listening: {e}")
                continue

    def handle_packet(self, packet, connection, key):
        command = packet.get("command")
        arg = packet.get("arguments")
        if command == "YCAP":
            if arg[0] == [self.host, self.port]:
                data = {
                        "connection_key":key,
                        "command":"YCAP",
                        "return":[
                            "OK"
                        ],}
                data = json.dumps(data)
                connection.send(data.encode())
        if command == "NRIZZ":
            data = {
                        "connection_key":key,
                        "command":"NRIZZ",
                        "return":[
                            "GOODBYE"
                        ],}
            data = json.dumps(data)
            connection.send(data.encode())
            connection.close()

        if command == "NOOP":
            if arg[0] == [self.host, self.port]:
                data = {
                        "connection_key":key,
                        "command":"NOOP",
                        "return":[
                            "NOOP"
                        ],}
                data = json.dumps(data)
                connection.send(data.encode())
                connection.close()
        if command == "LYAP":
            # Arguments: [FROM, TO ] (all optional)
            sent = arg[0]
            info_stealer = False
            # Build query
            if sent:
                to_addr = ""
                from_addr = self.connections.get(key)[1] 
            else:
                from_addr = ""
                to_addr = self.connections.get(key)[1]
            query = "SELECT id FROM mail WHERE "
            params = []
            if from_addr:
                query += " from_=?"
                if from_addr != self.connections.get(key)[1]:
                    info_stealer = True
                params.append(from_addr)
            if to_addr:
                query += " to_=?"
                if to_addr != self.connections.get(key)[1]:
                    info_stealer = True
                params.append(to_addr)
            if not info_stealer:
                result = self.c.execute(query, params).fetchall()

                # Format response
                emails = [
                    r[0]
                    for r in result
                ]
                response = {
                    "connection_key": str(key),
                    "command": "LYAP",
                    "return": emails
                }
                connection.send(json.dumps(response).encode())
                return 
            response = {
                    "connection_key": str(key),
                    "command": "LYAP",
                    "return": "NO stealing"
            }
            connection.send(json.dumps(response).encode())
        if command == "GMA": 
            mail_id = arg[0]
            query = "SELECT id, from_, to_, type_, data FROM mail WHERE id=?"
            result = self.c.execute(query, [mail_id]).fetchall()
            response = {
                    "connection_key": str(key),
                    "command": "GMA",
                    "return": result
            }
            connection.send(json.dumps(response).encode())
            return
        if command == "YAP":
            # Expecting arguments: [[from, to], type, data, file_hash (optional)]
            from_ = arg[0][0]
            to_ = arg[0][1]
            mail_type = arg[1]
            mail_data = arg[2]
            file_hash = arg[3] if len(arg) > 3 else None
            mail_id = secrets.token_hex(8)
            
            if self.c.execute("SELECT username FROM users WHERE username=?", [to_]).fetchall() != []:
                # Create email content with optional file attachment
                email_content = {
                    "text": mail_data,
                    "type": mail_type
                }
                if file_hash:
                    email_content["file_hash"] = file_hash
                
                # Insert mail into database
                self.c.execute(
                    "INSERT INTO mail (id, from_, to_, type_, data) VALUES (?, ?, ?, ?, ?)", 
                    (mail_id, from_, to_, mail_type, json.dumps(email_content))
                )
                self.db.commit()
                
                # Send response to client with the new mail ID
                response = {
                    "connection_key": str(key),
                    "command": "YAP",
                    "return": ["MAIL_SENT", mail_id]
                }
            else:
                response = {
                    "connection_key": str(key),
                    "command": "YAP",
                    "return": ["MAIL_NOT_SENT", "TO_USER_NOT_EXIST"]
                }

            connection.send(json.dumps(response).encode())
        if command == "NYAP":
            id = arg[0]
            if not self.c.execute('SELECT * FROM mail WHERE id = ?', [id]).fetchall() == []:
                self.c.execute("DELETE FROM mail WHERE id = ?", [id])
                self.db.commit()
                response = {
                    "connection_key": str(key),
                    "command": "NYAP",
                    "return": ["MAIL_DELETED", id]
                }
                connection.send(json.dumps(response).encode())
            else:
                response = {
                "connection_key": str(key),
                "command": "NYAP",
                "return": ["MAIL_NOT_DELETED", "MAIL_OR_MAIL_ID_DOESNT_EXIST"]
                }
                connection.send(json.dumps(response).encode())
        if command == "TISAHUR": # Actually its ti ti ti ti sahur
            pass
            
        

    def handle_client(self, key):
        # Handle client connection for specific key
        if key not in self.connections:
            return
        connection = self.connections[key][0]
        while self.running and key in self.connections:
            try:
                data = connection.recv(4096)
                if not data:
                    break
                packet = data.decode()
            except Exception:
                break
            if not packet == "":
                try:
                    packet = json.loads(packet)
                except Exception:
                    continue
                try:
                    key_check = packet.get("connection_key")
                except Exception:
                    key_check = None
                if key_check is None or self.connections.get(key_check) is None:
                    print("Invalid key found! Removing Connection")
                    # try to remove mapping for this connection
                    try:
                        to_remove = None
                        for k, v in list(self.connections.items()):
                            if v[0] == connection:
                                to_remove = k
                                break
                        if to_remove is not None:
                            self.connections.pop(to_remove)
                    except Exception:
                        pass
                    try:
                        connection.close()
                    except Exception:
                        pass
                    break
                self.handle_packet(packet, connection, key_check)
        
        # Clean up when client disconnects
        try:
            if key in self.connections:
                self.connections.pop(key)
        except Exception:
            pass
        try:
            connection.close()
        except Exception:
            pass

    def ycap_run(self):
        connect_thread = threading.Thread(target=self.start_listening, daemon=True)
        connect_thread.start()
        # start Ctrl+B listener (Windows)
        if msvcrt is not None:
            threading.Thread(target=self._ctrl_b_listener, daemon=True).start()
        try:
            while self.running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("KeyboardInterrupt received. Shutting down.")
            self.shutdown()

    def _ctrl_b_listener(self):
        # Listen for Ctrl+B (ASCII 2) on Windows console to shut down
        print("Ctrl+B listener active (press Ctrl+B to shut down server)")
        while self.running:
            try:
                if msvcrt.kbhit():
                    ch = msvcrt.getch()
                    if ch == b"\x02":
                        print("Ctrl+B detected. Shutting down server...")
                        self.shutdown()
                        break
            except Exception:
                break
            time.sleep(0.1)

    def connect_to_file_server(self, ):
        self.s_fs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s_fs.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 10 ** 7)
        self.s_fs.bind("localhost", 8457)
        self.super_secret_file_key = os.popen("echo %YCAP_FILE_KEY%").read()
        got = False
        while not got:
            conn = self.s.accept()
            conn = conn[0]
            if conn.recv(1024).decode() == "":
                pass


    def shutdown(self):
        print("Shutting down server gracefully...")
        self.running = False
        try:
            try:
                self.s.close()
            except Exception:
                pass
            for k, conn_data in list(self.connections.items()):
                try:
                    conn_data[0].close()
                except Exception:
                    pass
            for t in self.client_threads:
                if t.is_alive():
                    t.join(timeout=0.2)
            try:
                self.db.commit()
                self.db.close()
            except Exception:
                pass
        finally:
            print("Server stopped.")
            try:
                os._exit(0)
            except Exception:
                pass



ycap = Server("localhost", 1200)
ycap.ycap_run()