import socket
import threading

import Grupo

class Servidor:
    def __init__(self):
        self.HOST = '127.0.0.1'  # localhost
        self.PORT = 12345        # porta arbitrária

        self.Grupos = []

    def Chat(self, cliente, addr, destinatário):
        while True:
            try:
                mensagem = cliente.recv(1024)
                # if sair do grupo:
                    # self.EncontrarSala(cliente, addr)

                self.EnviarMensagem(mensagem, destinatário)
                print(f"{addr} - {cliente}: {mensagem}")
            except:
                break

    def Grupo(self, nome, cliente, addr):
        grupoSelecionado = None

        for grupo in self.Grupos:
            if grupo.Nome == nome:
                grupoSelecionado = grupo
                break

        while True:
            try:
                mensagem = cliente.recv(1024)
                # if sair do grupo:
                    # self.EncontrarSala(cliente, addr)

                for participante in grupoSelecionado.Participantes:
                    self.EnviarMensagem(mensagem, participante)

                print(f"{addr} - {cliente}: {mensagem}")
            except:
                break

    def EnviarMensagem(self, mensagem, destinatário):
        destinatário.send(mensagem)

    def EncontrarSala(self, cliente, addr):
        escolha = False

        while escolha == False:
            escolha = cliente.recv(1024)

            if escolha == "chat": # pegar endereço do outro participante
                self.Chat(self, cliente, addr, destinatário)

            elif escolha == "grupo": # pegar o nome do grupo
                self.Grupo(nome, cliente, addr)

            elif escolha == "criar grupo": # pegar o nome do grupo
                grupo = Grupo()
                grupo.Participantes.append(cliente)
                self.Grupos.append(grupo)
                self.Grupo(nome, cliente, addr)

    def Inicializar(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.HOST, self.PORT))

            while True:
                s.listen()
                print(f"Servidor TCP escutando em {self.HOST}: {self.PORT}...")
                cliente, endereço = s.accept()
                
                t = threading.Thread(target= self.EncontrarSala, args=(cliente, endereço))
                t.start()
