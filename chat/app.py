from flask import Flask , render_template , url_for , request , redirect , session
from flask_sqlalchemy import SQLAlchemy
import threading
import socket
import psycopg2
from datetime import datetime

app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://mensagens_data_user:rWCHTXjZTVi4mFeiJ386ULemRRfDXWIu@dpg-d84e2drbc2fs73c8jueg-a.oregon-postgres.render.com/mensagens_data'

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





def receberMensagens(socket_cliente):
    #so recebe do servidor q controla o banco
    while True:
        data = socket_cliente.recv(1024)

        if not data:
            break

        print(data.decode())

@app.route('/',methods=["GET","POST"])
def inicio():
    if request.method == 'POST':
        login = request.form['Login'].strip()
        senha = request.form['Senha'].strip()

        usuario = Usuario.query.get(login)

        if not usuario or usuario.senha != senha:
            return "Login ou senha inválidos"


        if login in clientes:
            clientes[login].close()
            del clientes[login]

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("127.0.0.1", 5001))
        s.send(login.encode())
        clientes[login] = s
                                                    

        t = threading.Thread(target=receberMensagens, args=(clientes[login],), daemon=True)
        t.start()
       
        session['usuario'] = login

        return redirect('/chat/1') 

    return render_template("inicio.html")

@app.route('/chat/<int:conversa_id>', methods=['GET', 'POST'])
def chat(conversa_id):
    if 'usuario' not in session:
        return redirect('/')
    
    
    login = session['usuario']
    participa = Participante.query.filter_by(usuario_login=login,conversa_id=conversa_id).first()   

    if not participa:
        return "Você não participa dessa conversa"

    conversa = Conversa.query.get_or_404(conversa_id)

    mensagens = Mensagem.query.filter_by(conversa_id=conversa_id).order_by(Mensagem.data_env).all()


    participacoes = Participante.query.filter_by(usuario_login=login).all()

    conversas = []

    for p in participacoes:
        conversa_temp = Conversa.query.get(p.conversa_id)
        conversas.append(conversa_temp)

    if login not in clientes:
        return redirect('/')

    socket_cliente = clientes[login]

    if request.method == 'POST':

        texto = request.form.get('mensagem')
        dest = request.form.get('procurar')

        if dest:
            
            if not Usuario.query.get(dest):
                return "O usuario não existe"
            nova_conversa = Conversa(nome=f'Conversa entre {dest} e {login}', tipo='privada')
            try:
                db.session.add(nova_conversa)
                db.session.commit()

                participante = Participante(usuario_login = login, conversa_id = nova_conversa.id)
                db.session.add(participante)
                db.session.commit()
            
                participante = Participante(usuario_login = dest, conversa_id = nova_conversa.id)
                db.session.add(participante)
                db.session.commit()
            except:
                return "Deu problema"
            
        if texto:
            msg_socket = f"{conversa_id}|{login}|{texto}"

            socket_cliente.send(msg_socket.encode())

        return redirect(f'/chat/{conversa_id}')

    return render_template("chat.html", mensagens=mensagens, conversa=conversa, conversas = conversas)

@app.route('/cadastro', methods = ['POST','GET'])
def index():
    if request.method == 'POST':
        login = request.form['Login'].strip()
        senha = request.form['Senha'].strip()

        if not login or not senha:
            return "Login e Senha não podem ser vazios"

        if Usuario.query.get(login):
            return "Usuário já existe"
        
        novo_usuario = Usuario(login=login, senha=senha)


        try:
            db.session.add(novo_usuario)
            db.session.commit()
            #talvez a gente mude mas a conversa com id 1 é o global ai quando o cara cadastra ele vira participante direto dela
            participante = Participante(usuario_login=login, conversa_id=1)

            db.session.add(participante)
            db.session.commit()

            return redirect('/')
        except: 
            return 'Deu problema'

    else:
        usuarios = Usuario.query.order_by(Usuario.data_c).all()
        return render_template("index.html", usuarios = usuarios)
    
@app.route('/excluir/<login>')

def excluir(login):
    usuario_exc = Usuario.query.get_or_404(login)

    try:
        
        # acho q do jeito q ta pode ter participante fantasma no global mas n sei se precisamo ligar pra isso 
        
        db.session.delete(usuario_exc)
        db.session.commit()
        return redirect('/cadastro')
    except:
        return 'A operação não pode ser concluída'    

#mudo nada esse editar
@app.route('/editar/<login>' , methods = ["POST", "GET"])

def editar(login):

    i = Usuario.query.get_or_404(login)

    if request.method == 'POST':

        novo_login = request.form['Login'].strip()
        nova_senha = request.form['Senha'].strip()

        if not novo_login or not nova_senha:
            return "Login e Senha não podem ser vazios"

        usuario_existente = Usuario.query.get(novo_login)

        if usuario_existente and usuario_existente.login != login:
            return "Usuário já existe"

        
        i.login = novo_login
        i.senha = nova_senha

        try:
            
            db.session.commit()
            return redirect('/')
        except: 
            return 'Deu problema'

    else:
        return render_template('editar.html', i = i)

if __name__ == '__main__':
    with app.app_context():
            db.create_all()

    app.run(host='0.0.0.0', port=8080)
