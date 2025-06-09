from flask import Flask, render_template, redirect, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'biblioteca123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///biblioteca.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)
    senha = db.Column(db.String(50), nullable=False)
    tipo = db.Column(db.String(10), nullable=False)
    nome_completo = db.Column(db.String(100))
    cpf = db.Column(db.String(20), unique=True)
    telefone = db.Column(db.String(20), unique=True)
    bloqueado = db.Column(db.Boolean, default=False)

class Livro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    identificacao = db.Column(db.String(20), unique=True, nullable=False)
    titulo = db.Column(db.String(100), nullable=False)
    autor = db.Column(db.String(100), nullable=False)
    disponivel = db.Column(db.Boolean, default=True)

class Emprestimo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    livro_id = db.Column(db.Integer, db.ForeignKey('livro.id'))
    data = db.Column(db.String(20))

def inicializar_banco():
    db.create_all()
    if not Usuario.query.first():
        db.session.add(Usuario(nome='Admin', senha='admin', tipo='admin'))
        db.session.add_all([
            Livro(identificacao='L001', titulo='Dom Casmurro', autor='Machado de Assis'),
            Livro(identificacao='L002', titulo='O Cortiço', autor='Aluísio Azevedo')
        ])
        db.session.commit()

@app.route('/')
def index():
    if 'usuario_id' in session:
        return redirect(url_for('painel'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    nome = request.form['nome']
    senha = request.form['senha']
    usuario = Usuario.query.filter_by(nome=nome, senha=senha).first()
    if usuario:
        if usuario.bloqueado:
            return render_template('login.html', erro='Usuário bloqueado.')
        session['usuario_id'] = usuario.id
        return redirect(url_for('painel'))
    return render_template('login.html', erro='Usuário ou senha inválidos.')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome_completo = request.form['nome_completo']
        cpf = request.form['cpf']
        telefone = request.form['telefone']
        nome = request.form['nome']
        senha = request.form['senha']

        if Usuario.query.filter_by(nome=nome).first():
            return render_template('cadastro.html', erro='Nome de usuário já cadastrado.')

        if Usuario.query.filter_by(cpf=cpf).first():
            return render_template('cadastro.html', erro='CPF já cadastrado.')

        if Usuario.query.filter_by(telefone=telefone).first():
            return render_template('cadastro.html', erro='Telefone já cadastrado.')

        novo_usuario = Usuario(
            nome=nome,
            senha=senha,
            nome_completo=nome_completo,
            cpf=cpf,
            telefone=telefone,
            tipo='usuario'
        )
        db.session.add(novo_usuario)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('cadastro.html')

@app.route('/logout')
def logout():
    session.pop('usuario_id', None)
    return redirect(url_for('index'))

@app.route('/painel')
def painel():
    if 'usuario_id' not in session:
        return redirect(url_for('index'))
    usuario = Usuario.query.get(session['usuario_id'])
    livros = Livro.query.all()
    emprestimos = Emprestimo.query.all()
    usuarios = Usuario.query.all()
    return render_template('painel.html', usuario=usuario, livros=livros, emprestimos=emprestimos, usuarios=usuarios)

@app.route('/retirar/<int:livro_id>')
def retirar(livro_id):
    if 'usuario_id' in session:
        livro = Livro.query.get(livro_id)
        if livro and livro.disponivel:
            livro.disponivel = False
            db.session.add(Emprestimo(usuario_id=session['usuario_id'], livro_id=livro_id, data=datetime.now().strftime('%d/%m/%Y')))
            db.session.commit()
    return redirect(url_for('painel'))

@app.route('/devolver/<int:livro_id>')
def devolver(livro_id):
    if 'usuario_id' in session:
        emprestimo = Emprestimo.query.filter_by(livro_id=livro_id, usuario_id=session['usuario_id']).first()
        if emprestimo:
            livro = Livro.query.get(livro_id)
            livro.disponivel = True
            db.session.delete(emprestimo)
            db.session.commit()
    return redirect(url_for('painel'))

@app.route('/adicionar', methods=['POST'])
def adicionar():
    if 'usuario_id' in session:
        usuario = Usuario.query.get(session['usuario_id'])
        if usuario.tipo == 'admin':
            identificacao = request.form['identificacao']
            titulo = request.form['titulo']
            autor = request.form['autor']
            db.session.add(Livro(identificacao=identificacao, titulo=titulo, autor=autor))
            db.session.commit()
    return redirect(url_for('painel'))

@app.route('/remover_livro/<int:livro_id>', methods=['POST'])
def remover_livro(livro_id):
    if 'usuario_id' in session:
        usuario = Usuario.query.get(session['usuario_id'])
        if usuario.tipo == 'admin':
            livro = Livro.query.get(livro_id)
            if livro:
                db.session.delete(livro)
                db.session.commit()
    return redirect(url_for('painel'))

@app.route('/usuarios')
def listar_usuarios():
    if 'usuario_id' in session:
        usuario = Usuario.query.get(session['usuario_id'])
        if usuario.tipo == 'admin':
            usuarios = Usuario.query.all()
            return render_template('usuarios.html', usuarios=usuarios)
    return redirect(url_for('painel'))

@app.route('/bloquear_usuario/<int:usuario_id>', methods=['POST'])
def bloquear_usuario(usuario_id):
    admin = Usuario.query.get(session['usuario_id'])
    if admin and admin.tipo == 'admin':
        usuario = Usuario.query.get(usuario_id)
        if usuario and usuario.tipo != 'admin':
            usuario.bloqueado = True
            db.session.commit()
    return redirect(url_for('listar_usuarios'))

@app.route('/remover_usuario/<int:usuario_id>', methods=['POST'])
def remover_usuario(usuario_id):
    admin = Usuario.query.get(session['usuario_id'])
    if admin and admin.tipo == 'admin':
        usuario = Usuario.query.get(usuario_id)
        if usuario and usuario.tipo != 'admin':
            db.session.delete(usuario)
            db.session.commit()
    return redirect(url_for('listar_usuarios'))

if __name__ == '__main__':
    with app.app_context():
        inicializar_banco()
    app.run(debug=True)
