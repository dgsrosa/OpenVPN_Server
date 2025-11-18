#!/bin/bash

# Configurações do usuário
USERNAME="MAIL_NO_IP"
PASSWORD= "INSERT_NO_IP PASSWORD"
HOSTNAME= "INSERT DNS TO UPDATE"
LOG="$HOME/noip_api.log"

# Detecta IP público atual
# Errado, tem que forçar atualizar IPV4
IPV4=$(curl -4 -s https://api.ipify.org)

# Atualiza via API da No-IP
curl -s "https://dynupdate.no-ip.com/nic/update?hostname=$HOSTNAME&myip=$IPV4" \
  -u "$USERNAME:$PASSWORD"

# Registra no log
echo "$(date '+%Y-%m-%d %H:%M:%S') - IP: $IPV4 - Resposta: $RESPONSE" >> $LOG


# Corrigido automaticamente a atualizaçao do IPV4. Checar, necessário também adicionar ao COntrab