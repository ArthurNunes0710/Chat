import socket
import threading

def receber(sock):
    while True:
        print(sock.recv(1024).decode())

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("127.0.0.1", 5001))

threading.Thread(target=receber, args=(sock,), daemon=True).start()

while True:
    msg = input()
    sock.send(msg.encode())