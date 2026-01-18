import socket
import json      
from cryptography import fernet      
import os
import typing
import warnings                   
import secrets
import base64
import hashlib
import datetime

"""
YCAP Protocol Client Implementation

This module provides a client implementation for the YCAP email protocol.
Handles connection to YCAP servers and implements protocol commands for sending and receiving emails.
"""

def normalize_email(email):
    """Normalize email to include ^ycap.com domain if not present"""
    if not email:
        return email
    if not email.endswith("^ycap.com"):
        email = f"{email}^ycap.com"
    return email

def sign_up(user_id, password, host, port):
        user_id = normalize_email(user_id)
        address = (host, port)
        try:
            s = socket.create_connection(address, timeout=5)
            s.settimeout(5)
        except Exception as e:
            raise ConnectionError("YCAP Server not active or blocked by firewall: " + str(e))

        try:
            s.send(user_id.encode())
            defaut_YCAP_key = os.popen("echo %YCAP_KEY%").read().strip()
            if not defaut_YCAP_key:
                raise RuntimeError("YCAP_KEY environment variable not set")
            fernet_YCAP = fernet.Fernet(defaut_YCAP_key)
            super_secret_key = fernet_YCAP.decrypt(s.recv(1024))
            fernet_for_agkey = fernet.Fernet(super_secret_key)
            s.send(json.dumps({"credentials":(fernet_for_agkey.encrypt(password.encode()).decode())}).encode())
            response_packet = json.loads(s.recv(1024).decode())
            if response_packet == ["USER SECURELY VERIFIED"]:
                return True
            else:
                s.send(json.dumps(["SIGN UP"]).encode())
                s.send(json.dumps([fernet_for_agkey.encrypt(user_id.encode()).decode(), fernet_for_agkey.encrypt(password.encode()).decode()]).encode())
                return True
        finally:
            try:
                s.close()
            except:
                pass
            
class File:
    def __init__(self, file_handle:typing.IO,) -> None:
        self.id = secrets.token_hex(8)
        self.handle = file_handle
        self.file_name = os.path.split(self.handle.name)[1]


class Client:
    """YCAP protocol client implementation.
    
    Provides methods to connect to a YCAP server and send/receive emails using the YCAP protocol.
    Implements all standard YCAP commands including YCAP (handshake), YAP (send), LYAP (list), etc.
    """

    def __init__(self, host, port, mailaddress, password, file_server_addr=("localhost", 5124)):
        self.host = host
        self.port = port
        self.emailaddress = normalize_email(mailaddress) 
        self.file_server_addr = file_server_addr
        
        self.address = (host, port)
        try:
            self.s = socket.create_connection(self.address, timeout=5)
            self.s.settimeout(5)
        except Exception as e:
            raise ConnectionError("YCAP Server not active or blocked by firewall: " + str(e))
    
        self.s.send(self.emailaddress.encode())
        self.defaut_YCAP_key = os.popen("echo %YCAP_KEY%").read().strip()
        self.fernet_YCAP = fernet.Fernet(self.defaut_YCAP_key)
        self.super_secret_key = self.fernet_YCAP.decrypt(self.s.recv(1024))
        self.fernet_for_agkey = fernet.Fernet(self.super_secret_key)
        self.login(password)

        response_packet = self.s.recv(1024).decode()
        if response_packet == '["USER SECURELY VERIFIED"]':
            pass
        else:
            self.s.send(json.dumps(["QUIT"]).encode())
            raise NotImplementedError("USER NOT IN SERVER DB")
        self.key = str(self.s.recv(64).decode())

    def login(self, password):
        password = (self.fernet_for_agkey.encrypt(password.encode()).decode())
        self.s.send(json.dumps({"credentials":password}).encode())
    
    def ycap(self,):
        packet = {
                    "connection_key":self.key,
                    "command":"YCAP",
                    "arguments":[[self.host, self.port]]
             }
        packet = json.dumps(packet)
        self.s.send(packet.encode())
        answer_packet = json.loads(self.s.recv(1024).decode())
        if answer_packet.get("return")[0] == "YES":
            return True
        return False
    
    def nrizz(self,):
        packet = {
                    "connection_key":self.key,
                    "command":"NRIZZ",
                    "arguments":["GOODBYE"]
             }
        packet = json.dumps(packet)
        self.s.send(packet.encode())

        answer_packet = json.loads(self.s.recv(1024).decode())
        if answer_packet.get("return")[0] == "GOODBYE":
            self.s.close()
            return True
        
        return False

    def noop(self,):
        packet = {
                    "connection_key":self.key,
                    "command":"NOOP",
                    "arguments":["NOOP"]
             }
        packet = json.dumps(packet)
        self.s.send(packet.encode())
        
        answer_packet = json.loads(self.s.recv(1024).decode())
        if answer_packet.get("return")[0] == "NOOP":
            return True
        
        return False

    def send_mail(self, to_addr, mail_type, mail_data, file_path=None):
        """Send an email with optional file attachment.
        
        Args:
            to_addr (str): Recipient's email address
            mail_type (str): Type of mail (e.g., 'text', 'html')
            mail_data (str): Email content
            file_path (str, optional): Path to file to attach
            
        Returns:
            dict: Server response containing status and new mail ID
        """
        print(mail_type)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 10 ** 7)
        now = datetime.datetime.now()
        timestamp = f"{now:%d-%m-%y (%H:%M:%S)}"
        file_hash = None
        
        # If file is provided, upload it first
        if file_path:
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                
            else:
                filename = os.path.basename(file_path)
                with open(file_path, 'rb') as f:
                    filedata = f.read()

                filesize = len(filedata) / 1024
                file_hash = hashlib.sha256(filedata).hexdigest()[:16]

                # Upload file to file server
                if not self._upload_to_file_server(file_hash, filename, filedata):
                    print("Warning: File upload failed, sending email without attachment")
                    file_hash = None
        
        # Send email
        packet = {
            "connection_key": self.key,
            "command": "YAP",
            "arguments": [[self.emailaddress, to_addr, timestamp], mail_type, mail_data, ]
        }
        
        # Add file hash if file was uploaded
        if file_hash:
            packet["arguments"].append(file_hash)
        
        self.s.send(json.dumps(packet).encode())
        
        try:
            answer_packet = json.loads(self.s.recv(1024).decode())
            if answer_packet.get("return")[0] == "MAIL_SENT":
                return answer_packet
            else:
                warnings.warn(f"Mail not sent: {answer_packet.get('return')[1]}")
                return answer_packet
        except Exception as e:
            print(f"Error sending mail: {e}")
            return None
    
    def send_file(self, to_addr, file_path, message=""):
        """Send a file with optional message.
        
        Args:
            to_addr (str): Recipient's email address
            file_path (str): Path to file to send
            message (str, optional): Message to include with file
            
        Returns:
            dict: Server response with mail ID and file hash
        """
        return self.send_mail(to_addr, "file", message, file_path)
    
    def _upload_to_file_server(self, file_hash, filename, filedata):
        """Upload file to file server"""
        try:
            fs = socket.create_connection(self.file_server_addr, timeout=10)
            fs.settimeout(10)
            
            # Authenticate with file server
            auth_packet = {
                "client_key": self.key
            }
            fs.send(json.dumps(auth_packet).encode())
            auth_response = json.loads(fs.recv(1024).decode())
            
            if auth_response.get("status") != "AUTHORIZED":
                print(f"File server auth failed: {auth_response.get('message')}")
                fs.close()
                return False
            
            # Upload file
            upload_packet = {
                "command": "UPLOAD",
                "file_hash": file_hash,
                "file_data":filedata,
                "filename": filename,
            }
            fs.send(json.dumps(upload_packet).encode())
            upload_response = json.loads(fs.recv(1024).decode())
            
            fs.close()
            return upload_response.get("status") == "SUCCESS"
        except Exception as e:
            print(f"Error uploading to file server: {e}")
            return False
    
    def GMA(self, id):
        packet = {
            "connection_key": self.key,
            "command": "GMA",
            "arguments": [id]
        }
        packet = json.dumps(packet)
        self.s.send(packet.encode())
        try:
            answer_packet = json.loads(self.s.recv(105000).decode())
            return answer_packet.get("return")[0]
        except Exception as e:
            print("No response or error:", e)
            return None
    
    def download_file(self, file_hash, save_path=None):
        """Download a file from file server.
        
        Args:
            file_hash (str): Hash ID of file to retrieve
            save_path (str): Path to save file (optional)
            
        Returns:
            dict: File data or None if failed
        """
        try:
            fs = socket.create_connection(self.file_server_addr, timeout=10)
            fs.settimeout(10)
            
            # Authenticate
            auth_packet = {
                "client_key": self.key
            }
            fs.send(json.dumps(auth_packet).encode())
            auth_response = json.loads(fs.recv(1024).decode())
            
            if auth_response.get("status") != "AUTHORIZED":
                print("File server auth failed")
                fs.close()
                return None
            
            # Download file
            download_packet = {
                "command": "DOWNLOAD",
                "file_hash": file_hash
            }
            fs.send(json.dumps(download_packet).encode())
            download_response = json.loads(fs.recv(1024).decode())
            
            fs.close()
            
            if download_response.get("status") == "SUCCESS":
                filename = download_response.get("filename")
                filedata_b64 = download_response.get("filedata")
                filedata = base64.b64decode(filedata_b64)
                
                if save_path:
                    with open(save_path, 'wb') as f:
                        f.write(filedata)
                    print(f"File saved to {save_path}")
                
                return {
                    "filename": filename,
                    "uploader": download_response.get("uploader"),
                    "data": filedata
                }
            else:
                print(f"Download failed: {download_response.get('error')}")
                return None
        except Exception as e:
            print(f"Error downloading file: {e}")
            return None
    
    def NYAP(self, id):
        packet = {
            "connection_key": self.key,
            "command": "NYAP",
            "arguments": [id]
        }
        packet = json.dumps(packet)
        self.s.send(packet.encode())
        try:
            answer_packet = json.loads(self.s.recv(1024).decode())
            if answer_packet.get("return")[0] == "MAIL_NOT_DELETED":
                warnings.warn(f"Due to '{answer_packet.get("return")[1]}' mail is not deleted")
            return answer_packet
        except Exception as e:
            print("No response or error:", e)
            return None
    
    def get_mail(self, sent=False, no=10):
        """Request mail from server using the LYAP command.
        
        Retrieves emails matching the specified filters. All filter parameters are optional.
        
        Args:
            from_addr (str, optional): Filter by sender address
            to_addr (str, optional): Filter by recipient address
            mail_type (str, optional): Filter by mail type
            mail_data (str, optional): Filter by content
            since_id (int, optional): Only fetch messages with ID > since_id
            
        Returns:
            dict: Server response containing matching emails
            None: If request fails
        """

        packet = {
            "connection_key": self.key,
            "command": "LYAP",
            "arguments": [ sent ]
        }
        packet = json.dumps(packet)
        try:
            self.s.send(packet.encode())
        except Exception as e:
            print("Failed to send LYAP request:", e)
            return None
        try:
            answer_packet = json.loads(self.s.recv(8192).decode())
            mails = []
            if len(answer_packet.get("return")) > no:
                for i in range(no):
                    mails.append(self.GMA(answer_packet.get("return")[i]))
            else:
                for i in answer_packet.get("return"):
                    mails.append(self.GMA(i))   
            return mails
        except Exception as e:
            print("No response or error:", e)
            return None

