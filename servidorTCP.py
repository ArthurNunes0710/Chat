import socket
import threading

# lista de clientes conectados
clientes = []

# função para enviar mensagem para todos
def broadcast(mensagem, cliente_origem):
    for cliente in clientes:
        if cliente != cliente_origem:
            try:
                cliente.send(mensagem)
            except:
                clientes.remove(cliente)

# função que lida com cada cliente (THREAD)
def lidar_cliente(conn, addr):
    print(f"Conectado com {addr}")
    clientes.append(conn)

    while True:
        try:
            mensagem = conn.recv(1024)
            if not mensagem:
                break
            print(f"{addr}: {mensagem.decode()}")
            broadcast(mensagem, conn)
        except:
            break

    print(f"Desconectado: {addr}")
    clientes.remove(conn)
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