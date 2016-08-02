import socket
import sys

LHOST = ''                 # Symbolic name meaning all available interfaces
LPORT = 6000              # Arbitrary non-privileged port

RHOST = sys.argv[1]
RPORT = int(sys.argv[2])

ss = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ss.bind((LHOST, LPORT))
ss.listen(1)

conn, addr = ss.accept()
print 'Connected by', addr

sc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sc.connect((RHOST, RPORT))
print 'Connected to', LHOST, LPORT

while 1:
    data = conn.recv(1024)
    if not data: break
    print 'Received:', data
    data = str(data)
    sc.sendall(data.upper())
    
conn.close()
sc.close()
