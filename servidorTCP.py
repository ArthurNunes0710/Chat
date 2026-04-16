import socket
import threading

# lista de clientes conectados
clientes = {}

# função para enviar mensagem para todos
def broadcast(mensagem, cliente_origem):
    nome = clientes[cliente_origem]
    msg_format = f"{nome}: {mensagem.decode()}".encode()
    for cliente in clientes:
        if cliente != cliente_origem:
            try:
                cliente.send(msg_format)
            except:
                clientes.pop(cliente,None)

# função que lida com cada cliente (THREAD)
def lidar_cliente(conn, addr):
    nome = conn.recv(1024).decode()
    print(f"{nome} conectado com {addr}")
    clientes[conn] = nome

    while True:
        try:
            mensagem = conn.recv(1024)
            if not mensagem:
                break
            print(f"{addr} - {clientes[conn]}: {mensagem.decode()}")
            broadcast(mensagem, conn)
        except:
            break

    print(f"Desconectado: {addr}")
    clientes.pop(conn , None)
    conn.close()

# função principal do servidor
def iniciar_servidor():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.bind(("0.0.0.0", 5001))
    servidor.listen()

    print("Servidor rodando...")

    while True:
        conn, addr = servidor.accept()
        thread = threading.Thread(target=lidar_cliente, args=(conn, addr))
        thread.start()

iniciar_servidor()
