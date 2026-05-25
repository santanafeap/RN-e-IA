from flask import Flask, render_template, jsonify
import json

app = Flask(__name__)


# ==========================
# PÁGINA PRINCIPAL
# ==========================
@app.route('/')
def index():
    return render_template('index.html')


# ==========================
# API JSON
# ==========================
@app.route('/api/diarios')
def diarios():

    with open('diarios_resumidos.json', 'r', encoding='utf-8') as arquivo:
        dados = json.load(arquivo)

    return jsonify(dados)


# ==========================
# START
# ==========================
if __name__ == '__main__':
    app.run(debug=True)