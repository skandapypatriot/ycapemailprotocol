import hashlib
import socket
import json
import threading
import base64
import time
import sqlite3
import os


class FileServer:
    """File server for YCAP protocol.
    
    Handles file storage and delivery, communicates with mail server for client verification.
    Uses SQLite for metadata and filesystem for file storage (hybrid approach).
    """
    def __init__(self, host, port, mail_server_addr):
        self.host = host
        self.port = port
        self.mail_server_conf_addr = mail_server_addr
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 10 ** 7)
        try:
            self.s.bind((host, port))
        except Exception as e:
            raise ConnectionError(f"Port blocked or firewall issue: {e}")
        
        self.running = True
        self.client_threads = []
        
        # Setup filesystem storage
        self.files_dir = "ycap_files"
        if not os.path.exists(self.files_dir):
            os.makedirs(self.files_dir)
        
        # Setup SQLite database for metadata
        self.db = sqlite3.connect("files.db", check_same_thread=False)
        self.c = self.db.cursor()
        self.c.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id TEXT PRIMARY KEY,
            filename TEXT,
            username TEXT,
            filesize INTEGER,
            timestamp REAL,
            filepath TEXT
        )
        """)
        self.db.commit()
        print(f"File server initialized on {host}:{port}")
        print(f"Files directory: {os.path.abspath(self.files_dir)}")
    
    def verify_client_with_mail_server(self, client_key):
        """Verify client key with mail server"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect(self.mail_server_conf_addr)
            s.send(os.popen("echo %YCAP_FILE_KEY%").read().encode())
            verify_packet = {
                "command": "VERIFY_CLIENT",
                "client_key": client_key,
                "timestamp": time.time()
            }
            s.send(json.dumps(verify_packet).encode())
            response = json.loads(s.recv(1024).decode())
            s.close()
            return response.get("verified", False), response.get("username")
        except Exception as e:
            print(f"Error verifying client with mail server: {e}")
            return False, None
    
    
    
    def save_file_to_disk(self, file_hash, filedata):
        """Save file data to disk"""
        filepath = os.path.join(self.files_dir, file_hash)
        try:
            f = open(filepath, 'w')
            f.write(filedata)
            f.flush()
            f.close()
            return filepath
        except Exception as e:
            print(f"Error saving file to disk: {e}")
            return None
    
    def load_file_from_disk(self, file_hash):
        """Load file data from disk"""
        filepath = os.path.join(self.files_dir, file_hash)
        try:
            with open(filepath, 'r') as f:
                filedata = f.read()
            return filedata
        except Exception as e:
            print(f"Error loading file from disk: {e}")
            return None
    
    def delete_file_from_disk(self, file_hash):
        """Delete file from disk"""
        filepath = os.path.join(self.files_dir, file_hash)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
        except Exception as e:
            print(f"Error deleting file from disk: {e}")
        return False
    
    def handle_client(self, connection, addr):
        """Handle individual client connections"""
        print(f"File server connection from {addr}")
        username = None
        
        try:
            # Receive auth data
            auth_packet = json.loads(connection.recv(1024).decode())
            client_key = auth_packet.get("client_key")
            if not client_key:
                response = {
                    "command": "AUTH",
                    "status": "FAILED",
                    "message": "No client key provided"
                }
                connection.send(json.dumps(response).encode())
                connection.close()
                return
            # Verify with mail server
            verified, username = self.verify_client_with_mail_server(client_key)
            if not verified:
                response = {
                    "command": "AUTH",
                    "status": "UNAUTHORIZED",
                    "message": "Client verification failed"
                }
                connection.send(json.dumps(response).encode())
                connection.close()
                return
            # Client authenticated
            response = {
                "command": "AUTH",
                "status": "AUTHORIZED",
                "username": username
            }
            connection.send(json.dumps(response).encode())
            print(f"Client {username} authenticated")
            # Handle file operations
            while self.running:
                data = connection.recv(4096)
                if not data:
                    break
                while not data.decode()[len(data)-1] == "}":
                    data += connection.recv(4096)
                packet = json.loads(data.decode())
                command = packet.get("command")
                
                if command == "UPLOAD":
                    
                    # Client uploading file
                    file_hash = packet.get("file_hash")
                    filename = packet.get("filename")
                    filedata = packet.get("file_data")
                    filesize =  packet.get("file_size")
                    try:
                        print(filedata)


                        # Save to disk
                        filepath = self.save_file_to_disk(file_hash, filedata)
                        if filepath:
                            # Save metadata to database
                            self.c.execute("""
                            INSERT OR REPLACE INTO files 
                            (id, filename, username, filesize, timestamp, filepath) 
                            VALUES (?, ?, ?, ?, ?, ?)
                            """, (file_hash, filename, username, filesize, time.time(), filepath))
                            self.db.commit()
                            response = {
                                "command": "UPLOAD",
                                "status": "SUCCESS",
                                "file_hash": file_hash,
                                "filesize": filesize
                            }
                            print(f"File {filename} ({filesize} bytes) uploaded by {username} with hash {file_hash}")
                        else:
                            response = {
                                "command": "UPLOAD",
                                "status": "FAILED",
                                "error": "Could not save file to disk"
                            }
                        connection.send(json.dumps(response).encode())
                    except Exception as e:
                        response = {
                            "command": "UPLOAD",
                            "status": "FAILED",
                            "error": str(e)
                        }
                        print(f"Upload failed: {e}")
                        connection.send(json.dumps(response).encode())
                elif command == "DOWNLOAD":
                    # Client downloading file
                    file_hash = packet.get("file_hash")
                    file_record = self.c.execute(
                        "SELECT filename, username, filesize FROM files WHERE id=?", 
                        [file_hash]
                    ).fetchall()
                    print(file_record)
                    if file_record:
                        filename, uploader, filesize = file_record[0]
                        filedata = self.load_file_from_disk(file_hash)
                        if filedata:
                            response = {
                                "command": "DOWNLOAD",
                                "status": "SUCCESS",
                                "filename": filename,
                                "filedata": filedata,
                                "uploader": uploader,
                                "filesize": filesize
                            }
                            print(f"File {file_hash} ({filesize} bytes) downloaded by {username}")
                        else:
                            response = {
                                "command": "DOWNLOAD",
                                "status": "FAILED",
                                "error": "Could not load file from disk"
                            }
                    else:
                        response = {
                            "command": "DOWNLOAD",
                            "status": "NOT_FOUND",
                            "error": "File hash not found"
                        }
                        print(f"Download failed: {file_hash} not found")
                    connection.send(json.dumps(response).encode())

                elif command == "DELETE":
                    # Client deleting file
                    file_hash = packet.get("file_hash")
                    print(f"DELETE request for file_hash: {file_hash} by user: {username}")
                    file_record = self.c.execute(
                        "SELECT username FROM files WHERE id=?", 
                        [file_hash]
                    ).fetchall()
                    if file_record:
                        file_owner = file_record[0][0]
                        print(f"File owner: {file_owner}, Current user: {username}")
                        if file_owner == username:
                            # Delete from disk
                            if self.delete_file_from_disk(file_hash):
                                # Delete from database
                                self.c.execute("DELETE FROM files WHERE id=?", [file_hash])
                                self.db.commit()
                                response = {
                                    "command": "DELETE",
                                    "status": "SUCCESS",
                                    "file_hash": file_hash
                                }
                                print(f"File {file_hash} deleted by {username}")
                            else:
                                response = {
                                    "command": "DELETE",
                                    "status": "FAILED",
                                    "error": "Could not delete file from disk"
                                }
                        else:
                            response = {
                                "command": "DELETE",
                                "status": "UNAUTHORIZED",
                                "error": "Not file owner"
                            }
                            print(f"Delete unauthorized: {username} is not owner of {file_hash}")
                    else:
                        response = {
                            "command": "DELETE",
                            "status": "NOT_FOUND",
                            "error": "File hash not found"
                        }
                        print(f"DELETE failed: {file_hash} not found in database")
                    connection.send(json.dumps(response).encode())
                elif command == "LIST":
                    # List files uploaded by this user
                    user_files = self.c.execute(
                        "SELECT id, filename, filesize, timestamp FROM files WHERE username=?",
                        [username]
                    ).fetchall()
                    files_list = [
                        {
                            "hash": fh,
                            "filename": fn,
                            "filesize": fs,
                            "timestamp": ts
                        }
                        for fh, fn, fs, ts in user_files
                    ]
                    response = {
                        "command": "LIST",
                        "status": "SUCCESS",
                        "files": files_list
                    }
                    connection.send(json.dumps(response).encode())
                else:
                    response = {
                        "command": command,
                        "status": "UNKNOWN_COMMAND",
                        "error": f"Command {command} not recognized"
                    }
                    connection.send(json.dumps(response).encode())
        except json.JSONDecodeError:
            print("Invalid JSON received")
        except Exception as e:
            print(f"Error in handle_client: {e}")
        finally:
            try:
                connection.close()
            except:
                pass
            if username:
                print(f"Client {username} disconnected")

    def start(self):
        """Start file server"""
        print(f"File server listening on {self.host}:{self.port}")
        self.s.listen()
        try:
            while self.running:
                try:
                    connection, addr = self.s.accept()
                    t = threading.Thread(target=self.handle_client, args=(connection, addr), daemon=True)
                    t.start()
                    self.client_threads.append(t)
                except Exception as e:
                    print(f"Error accepting connection: {e}")
                    continue
        except KeyboardInterrupt:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown file server gracefully"""
        print("File server shutting down...")
        self.running = False
        try:
            self.s.close()
        except:
            pass
        for t in self.client_threads:
            if t.is_alive():
                t.join(timeout=0.2)
        try:
            self.db.commit()
            self.db.close()
        except:
            pass
        print("File server stopped.")

# Example usage
if __name__ == "__main__":
    file_server = FileServer("localhost", 5124, ("localhost", 8719))
    file_server.start()