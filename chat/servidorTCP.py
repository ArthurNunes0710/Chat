import socket
import threading
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from datetime import datetime


#  app.config liga os dois no mesmo db
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)
app.secret_key = "abc123"

clientes = {}

class Usuario(db.Model):
    __tablename__ = 'usuario'
    login = db.Column(db.String, primary_key=True)
    senha = db.Column(db.String(20), nullable = False)
    data_c = db.Column(db.DateTime, default= datetime.now)

    def __repr__(self):
        return '<Login %r>' % self.login

class Conversa(db.Model):
    __tablename__ = 'conversa'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50))
    tipo = db.Column(db.String(20))

class Mensagem(db.Model):
    __tablename__ = 'mensagem'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    texto = db.Column(db.Text, nullable=False)
    proprietario = db.Column(db.String, db.ForeignKey('usuario.login'))
    conversa_id = db.Column(db.Integer, db.ForeignKey('conversa.id'))
    data_env = db.Column(db.DateTime, default=datetime.now)


class Participante(db.Model):
    __tablename__ = 'participante'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement = True)
    usuario_login = db.Column(db.String, db.ForeignKey('usuario.login'))
    conversa_id = db.Column(db.Integer, db.ForeignKey('conversa.id'))



# função para enviar mensagem para todos
def broadcast(mensagem):

    for cliente in clientes:
        try:
            cliente.send(mensagem)
        except:
            clientes.pop(cliente, None)

# função que lida com cada cliente (THREAD)
def lidar_cliente(conn, addr):
    nome = conn.recv(1024).decode()

    print(f"{nome} Conectado com {addr}")
    clientes[conn] = nome

    with app.app_context():
        while True:
            try:
                mensagem = conn.recv(1024)
                if not mensagem:
                    break
                mensagem_decod = mensagem.decode()

                conversa_id, login, texto = mensagem_decod.split('|', 2)

                nova_msg = Mensagem(texto=texto, proprietario=login, conversa_id=int(conversa_id))

                db.session.add(nova_msg)
                db.session.commit()
                
                print(f"{addr} - {clientes[conn]}: {mensagem.decode()}")
                
                broadcast(mensagem)
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