
# Importando o Flask-SQLAlchemy
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Carregando o SQLAlchemy em uma variável
db = SQLAlchemy()


# Tabela de Usuários
class Usuario(db.Model):

    # Campos da tabela
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    nickname = db.Column(db.String(60), unique=True, nullable=False)

    # Foto de perfil
    foto_perfil = db.Column(db.String(255), nullable=True)

    # Relacionamento com as imagens
    imagens = db.relationship('Imagem', backref='autor', lazy=True)

    # Relacionamento com as curtidas
    curtidas = db.relationship(
        'Curtida',
        backref='usuario',
        lazy=True,
        cascade='all, delete-orphan'
    )

    def __init__(self, email, senha, nickname):
        self.email = email
        self.nickname = nickname
        self.senha = senha


# Tabela de Imagens
class Imagem(db.Model):

    # Atributos
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), unique=True, nullable=False)
    legenda = db.Column(db.String(255))

    # Data e hora da publicação
    data_envio = db.Column(db.DateTime, default=datetime.now)

    # ID do usuário que publicou
    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey('usuario.id'),
        nullable=False
    )

    # Relacionamento com as curtidas
    curtidas = db.relationship(
        'Curtida',
        backref='imagem',
        lazy=True,
        cascade='all, delete-orphan'
    )

    # Função construtora
    def __init__(self, filename, legenda, usuario_id):
        self.filename = filename
        self.legenda = legenda
        self.usuario_id = usuario_id


# Tabela de Curtidas
class Curtida(db.Model):

    # Atributos
    id = db.Column(db.Integer, primary_key=True)

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey('usuario.id'),
        nullable=False
    )

    imagem_id = db.Column(
        db.Integer,
        db.ForeignKey('imagem.id'),
        nullable=False
    )

    # Impedindo curtidas duplicadas
    __table_args__ = (
        db.UniqueConstraint(
            'usuario_id',
            'imagem_id',
            name='curtida_unica'
        ),
    )
