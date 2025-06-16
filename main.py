import json
import requests
from datetime import datetime
from collections import Counter
import cv2
from ultralytics import YOLO
import easyocr
import re
import os

# Configurações de IPs
IP_CAM = "192.168.x.x"      # IP da ESP32-CAM -> APARECE NO SERIAL MONITOR
IP_LCD = "192.168.x.x"      # IP do ESP32 com LCD -> APARECE NO SERIAL MONITOR
URL_LCD = f"http://{IP_LCD}/lcd"

# Inicializações
model = YOLO("license_plate_detector.pt")
reader = easyocr.Reader(['pt'], gpu=True)
cap = cv2.VideoCapture(f"http://{IP_CAM}:81/stream")

# Arquivos
path_detectadas = "placas_detectadas.json"
path_liberadas = "placas_liberadas.json"

# Carrega placas detectadas anteriormente
if os.path.exists(path_detectadas):
    with open(path_detectadas, "r") as f:
        placas_detectadas = json.load(f)
else:
    placas_detectadas = []

# Carrega placas liberadas
with open(path_liberadas, "r") as f:
    placas_liberadas = json.load(f)

# Utilitários

def validar_formato_placa(texto):
    padrao_novo = re.compile(r'^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$')
    padrao_antigo = re.compile(r'^[A-Z]{3}[0-9]{4}$')
    return padrao_novo.match(texto) or padrao_antigo.match(texto)

def detectar_texto_placa(imagem_placa):
    imagem_placa = cv2.resize(imagem_placa, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    resultados = reader.readtext(imagem_placa, allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    for (_, texto, confianca) in resultados:
        texto = texto.upper().replace(" ", "").strip()
        if confianca > 0.6 and 4 <= len(texto) <= 8 and validar_formato_placa(texto):
            return texto
    return "?"

def enviar_mensagem_lcd(mensagem):
    try:
        resposta = requests.get(URL_LCD, params={"msg": mensagem}, timeout=10)
        if resposta.status_code == 200:
            print(f"[✓] Mensagem enviada ao LCD: {mensagem}")
        else:
            print(f"[!] Erro ao enviar mensagem ao LCD: {resposta.status_code}")
    except Exception as e:
        print(f"[ERRO] Falha ao comunicar com ESP LCD: {e}")

# Buffer de leituras
buffer_leituras = []
BUFFER_SIZE = 10
LIMIAR_CONFIRMACAO = 6
placas_confirmadas = [p["placa"] for p in placas_detectadas]

# Loop principal
while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, conf=0.7, verbose=False)
    annotated = frame.copy()

    for box in results[0].boxes:
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
        crop = frame[y1:y2, x1:x2]

        leitura = detectar_texto_placa(crop)
        if leitura != "?":
            buffer_leituras.append(leitura)
            if len(buffer_leituras) > BUFFER_SIZE:
                buffer_leituras.pop(0)

            if len(buffer_leituras) == BUFFER_SIZE:
                contagem = Counter(buffer_leituras)
                mais_comum, qtd = contagem.most_common(1)[0]

                if qtd >= LIMIAR_CONFIRMACAO and mais_comum not in placas_confirmadas:
                    print(f"[+] Placa confirmada: {mais_comum}")
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Salva no JSON local
                    placas_detectadas.append({"data_hora": now, "placa": mais_comum})
                    placas_confirmadas.append(mais_comum)
                    with open(path_detectadas, "w") as f:
                        json.dump(placas_detectadas, f, indent=4, ensure_ascii=False)

                    # Envia mensagem ao ESP LCD
                    if mais_comum in placas_liberadas:
                        enviar_mensagem_lcd(f"{mais_comum} Liberado")
                    else:
                        enviar_mensagem_lcd(f"{mais_comum} Negado")

                    # Definir status
                    status = "Liberado" if mais_comum in placas_liberadas else "Negado"

                    try:
                        status = "Liberado" if mais_comum in placas_liberadas else "Negado"
                        dados = {
                            "placa": mais_comum,
                            "timestamp": now,
                            "status": status
                        }
                        resposta = requests.post("http://localhost:5000/nova-placa", json=dados, timeout=20)
                        if resposta.status_code == 200:
                            print("[✓] Placa enviada com sucesso para a página HTML.")
                        else:
                            print(f"[!] Falha ao enviar placa para a página: {resposta.status_code}")
                    except Exception as e:
                        print(f"[ERRO] Erro ao enviar dados para a API Flask: {e}")


                    # Limpa buffer após confirmação
                    buffer_leituras.clear()

        # Visualização
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(annotated, leitura, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)

    try:
        cv2.imshow("OCR Placas", annotated)
    except cv2.error:
        pass

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
