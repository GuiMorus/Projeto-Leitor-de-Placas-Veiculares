#!/bin/bash
# Shebang: Indica que o script deve ser executado com o interpretador Bash.

# Função para validar o formato de um endereço IP.
# Valida o formato e os valores dos octetos (0-255).
validar_ip_completo() {
    local ip=$1
    local stat=1

    if [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        OIFS=$IFS
        IFS='.'
        ip_array=($ip)
        IFS=$OIFS
        if [[ ${ip_array[0]} -le 255 && ${ip_array[1]} -le 255 && ${ip_array[2]} -le 255 && ${ip_array[3]} -le 255 ]]; then
            stat=0
        fi
    fi
    return $stat
}

# Loop infinito para solicitar e validar o IP da ESP32-CAM.
while true; do
    # Pede ao usuário para digitar o IP e armazena na variável IP_CAM.
    read -p "Digite o IP da ESP32-CAM (ex: 192.168.1.10): " IP_CAM
    # Chama a função de validação. Se o retorno for 0 (sucesso), o 'if' é verdadeiro.
    if validar_ip_completo "$IP_CAM"; then
        break # Sai do loop se o IP for válido.
    else
        # Informa o usuário sobre o erro e o loop continua.
        echo "Formato de IP inválido. Tente novamente."
    fi
done

# Loop infinito para solicitar e validar o IP do ESP32 com LCD/Servo.
while true; do
    # Pede ao usuário para digitar o IP e armazena na variável IP_ESP32.
    read -p "Digite o IP do ESP32 com LCD/Servo (ex: 192.168.1.11): " IP_ESP32
    # Chama a função de validação.
    if validar_ip_completo "$IP_ESP32"; then
        break # Sai do loop se o IP for válido.
    else
        # Informa o usuário sobre o erro e o loop continua.
        echo "Formato de IP inválido. Tente novamente."
    fi
done

# Mensagem de confirmação para o usuário.
echo "Configurando os IPs nos arquivos..."

# Usa o comando 'sed' (stream editor) para substituir os IPs nos arquivos de configuração.
# A opção '-i.bak' edita o arquivo no local e cria um backup com a extensão .bak.
# Isso garante compatibilidade entre macOS (que exige a extensão) e Linux.

# Substitui a linha 'IP_CAM = "..."' no arquivo main.py pelo IP fornecido pelo usuário.
sed -i.bak "s/IP_CAM = \".*\"/IP_CAM = \"$IP_CAM\"/" "main.py"
# Substitui a linha 'IP_LCD = "..."' no arquivo main.py pelo IP fornecido pelo usuário.
sed -i.bak "s/IP_LCD = \".*\"/IP_LCD = \"$IP_ESP32\"/" "main.py"
# Substitui a linha 'const ipESP32Servo = "..."' no arquivo web/index.html.
# Note que as barras '/' em 'http://' precisam ser escapadas com '\' para o sed.
sed -i.bak "s/const ipESP32Servo = \".*\"/const ipESP32Servo = \"http:\/\/$IP_ESP32\"/" "web/index.html"

echo "IPs configurados com sucesso!"

# Inicia os serviços definidos no arquivo docker-compose.yml.
# O comando 'up' cria e inicia os contêineres.
# A flag '--build' força a reconstrução das imagens Docker antes de iniciar os serviços.
echo "Iniciando os serviços com Docker Compose..."
docker compose up --build

# Limpa os arquivos de backup (.bak) criados pelo comando 'sed'.
# A flag '-f' (force) evita mensagens de erro caso os arquivos não existam.
echo "Limpando arquivos de backup..."
rm -f main.py.bak web/index.html.bak

echo "Script finalizado."