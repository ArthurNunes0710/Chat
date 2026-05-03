import socket
import threading

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

    print(f"{nome} Conectado com {addr}")
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
    clientes.pop(conn, None)
    conn.close()

# função principal do servidor
def iniciar_servidor():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("0.0.0.0", 5001))
        s.listen()

        print("Servidor rodando...")

        while True:
            conn, addr = s.accept()
            thread = threading.Thread(target=lidar_cliente, args=(conn, addr))
            thread.start()

iniciar_servidor()