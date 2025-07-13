# app.py
# -*- coding: utf-8 -*-

import os
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for
from functools import wraps
import firebase_admin
from firebase_admin import credentials, auth, firestore
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import openpyxl
import unicodedata
from babel.numbers import format_currency

# --- Configuração do Firebase ---
# Nota: O arquivo 'firebase_config.json' deve estar no mesmo diretório.
# Ele contém as credenciais do seu projeto Firebase.
try:
    cred = credentials.Certificate('firebase_config.json')
    firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    print(f"Erro ao inicializar o Firebase: {e}")
    db = None

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- Funções Utilitárias ---

def normalize_string(s):
    """Normaliza uma string, removendo acentos e espaços extras."""
    if not isinstance(s, str):
        s = str(s)
    s = s.lower().strip()
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def parse_date_from_excel(value):
    """Analisa datas de diferentes formatos (string, número do Excel)."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, int):
        # Converte a data serial do Excel para datetime
        return datetime(1899, 12, 30) + timedelta(days=value)
    if isinstance(value, str):
        for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
    return None

def login_required(f):
    """Decorator para exigir autenticação em certas rotas."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Este é um exemplo simples. Em um app real, você integraria
        # um sistema de sessão de usuário completo.
        user_id = "default_user" # Simula um usuário logado
        kwargs['user_id'] = user_id
        return f(*args, **kwargs)
    return decorated_function

# --- Rotas da Aplicação ---

@app.route('/')
@login_required
def landing_page(user_id):
    """Renderiza a página inicial com os conjuntos de dados do usuário."""
    if not db:
        return "Erro: Banco de dados Firebase não conectado.", 500

    datasets_ref = db.collection('datasets')
    query = datasets_ref.where('userId', '==', user_id)
    datasets = [doc.to_dict() for doc in query.stream()]

    for dataset in datasets:
        if 'createdAt' in dataset and isinstance(dataset['createdAt'], datetime):
            dataset['createdAt'] = dataset['createdAt'].strftime('%d/%m/%Y')

    return render_template('index.html', datasets=datasets)

@app.route('/dashboard/<dataset_id>')
@login_required
def dashboard(user_id, dataset_id):
    """Renderiza o painel de controle para um conjunto de dados específico."""
    if not db:
        return "Erro: Banco de dados Firebase não conectado.", 500

    dataset_ref = db.collection('datasets').document(dataset_id)
    dataset = dataset_ref.get()

    if not dataset.exists or dataset.to_dict().get('userId') != user_id:
        return redirect(url_for('landing_page'))

    return render_template('dashboard.html', dataset=dataset.to_dict())

# --- API Endpoints ---

@app.route('/api/datasets', methods=['POST'])
@login_required
def create_dataset(user_id):
    """Cria um novo conjunto de dados a partir do zero."""
    if not db:
        return jsonify({"error": "Banco de dados não conectado"}), 500

    data = request.json
    name = data.get('name')
    if not name:
        return jsonify({"error": "O nome é obrigatório"}), 400

    new_dataset_data = {
        'name': name,
        'userId': user_id,
        'transactions': [],
        'createdAt': datetime.now()
    }
    _, new_doc_ref = db.collection('datasets').add(new_dataset_data)
    return jsonify({"id": new_doc_ref.id})

@app.route('/api/datasets/upload', methods=['POST'])
@login_required
def upload_dataset(user_id):
    """Cria um conjunto de dados a partir de um arquivo Excel."""
    if not db:
        return jsonify({"error": "Banco de dados não conectado"}), 500

    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    file = request.files['file']
    name = request.form.get('name')

    if not name or not file or not file.filename.endswith('.xlsx'):
        return jsonify({"error": "Dados inválidos"}), 400

    try:
        workbook = openpyxl.load_workbook(file)
        sheet = workbook.active
        rows = list(sheet.iter_rows(values_only=True))

        if len(rows) < 2:
            return jsonify({"error": "A planilha está vazia"}), 400

        headers = [normalize_string(h) for h in rows[0]]
        required_headers = ['data', 'descricao', 'categoria', 'valor']
        if not all(h in headers for h in required_headers):
            return jsonify({"error": f"Colunas necessárias ausentes: {', '.join(required_headers)}"}), 400

        transactions = []
        for i, row in enumerate(rows[1:]):
            row_data = dict(zip(rows[0], row))
            
            valor_raw = row_data.get('Valor')
            valor = float(str(valor_raw).replace('R$', '').replace('.', '').replace(',', '.').strip()) if valor_raw is not None else 0.0
            
            data_raw = row_data.get('Data')
            data = parse_date_from_excel(data_raw)

            if data is None: continue

            transactions.append({
                'id': f"{int(datetime.now().timestamp())}-{i}",
                'date': data.strftime('%Y-%m-%d'),
                'description': str(row_data.get('Descrição', 'Sem descrição')),
                'category': str(row_data.get('Categoria', 'Geral')),
                'amount': abs(valor),
                'type': 'income' if valor >= 0 else 'expense'
            })
        
        new_dataset_data = {
            'name': name,
            'userId': user_id,
            'transactions': transactions,
            'createdAt': datetime.now()
        }
        _, new_doc_ref = db.collection('datasets').add(new_dataset_data)
        return jsonify({"id": new_doc_ref.id})

    except Exception as e:
        return jsonify({"error": f"Erro ao processar o arquivo: {e}"}), 500

@app.route('/api/datasets/<dataset_id>/transactions', methods=['GET', 'POST'])
@login_required
def manage_transactions(user_id, dataset_id):
    """Gerencia as transações de um conjunto de dados."""
    if not db:
        return jsonify({"error": "Banco de dados não conectado"}), 500

    dataset_ref = db.collection('datasets').document(dataset_id)
    
    if request.method == 'GET':
        # Filtra transações pelo mês atual
        month_str = request.args.get('month', datetime.now().strftime('%Y-%m'))
        current_month_start = datetime.strptime(month_str, '%Y-%m')
        current_month_end = current_month_start + relativedelta(months=1)

        dataset = dataset_ref.get().to_dict()
        all_transactions = dataset.get('transactions', [])
        
        monthly_transactions = []
        for t in all_transactions:
            t_date = datetime.strptime(t['date'], '%Y-%m-%d')
            if current_month_start <= t_date < current_month_end:
                monthly_transactions.append(t)
        
        return jsonify(sorted(monthly_transactions, key=lambda x: x['date'], reverse=True))

    if request.method == 'POST':
        # Adiciona ou atualiza uma transação
        transaction_data = request.json
        dataset = dataset_ref.get().to_dict()
        transactions = dataset.get('transactions', [])

        if 'id' in transaction_data and transaction_data['id']: # Atualizar
            transactions = [t if t['id'] != transaction_data['id'] else transaction_data for t in transactions]
        else: # Adicionar
            transaction_data['id'] = str(int(datetime.now().timestamp()))
            transactions.append(transaction_data)
        
        dataset_ref.update({'transactions': transactions})
        return jsonify(transaction_data)

@app.route('/api/datasets/<dataset_id>/transactions/<transaction_id>', methods=['DELETE'])
@login_required
def delete_transaction(user_id, dataset_id, transaction_id):
    """Exclui uma transação."""
    if not db:
        return jsonify({"error": "Banco de dados não conectado"}), 500
        
    dataset_ref = db.collection('datasets').document(dataset_id)
    dataset = dataset_ref.get().to_dict()
    transactions = dataset.get('transactions', [])
    
    transactions = [t for t in transactions if t.get('id') != transaction_id]
    
    dataset_ref.update({'transactions': transactions})
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
