import socket 

load = "a"
load_no = 1
s = socket.socket()
s.bind(("localhost", 9000))

def check_load_integrity(packet):
    checksum = int(s.recv(1024))
    if checksum == load_no:
        return True
    else:
        return False
s.send(load.encode())
packet = s.recv(1024)
li = check_load_integrity(packet)
while li:
    s.send(load.encode())
    packet = s.recv(1024)
    li = check_load_integrity(packet)
    load += "a"
    load_no += 1
print(load_no)
s.detach()