from flask import Flask, jsonify, request, send_from_directory
import json
import os

app = Flask(__name__, static_folder="web", static_url_path="")

JSON_FILE = "placas_detectadas.json"

def carregar_placas():
    """Carrega as placas do arquivo JSON, se existir."""
    if os.path.exists(JSON_FILE):
        # Evita erro se o arquivo estiver vazio
        if os.path.getsize(JSON_FILE) > 0:
            with open(JSON_FILE, "r", encoding='utf-8') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return [] # Retorna lista vazia se o arquivo estiver corrompido
    return []

def salvar_placas(placas):
    """Salva a lista de placas no arquivo JSON."""
    with open(JSON_FILE, "w", encoding='utf-8') as f:
        json.dump(placas, f, indent=4, ensure_ascii=False)

placas_detectadas = carregar_placas()

@app.route("/")
def index():
    return send_from_directory("web", "index.html")

@app.route("/placas")
def get_placas():
    return jsonify(placas_detectadas)

@app.route("/nova-placa", methods=["POST"])
def nova_placa():
    dados = request.json
    # Validação básica dos dados recebidos
    if dados and "placa" in dados and "timestamp" in dados and "status" in dados:
        placas_detectadas.append(dados)
        salvar_placas(placas_detectadas)
        return jsonify({"status": "sucesso"}), 200
    return jsonify({"erro": "Dados inválidos"}), 400

if __name__ == "__main__":
    # Desativar o modo debug em um ambiente de produção/container
    app.run(host="0.0.0.0", port=5000)