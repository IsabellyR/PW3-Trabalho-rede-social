
# Importando o Flask para a aplicação
from flask import render_template, request, redirect, url_for, flash, session

# Importando o MARKUPSAFE
from markupsafe import Markup

# Importando os Models
from models.database import db, Usuario, Imagem, Curtida

# Importando WERKZEUG
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Importando bibliotecas
import urllib.request
import json
import os
import uuid


# Criando a função principal para inicializar as rotas
def init_app(app):

    # FUNÇÃO DE MIDDLEWARE
    @app.before_request
    def check_auth():

        # Rotas que não precisam de autenticação
        rotasPermitidas = ['home', 'login', 'cadastro', 'static']

        if request.endpoint in rotasPermitidas:
            return

        # Verificando se o usuário está autenticado
        if 'usuario_id' not in session:
            return redirect(url_for('login'))

    # ROTA PRINCIPAL DO SITE
    @app.route('/')
    def home():
        return render_template('index.html')

    # ROTA DE CADASTRO DE USUÁRIO
    @app.route('/cadastro', methods=['GET', 'POST'])
    def cadastro():

        if request.method == 'POST':

            # Coletando os dados do formulário
            email = request.form['email']
            nickname = request.form['nickname']
            senha = request.form['senha']

            # Verificando se o email já existe
            usuario = Usuario.query.filter_by(email=email).first()

            if usuario:
                msgUsuario = Markup(
                    "Usuário já cadastrado. Faça o <a href='/login'>login</a>"
                )
                flash(msgUsuario, 'danger')
                return redirect(url_for('cadastro'))

            # Verificando se o nickname já existe
            nickname_existente = Usuario.query.filter_by(
                nickname=nickname
            ).first()

            if nickname_existente:
                flash("Esse nickname já está sendo utilizado!", 'danger')
                return redirect(url_for('cadastro'))

            # Gerando o hash da senha
            senha_criptografada = generate_password_hash(
                senha,
                method='scrypt'
            )

            # Criando o usuário
            novo_usuario = Usuario(
                email=email,
                senha=senha_criptografada,
                nickname=nickname
            )

            db.session.add(novo_usuario)
            db.session.commit()

            msgCad = Markup(
                "Cadastro realizado com sucesso! Você já pode fazer o <a href='/login'>login</a>."
            )
            flash(msgCad, 'success')

            return redirect(url_for('cadastro'))

        return render_template('cadastro.html')

    # ROTA DE LOGIN
    @app.route('/login', methods=['GET', 'POST'])
    def login():

        if request.method == 'POST':

            # Coletando os dados do usuário
            email = request.form['email']
            senha = request.form['senha']

            # Buscando o usuário no banco
            usuario = Usuario.query.filter_by(email=email).first()

            if usuario:

                # Verificando a senha
                if check_password_hash(usuario.senha, senha):

                    # Criando a sessão
                    session['usuario_id'] = usuario.id
                    session['usuario_email'] = usuario.email
                    session['usuario_nickname'] = usuario.nickname

                    flash(
                        "Você foi autenticado com sucesso! Bem-vindo!",
                        'success'
                    )

                    return redirect(url_for('home'))

                else:
                    flash(
                        'Falha no login. Verifique os dados e tente novamente!',
                        'danger'
                    )
                    return redirect(url_for('login'))

            else:
                flash('O usuário informado não existe!', 'danger')
                return redirect(url_for('login'))

        return render_template('login.html')

    # ROTA DE LOGOUT
    @app.route('/logout', methods=['GET', 'POST'])
    def logout():

        # Destruindo a sessão
        session.clear()

        return redirect(url_for('home'))

    # ROTA DE UPLOAD (FEED DE FOTOS)
    @app.route('/feed', methods=['GET', 'POST'])
    def feed():

        # Extensões permitidas
        FILE_TYPES = {'png', 'jpg', 'jpeg', 'gif'}

        # Função para validar o arquivo
        def arquivos_permitidos(filename):
            return (
                '.' in filename and
                filename.rsplit('.', 1)[1].lower() in FILE_TYPES
            )

        if request.method == 'POST':

            # Recebendo o arquivo e a legenda
            file = request.files.get('file')
            legenda = request.form.get('legenda', '')

            # Verificando se um arquivo foi selecionado
            if not file or file.filename == '':
                flash("Selecione uma imagem!", 'danger')
                return redirect(url_for('feed'))

            # Verificando a extensão
            if not arquivos_permitidos(file.filename):
                flash(
                    "Arquivo não permitido! Envie PNG, JPG, JPEG ou GIF.",
                    'danger'
                )
                return redirect(url_for('feed'))

            # Gerando um nome aleatório
            nome_seguro = secure_filename(file.filename)
            extensao = nome_seguro.rsplit('.', 1)[1].lower()
            filename = str(uuid.uuid4()) + '.' + extensao

            # Criando a pasta de uploads
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

            # Salvando o arquivo
            caminho = os.path.join(
                app.config['UPLOAD_FOLDER'],
                filename
            )
            file.save(caminho)

            # Pegando o usuário logado
            usuario_id = session['usuario_id']

            # Criando a publicação
            imagem = Imagem(
                filename=filename,
                legenda=legenda,
                usuario_id=usuario_id
            )

            db.session.add(imagem)
            db.session.commit()

            flash("Imagem recebida com sucesso!", 'success')
            return redirect(url_for('feed'))

        # Buscando as imagens mais recentes primeiro
        imagens = Imagem.query.order_by(
            Imagem.data_envio.desc()
        ).all()

        # Buscando as curtidas do usuário logado
        curtidas_usuario = {
            curtida.imagem_id
            for curtida in Curtida.query.filter_by(
                usuario_id=session['usuario_id']
            ).all()
        }

        return render_template(
            'feed.html',
            imagens=imagens,
            curtidas_usuario=curtidas_usuario
        )

    # ROTA PARA CURTIR E DESCURTIR PUBLICAÇÕES
    @app.route('/curtir/<int:imagem_id>', methods=['POST'])
    def curtir_post(imagem_id):

        # Buscando a publicação
        imagem = db.session.get(Imagem, imagem_id)

        if not imagem:
            flash("Publicação não encontrada!", 'danger')
            return redirect(url_for('feed'))

        usuario_id = session['usuario_id']

        # Verificando se já existe uma curtida
        curtida = Curtida.query.filter_by(
            usuario_id=usuario_id,
            imagem_id=imagem_id
        ).first()

        if curtida:

            # Removendo a curtida
            db.session.delete(curtida)
            flash("Curtida removida!", 'info')

        else:

            # Criando uma nova curtida
            nova_curtida = Curtida(
                usuario_id=usuario_id,
                imagem_id=imagem_id
            )

            db.session.add(nova_curtida)
            flash("Você curtiu a publicação!", 'success')

        db.session.commit()

        return redirect(url_for('feed'))

    # ROTA PARA EXCLUIR PUBLICAÇÕES
    @app.route('/excluir_post/<int:imagem_id>', methods=['POST'])
    def excluir_post(imagem_id):

        # Buscando a publicação
        imagem = db.session.get(Imagem, imagem_id)

        if not imagem:
            flash("Publicação não encontrada!", 'danger')
            return redirect(url_for('feed'))

        # Verificando se a publicação pertence ao usuário
        if imagem.usuario_id != session['usuario_id']:
            flash(
                "Você não pode excluir essa publicação!",
                'danger'
            )
            return redirect(url_for('feed'))

        # Localizando o arquivo
        caminho = os.path.join(
            app.config['UPLOAD_FOLDER'],
            imagem.filename
        )

        # Excluindo a publicação e suas curtidas
        db.session.delete(imagem)
        db.session.commit()

        # Excluindo a foto da pasta uploads
        if os.path.exists(caminho):
            os.remove(caminho)

        flash("Publicação excluída com sucesso!", 'success')

        return redirect(url_for('feed'))

    # ROTA DO PERFIL
    @app.route('/perfil', methods=['GET', 'POST'])
    def perfil():

        # Buscando o usuário logado
        usuario = db.session.get(
            Usuario,
            session['usuario_id']
        )

        if not usuario:
            session.clear()
            return redirect(url_for('login'))

        if request.method == 'POST':

            # Recebendo a foto
            file = request.files.get('foto_perfil')

            if not file or file.filename == '':
                flash("Selecione uma foto!", 'danger')
                return redirect(url_for('perfil'))

            # Extensões permitidas
            FILE_TYPES = {'png', 'jpg', 'jpeg', 'gif'}

            # Validando o arquivo
            if (
                '.' not in file.filename or
                file.filename.rsplit('.', 1)[1].lower() not in FILE_TYPES
            ):
                flash(
                    "Arquivo não permitido! Envie PNG, JPG, JPEG ou GIF.",
                    'danger'
                )
                return redirect(url_for('perfil'))

            # Gerando nome aleatório
            nome_seguro = secure_filename(file.filename)
            extensao = nome_seguro.rsplit('.', 1)[1].lower()
            filename = str(uuid.uuid4()) + '.' + extensao

            # Criando a pasta de uploads
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

            # Salvando a nova foto
            caminho = os.path.join(
                app.config['UPLOAD_FOLDER'],
                filename
            )
            file.save(caminho)

            # Guardando o nome da foto antiga
            foto_antiga = usuario.foto_perfil

            # Atualizando a foto no banco
            usuario.foto_perfil = filename
            db.session.commit()

            # Excluindo a foto antiga, se existir
            if foto_antiga:
                caminho_antigo = os.path.join(
                    app.config['UPLOAD_FOLDER'],
                    foto_antiga
                )

                if os.path.exists(caminho_antigo):
                    os.remove(caminho_antigo)

            flash("Foto de perfil atualizada com sucesso!", 'success')

            return redirect(url_for('perfil'))

        return render_template(
            'perfil.html',
            usuario=usuario
        )

    # ROTA DE CHAT COM JOGADORES
    @app.route('/chat')
    def chat():
        return render_template(
            'chat.html',
            nickname=session.get('usuario_nickname')
        )
