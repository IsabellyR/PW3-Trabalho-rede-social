
# Comentário no Python
# Importando o Flask para a aplicação
import pymysql.cursors
from flask import Flask, render_template

# Importando PYMYSQL
import pymysql

# Importando o SQLAlchemy e os Models
from models.database import db, Usuario, Imagem, Curtida

# Importando o SQLAlchemy inspect e text
from sqlalchemy import inspect, text

# Importando o Flask-SocketIO
from flask_socketio import SocketIO

# Definindo um nome para o banco
DB_NAME = 'spotface'

# Importando o Controller (rotas)
from controllers import routes

# Importando o arquivo de chat
from controllers import chat


# Carregando o Flask na variável "app"
app = Flask(__name__, template_folder='views')

# Passando o nome do banco para o Flask
app.config['DATABASE_NAME'] = DB_NAME

# Passando o endereço do banco para o Flask-SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://root:@localhost/{DB_NAME}'

# DEFININDO UMA CHAVE SECRETA
app.config['SECRET_KEY'] = 'meusegredo'

# DEFININDO O TEMPO DA SESSÃO
app.config['PERMANENT_SESSION_LIFETIME'] = 3600

# DEFININDO A PASTA DE UPLOADS
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# DEFININDO TAMANHO MÁXIMO DOS UPLOADS
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


# CONFIGURANDO O SOCKETIO
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)


# INICIALIZANDO O FLASK-SQLALCHEMY
db.init_app(app)

# ENVIANDO A VARIÁVEL APP PARA AS ROTAS
routes.init_app(app)

# INICIALIZANDO O SOCKETIO
chat.init_app(socketio)


# INICIANDO O SERVIDOR
if __name__ == '__main__':

    # CONECTANDO AO MYSQL PARA CRIAR O BANCO
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                f'CREATE DATABASE IF NOT EXISTS {DB_NAME}'
            )

            print("O banco de dados está criado!")

    except Exception as error:
        print(f"Ocorreu um erro ao criar o banco de dados! {error}")

    finally:
        connection.close()


    # CRIANDO E ATUALIZANDO AS TABELAS
    with app.app_context():

        # Criando as tabelas que ainda não existem
        db.create_all()

        # Criando o inspector
        inspector = inspect(db.engine)


        # VERIFICANDO AS COLUNAS DA TABELA USUARIO
        colunas_usuario = [
            coluna['name']
            for coluna in inspector.get_columns('usuario')
        ]

        # Verificando nickname
        if 'nickname' not in colunas_usuario:

            db.session.execute(text(
                "ALTER TABLE usuario ADD COLUMN nickname VARCHAR(60) UNIQUE"
            ))

            print("Coluna nickname criada com sucesso!")

        else:
            print("A coluna nickname já existe!")


        # Verificando foto_perfil
        if 'foto_perfil' not in colunas_usuario:

            db.session.execute(text(
                "ALTER TABLE usuario ADD COLUMN foto_perfil VARCHAR(255) NULL"
            ))

            print("Coluna foto_perfil criada com sucesso!")

        else:
            print("A coluna foto_perfil já existe!")


        # VERIFICANDO AS COLUNAS DA TABELA IMAGEM
        colunas_imagem = [
            coluna['name']
            for coluna in inspector.get_columns('imagem')
        ]

        # Verificando legenda
        if 'legenda' not in colunas_imagem:

            db.session.execute(text(
                "ALTER TABLE imagem ADD COLUMN legenda VARCHAR(255)"
            ))

            print("Coluna legenda criada com sucesso!")

        else:
            print("A coluna legenda já existe!")


        # Verificando data_envio
        if 'data_envio' not in colunas_imagem:

            db.session.execute(text(
                "ALTER TABLE imagem ADD COLUMN data_envio DATETIME DEFAULT CURRENT_TIMESTAMP"
            ))

            print("Coluna data_envio criada com sucesso!")

        else:
            print("A coluna data_envio já existe!")


        # Verificando usuario_id
        if 'usuario_id' not in colunas_imagem:

            db.session.execute(text(
                "ALTER TABLE imagem ADD COLUMN usuario_id INT NULL"
            ))

            print("Coluna usuario_id criada com sucesso!")

        else:
            print("A coluna usuario_id já existe!")


        # SALVANDO AS ALTERAÇÕES
        db.session.commit()

        print("Banco de dados atualizado com sucesso!")


    # INICIALIZANDO O SERVIDOR
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True
    )
