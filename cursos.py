import shelve

python_basico_desc = (
    f'Curso básico de Python\n'
    f'Valor: R$20,00\n'
    f'Data: 26, 27 e 28 de novembro\n'
    f'• Caracteristicas da linguagem\n'
    f'• Operações matemáticas e booleanas\n'
    f'• Interação com o usuário\n'
    f'• Strings e Fstrings\n'
    f'• Listas, Tuplas, Conjuntos, Dicionários\n'
    f'• Funções\n'
    f'• If, elif, else\n'
    f'• For, While\n'
    f'• Try, Except\n'
    f'• Assert\n'
    f'• Classes e Objetos\n'
    f'• Criar executáveis com Pyinstaller\n'
)


def cadastrar_cursos(file):

    db = shelve.open(file, writeback=True)

    if 'cursos' not in db:
        db['cursos'] = {}

    if 'Python básico' not in db['cursos']:
        db['cursos']['python_basico'] = {
            'nome': 'Python Básico',
            'descrição': python_basico_desc,
            'qtd_vagas': 20,
            'alunos_inscritos': []
        }


cadastrar_cursos('database')
