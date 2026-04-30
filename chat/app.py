from flask import Flask , render_template , url_for , request , redirect , session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)
app.secret_key = "abc123"


class Usuario(db.Model):
    login = db.Column(db.String, primary_key=True)
    senha = db.Column(db.String(20), nullable = False)
    data_c = db.Column(db.DateTime, default= datetime.now)

    def __repr__(self):
        return '<Login %r>' % self.login


@app.route('/',methods=["GET","POST"])
def inicio():
    if request.method == 'POST':
        login = request.form['Login'].strip()
        senha = request.form['Senha'].strip()

        usuario = Usuario.query.get(login)

        if not usuario or usuario.senha != senha:
            return "Login ou senha inválidos"

       
        session['usuario'] = login

        return redirect('/chat') 

    return render_template("inicio.html")
    

@app.route('/chat')
def chat():
    return render_template("chat.html")



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
        db.session.delete(usuario_exc)
        db.session.commit()
        return redirect('/cadastro')
    except:
        return 'A operação não pode ser concluída'    

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
    app.run(debug=True)