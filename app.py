from flask import Flask, jsonify
import os

app = Flask(__name__)

# Esta é a página principal do seu site
@app.route('/')
def home():
    # Retorna uma mensagem simples
    return "Meu aplicativo de finanças está no ar!"

# Rota para verificar a chave da API (para teste)
@app.route('/check_api')
def check_api():
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        return jsonify(message="A chave da API do Gemini foi encontrada!", status="OK")
    else:
        return jsonify(message="ERRO: A chave da API do Gemini não foi encontrada!", status="Erro"), 404

if __name__ == '__main__':
    # Este comando permite que o Render inicie o aplicativo
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))