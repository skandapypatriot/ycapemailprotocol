import socket
import json      
from cryptography import fernet      
import os
import warnings                   

"""
YCAP Protocol Client Implementation

This module provides a client implementation for the YCAP email protocol.
Handles connection to YCAP servers and implements protocol commands for sending and receiving emails.
"""

def sign_up(user_id, password, host, port):
        s = socket.socket()
        address = (host, port)
        try:
            s.connect(address)
        except:
            ConnectionError("YCAP Server not active or blocked by firewall")
        
        s.send(user_id.encode())
        defaut_YCAP_key = os.popen("echo %YCAP_KEY%").read()
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
            
        

class Client:
    """YCAP protocol client implementation.
    
    Provides methods to connect to a YCAP server and send/receive emails using the YCAP protocol.
    Implements all standard YCAP commands including YCAP (handshake), YAP (send), LYAP (list), etc.
    """


       
    def __init__(self, host, port, mailaddress, password,):
        self.host = host
        self.port = port
        self.emailaddress = mailaddress

        
        self.s = socket.socket()
        self.address = (host, port)
        try:
            self.s.connect(self.address)
        except:
            ConnectionError("YCAP Server not active or blocked by firewall")
    

        self.s.send(self.emailaddress.encode())
        self.defaut_YCAP_key = os.popen("echo %YCAP_KEY%").read(1024)
        self.fernet_YCAP = fernet.Fernet(self.defaut_YCAP_key)
        self.super_secret_key = self.fernet_YCAP.decrypt(self.s.recv(1024))
        self.fernet_for_agkey = fernet.Fernet(self.super_secret_key)
        self.login(password)
        response_packet = json.loads(self.s.recv(1024).decode())    
        if response_packet == ["USER SECURELY VERIFIED"]:
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

    def send_mail(self,  to_addr, mail_type, mail_data):
        """Send an email using the YAP command.
        
        Args:
            to_addr (str): Recipient's email address
            mail_type (str): Type of mail (e.g., 'text', 'html')
            mail_data (str): Email content
            
        Returns:
            dict: Server response containing status and new mail ID
            None: If sending fails
        """
        packet = {
            "connection_key": self.key,
            "command": "YAP",
            "arguments": [[self.emailaddress, to_addr], mail_type, mail_data]
        }
        packet = json.dumps(packet)
        self.s.send(packet.encode())
        # Optionally, wait for a response (if server sends one)
        try:
            answer_packet = json.loads(self.s.recv(1024).decode())
            if answer_packet.get("return")[0] == "MAIL_NOT_SENT":
                warnings.warn(f"Due to '{answer_packet.get("return")[1]}' mail is not sent")
            return answer_packet
        except Exception as e:
            print("No response or error:", e) 
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

