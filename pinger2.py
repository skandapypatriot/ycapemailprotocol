import socket 


s = socket.socket()
s.connect(("localhost", 9000),)
s.accept()
def check_load_integrity(packet):
    checksum = int(s.recv(1024))
    if checksum == load_no:
        return True
    else:
        return False
load = ""
load_no = 0
s.send(load.encode())
load_no = load.count("a")
packet = s.recv(1024)
li = check_load_integrity(packet)
while li:
    s.send(load.encode())
    packet = s.recv(1024)
    li = check_load_integrity(packet)
    load += "a"
    load_no += 1