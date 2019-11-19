import re
import shelve
from pprint import pprint
from time import sleep
import random

import telepot
import yagmail
from telepot.loop import MessageLoop
from boto.s3.connection import S3Connection

from cursos import cadastrar_cursos


TOKEN = S3Connection(os.environ['TOKEN'], os.environ['S3_SECRET'])
email = S3Connection(os.environ['EMAIL'], os.environ['S3_SECRET'])
password = S3Connection(os.environ['PASS'], os.environ['S3_SECRET']) 

email_bot = yagmail.SMTP(email, password)

bot = telepot.Bot(TOKEN)

db = shelve.open('database', writeback=True)

if __name__ == "__main__":

    if 'pessoas' not in db:
        db['pessoas'] = {}

    if 'cursos' not in db:
        db['cursos'] = {}

    cadastrar_cursos('database')


def logica(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    id_pessoa = str(chat_id)

    if id_pessoa not in db['pessoas']:
        db['pessoas'][id_pessoa] = {
            'proxima_acao': inicio,
            'nome': None,
            'matricula': None,
            'email': None,
            'cod_email': None,
            'email_verificado': False,
            'cadastrado': False,
            'cursos': []
        }

    pprint({
        'pessoa': db['pessoas'][id_pessoa],
        'msg': msg
    })

    if content_type == 'text':
        comando, *resto = msg['text'].split('@')
        if comando in comandos:
            comandos[comando](msg)

        else:
            db['pessoas'][id_pessoa]['proxima_acao'](msg)


def inicio(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    id_pessoa = str(chat_id)
    if db['pessoas'][id_pessoa]['cadastrado']:
        enviar_status(msg)
    else:
        bot.sendMessage(
            chat_id,
            f'Olá {msg["chat"]["first_name"]}, eu sou o bot 🤖 da Week.py\n'
            f'Para realizar seu cadastro clique: /cadastrar\n'
            f'Para cancelar a operação envie a qualquer momento: /cancelar\n'
        )


def enviar_status(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    id_pessoa = str(chat_id)
    pessoa = db['pessoas'][id_pessoa]

    if esta_cadastrado(chat_id):
        apelido = msg["chat"]["first_name"]
        cursos = pessoa['cursos']
        nome_cursos = [
            db['cursos'][id_curso]['nome']
            for id_curso in cursos
        ]
        bot.sendMessage(
            chat_id,
            (
                f'{apelido}, você está cadastrado na Week.py.\n'
                f'Você está inscrito em: {", ".join(nome_cursos)}\n'
                f'Para ver os cursos envie /cursos'
            )
        )
    else:
        enviar_msg_não_cadastrado(chat_id)


def cancelar(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    id_pessoa = str(chat_id)
    db['pessoas'][id_pessoa]['proxima_acao'] = inicio
    bot.sendMessage(chat_id, 'Operação cancelada')
    inicio(msg)


def iniciar_cadastro(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)

    if esta_cadastrado(chat_id):
        enviar_status(msg)
        return

    bot.sendMessage(
        chat_id,
        (
            f'Que bom que você quer participar, pra realizar seu '
            f'cadastro eu vou precisar de alguns dados seus.'
        )
    )
    cadastrar(msg)


def cadastrar(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    id_pessoa = str(chat_id)

    if esta_cadastrado(chat_id):
        enviar_status(msg)
        return

    if db['pessoas'][id_pessoa]['nome'] is None:
        bot.sendMessage(
            chat_id,
            f'Por favor, envie seu nome completo.'
        )
        db['pessoas'][id_pessoa]['proxima_acao'] = cadastrar_nome
        db.sync()

    elif db['pessoas'][id_pessoa]['matricula'] is None:
        bot.sendMessage(
            chat_id,
            f'Por favor, envie sua matrícula.'
        )
        db['pessoas'][id_pessoa]['proxima_acao'] = cadastrar_matricula
        db.sync()

    elif db['pessoas'][id_pessoa]['email'] is None:
        bot.sendMessage(
            chat_id,
            f'Por favor, envie seu e-mail, ele será verificado.'
        )
        db['pessoas'][id_pessoa]['proxima_acao'] = cadastrar_email
        db.sync()

    elif db['pessoas'][id_pessoa]['email_verificado'] is False:
        email = db['pessoas'][id_pessoa]['email']
        nome = db['pessoas'][id_pessoa]['nome']
        cod_email = gerar_codigo()
        db['pessoas'][id_pessoa]['cod_email'] = cod_email
        db.sync()
        enviar_email_de_verificação(email, nome, cod_email)
        bot.sendMessage(
            chat_id,
            f'Beleza, seu email ainda não foi verificado então eu te '
            f'mandei um código em {email} e preciso que me diga qual foi.\n'
            f'Não esquece de verificar se o email caiu no spam ou na lixeira.'
        )
        bot.sendMessage(
            chat_id,
            f'Se você não receber o email nos proximos minutos, envie: /reenviar'
        )
        db['pessoas'][id_pessoa]['proxima_acao'] = verificar_codigo
        db.sync()
    else:
        db['pessoas'][id_pessoa]['cadastrado'] = True
        db.sync()
        enviar_status(msg)


def cadastrar_nome(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    id_pessoa = str(chat_id)
    db['pessoas'][id_pessoa]['nome'] = msg['text']
    db.sync()
    bot.sendMessage(
        chat_id,
        f'Tudo certo.'
    )
    cadastrar(msg)


def cadastrar_matricula(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    id_pessoa = str(chat_id)

    if msg['text'].isdigit():
        db['pessoas'][id_pessoa]['matricula'] = msg['text']
        db.sync()
        bot.sendMessage(
            chat_id,
            f'Tudo certo.'
        )

    else:
        bot.sendMessage(
            chat_id,
            f'Matrícula inválida, tente novamente ou /cancelar para cancelar'
        )

    cadastrar(msg)


def email_valido(email):
    regex = r'^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'

    if(re.search(regex, email)):
        return True
    else:
        return False


def gerar_codigo():
    caracteres = [
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l',
        'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'x', 'w',
        'y', 'z', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
    ]
    codigo = ''
    for i in range(4):
        codigo += random.choice(caracteres)
    return codigo


def verificar_codigo(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    id_pessoa = str(chat_id)
    if msg['text'] == db['pessoas'][id_pessoa]['cod_email']:
        db['pessoas'][id_pessoa]['email_verificado'] = True
        db.sync()
        bot.sendMessage(
            chat_id,
            f'E-mail verificado, maravilha.'
        )
        db['pessoas'][id_pessoa]['proxima_acao'] = enviar_status

    cadastrar(msg)


def enviar_email_de_verificação(email, nome, cod_email):
    subject = f'Seu código de verificação é: {cod_email}'
    body = (
        f'Olá, {nome}.\n\n'
        f'Seu cógigo de verificação é: {cod_email}.\n'
        f'Envie esse código de volta para o bot para validar seu email.\n\n'
        f'Att.: Equipe Week.py'
    )

    email_bot.send(email, subject, body)


def cadastrar_email(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    id_pessoa = str(chat_id)
    if email_valido(msg['text']):
        db['pessoas'][id_pessoa]['email'] = msg['text']
        db.sync()
        bot.sendMessage(
            chat_id,
            f'Show! Aguarde o email de verificação.'
        )

    else:
        bot.sendMessage(
            chat_id,
            f'E-mail inválido, tente novamente ou /cancelar para cancelar'
        )

    cadastrar(msg)


def reenviar_email(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    id_pessoa = str(chat_id)
    cod_email = gerar_codigo()
    db['pessoas'][id_pessoa]['cod_email'] = cod_email
    db.sync()
    nome = db['pessoas'][id_pessoa]['nome']
    email = db['pessoas'][id_pessoa]['email']
    enviar_email_de_verificação(email, nome, cod_email)
    bot.sendMessage(
        chat_id,
        f'Reenviei um novo código para {email}, o antigo já não é válido.\n'
        f'Agora preciso que me diga o novo código.'
    )


def listar_cursos(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)

    if not esta_cadastrado(chat_id):
        enviar_msg_não_cadastrado(chat_id)
        return

    bot.sendMessage(
        chat_id,
        f'📋Os cursos disponíveis são:\n'
    )
    for curso_id, curso_dict in db['cursos'].items():
        bot.sendMessage(
            chat_id,
            (
                f'{curso_dict["descrição"]}\n'
                f'Para se inscrever click em: /inscrever@{curso_id}'
            )

        )


def esta_cadastrado(chat_id):
    id_pessoa = str(chat_id)
    return db['pessoas'][id_pessoa]['cadastrado']


def enviar_msg_não_cadastrado(chat_id):
    bot.sendMessage(
        chat_id,
        (
            f'Você não está cadastrado 😬\n'
            f'Mas fica tranquilo que pra cadastrar é só clicar em /cadastrar 🤯'
        )
    )


def inscrever_curso(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    id_pessoa = str(chat_id)
    comando, *resto = msg['text'].split('@')
    id_curso = resto[0]

    if not esta_cadastrado(chat_id):
        enviar_msg_não_cadastrado(chat_id)
        return

    if id_curso in db['cursos']:

        qtd_vagas = db['cursos'][id_curso]['qtd_vagas']
        qtd_inscritos = len(db['cursos'][id_curso]['alunos_inscritos'])

        if qtd_vagas <= qtd_inscritos:
            bot.sendMessage(
                chat_id,
                f'Poxa, infelizmente esse curso não tem mais vagas 😥'
            )
            return

        if id_pessoa not in db['cursos'][id_curso]['alunos_inscritos']:

            nome_curso = db['cursos'][id_curso]['nome']
            db['cursos'][id_curso]['alunos_inscritos'].append(id_pessoa)
            db['pessoas'][id_pessoa]['cursos'].append(id_curso)
            db.sync()
            bot.sendMessage(
                chat_id,
                f'Incrição em {nome_curso} realizada.😀\n'
            )
        else:
            bot.sendMessage(
                chat_id,
                f'Você já está cadastrado nesse curso. 😶\n'
            )
    else:
        bot.sendMessage(
            chat_id,
            f'Curso inválido 😅\n'
        )


funcoes = {
    'inicio': inicio,

}

comandos = {
    '/cancelar': cancelar,
    '/cadastrar': iniciar_cadastro,
    '/reenviar': reenviar_email,
    '/cursos': listar_cursos,
    '/inscrever': inscrever_curso
}


if __name__ == "__main__":
    MessageLoop(bot, logica).run_as_thread()

    print('Iniciado')
    while 1:
        sleep(10)
