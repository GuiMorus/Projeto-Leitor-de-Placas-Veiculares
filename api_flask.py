from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder="web", static_url_path="")

placas_detectadas = []

@app.route("/")
def index():
    return send_from_directory("web", "index.html")

@app.route("/placas")
def get_placas():
    return jsonify(placas_detectadas)

@app.route("/nova-placa", methods=["POST"])
def nova_placa():
    dados = request.json
    if dados:
        placas_detectadas.append(dados)
        return jsonify({"status": "sucesso"}), 200
    return jsonify({"erro": "Dados inválidos"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)