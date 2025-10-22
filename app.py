from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# Função para conectar ao banco SQLite
def get_db_connection():
    conn = sqlite3.connect('finances.db')
    conn.row_factory = sqlite3.Row
    return conn

# Criar tabela se não existir
def create_table():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            valor REAL NOT NULL,
            descricao TEXT,
            data TEXT NOT NULL,
            mes INTEGER,
            ano INTEGER
        )
    ''')
    conn.commit()
    conn.close()


create_table()

# Página inicial
@app.route('/')
def index():
    conn = get_db_connection()
    transacoes = conn.execute('SELECT * FROM transacoes ORDER BY data').fetchall()
    conn.close()
    saldo = 0
    for t in transacoes:
        valor = t['valor']
        if t['tipo'] == 'despesa':
            valor = -abs(valor)
        saldo += valor
    saldo = round(saldo, 2)
    return render_template('index.html', transacoes=transacoes, saldo=saldo)

from datetime import datetime

@app.route('/adicionar', methods=['POST'])
def adicionar():
    tipo = request.form['tipo']
    valor = float(request.form['valor'])
    descricao = request.form['descricao']
    data = request.form['data']

    # Extrair mês e ano automaticamente da data
    data_convertida = datetime.strptime(data, "%Y-%m-%d")
    mes = data_convertida.month
    ano = data_convertida.year

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO transacoes (tipo, valor, descricao, data, mes, ano) VALUES (?, ?, ?, ?, ?, ?)',
        (tipo, valor, descricao, data, mes, ano)
    )
    conn.commit()
    conn.close()
    return redirect('/')



# Excluir transação
@app.route('/excluir/<int:id>')
def excluir(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM transacoes WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect('/')

# Editar transação (mostrar formulário)
@app.route('/editar/<int:id>')
def editar(id):
    conn = get_db_connection()
    transacao = conn.execute('SELECT * FROM transacoes WHERE id = ?', (id,)).fetchone()
    conn.close()
    return render_template('editar.html', transacao=transacao)

# Atualizar transação (receber formulário)
@app.route('/atualizar/<int:id>', methods=['POST'])
def atualizar(id):
    tipo = request.form['tipo']
    valor = float(request.form['valor'])
    descricao = request.form['descricao']
    data = request.form['data']

    conn = get_db_connection()
    conn.execute('UPDATE transacoes SET tipo = ?, valor = ?, descricao = ?, data = ? WHERE id = ?',
                 (tipo, valor, descricao, data, id))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/relatorios', methods=['GET'])
def relatorios():
    mes = request.args.get('mes')
    ano = request.args.get('ano')

    transacoes = []
    ganhos = despesas = saldo = 0

    if mes and ano:
        conn = get_db_connection()
        transacoes = conn.execute(
            'SELECT * FROM transacoes WHERE mes = ? AND ano = ? ORDER BY data',
            (mes, ano)
        ).fetchall()
        conn.close()

        for t in transacoes:
            valor = t['valor']
            if t['tipo'] == 'ganho':
                ganhos += valor
            else:
                despesas += valor
        saldo = ganhos - despesas

    return render_template('relatorios.html', transacoes=transacoes, mes=mes, ano=ano,
                           ganhos=ganhos, despesas=despesas, saldo=saldo)

if __name__ == '__main__':
    app.run(debug=True)
