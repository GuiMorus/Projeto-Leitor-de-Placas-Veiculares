#include <WiFi.h>
#include <LiquidCrystal_I2C.h>
#include <WebServer.h>
#include <ESP32Servo.h>

// Wi-Fi
const char* ssid = "NOME_DA_SUA_REDE_WIFI";
const char* password = "SENHA_DA_SUA_REDE_WIFI";

// LCD
LiquidCrystal_I2C lcd(0x27, 16, 2);

// Servo
Servo servo;
const int pinoServo = 18;  // Troque para outro pino se necessário
int anguloAtual = 0;       // Armazena a posição atual do servo

// Web server
WebServer server(80);

// Tempo
unsigned long ultimaMensagem = 0;
const unsigned long tempoLimite = 8 * 1000;

void mostrarMensagemPadrao() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("PACKBAG");
  lcd.setCursor(0, 1);
  lcd.print("Boas Vindas!");
}

void moverServoComLCD(int alvo, String mensagemPiscar) {
  int atual = servo.read();
  int passos = abs(alvo - atual);
  int direcao = (alvo > atual) ? 1 : -1;

  const int tempoDelay = 15;
  const int duracaoMovimento = passos * tempoDelay;  // tempo total do movimento
  const int intervaloPiscar = 400;
  int numPiscadas = duracaoMovimento / (2 * intervaloPiscar);  // piscadas visíveis

  // Começa movimento e piscar ao mesmo tempo
  unsigned long inicioPiscar = millis();
  unsigned long ultimaTroca = 0;
  bool visivel = false;

  for (int pos = atual, passo = 0; passo <= passos; pos += direcao, passo++) {
    servo.write(pos);

    // Piscar mensagem a cada intervaloPiscar
    if (millis() - ultimaTroca >= intervaloPiscar) {
      lcd.clear();
      if (!visivel) {
        lcd.setCursor(0, 0);
        lcd.print(mensagemPiscar);
      }
      visivel = !visivel;
      ultimaTroca = millis();
    }

    delay(tempoDelay);
  }

  lcd.clear();
  mostrarMensagemPadrao();
  ultimaMensagem = millis();  // reinicia o temporizador
}


void handleText() {
  if (server.hasArg("msg")) {
    String message = server.arg("msg");
    lcd.clear();
    lcd.setCursor(0, 0);

    if (message.length() > 16) {
      lcd.print(message.substring(0, 16));
      lcd.setCursor(0, 1);
      lcd.print(message.substring(16, 32));
    } else {
      lcd.print(message);
    }

    ultimaMensagem = millis();
    server.send(200, "text/plain", "Mensagem exibida no LCD!");
  } else {
    server.send(400, "text/plain", "Parâmetro 'msg' ausente.");
  }
}

void abrirPortao() {
  moverServoComLCD(90, "Abrindo Portao");
  server.send(200, "text/plain", "Portão aberto.");
}

void fecharPortao() {
  moverServoComLCD(0, "Fechando Portao");
  server.send(200, "text/plain", "Portão fechado.");
}

void setup() {
  Serial.begin(115200);
  Serial2.begin(115200, SERIAL_8N1, 16, 17); // Comunicação com ESP32-CAM
  Wire.begin(21, 22);  // I2C para LCD | SDA = 21, SCL = 22

  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("Conectando WiFi");

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nESP32 conectado!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  lcd.clear();
  lcd.print("IP:");
  lcd.setCursor(0, 1);
  lcd.print(WiFi.localIP());
  delay(3000);

  mostrarMensagemPadrao();
  ultimaMensagem = millis();

  // Servo
  servo.attach(pinoServo);
  servo.write(0);
  anguloAtual = 0;

  // Teste rápido do servo no setup
  delay(1000);
  servo.write(90);
  delay(1000);
  servo.write(0);
  delay(1000);

  // Rotas
  server.on("/lcd", HTTP_GET, handleText);
  server.on("/abrir", HTTP_GET, abrirPortao);
  server.on("/fechar", HTTP_GET, fecharPortao);
  server.begin();
  Serial.println("Servidor iniciado");
}

void loop() {
  server.handleClient();

  // Comunicação serial com ESP32-CAM
  if (Serial2.available()) {
    Serial.write(Serial2.read());
  }
  if (Serial.available()) {
    Serial2.write(Serial.read());
  }

  // Mensagem padrão se não houver atividade
  if (millis() - ultimaMensagem > tempoLimite) {
    mostrarMensagemPadrao();
    ultimaMensagem = millis();
  }
}
