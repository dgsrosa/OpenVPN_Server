#!/bin/bash

set -euo pipefail

# Configurações do usuário
USERNAME="${NOIP_USERNAME:-MAIL_NO_IP}"
PASSWORD="${NOIP_PASSWORD:-}"
HOSTNAME="${NOIP_HOSTNAME:-}"
LOG="${NOIP_LOG:-$HOME/noip_api.log}"

if [[ -z "$PASSWORD" || -z "$HOSTNAME" ]]; then
  echo "❌ Erro: defina NOIP_PASSWORD e NOIP_HOSTNAME (e opcionalmente NOIP_USERNAME)."
  exit 1
fi

# Detecta IP público atual
IPV4=$(curl -4 -s https://api.ipify.org)
if [[ -z "$IPV4" ]]; then
  echo "❌ Erro: não foi possível obter IPv4 público"
  exit 1
fi

# Atualiza via API da No-IP
RESPONSE=$(curl -sS "https://dynupdate.no-ip.com/nic/update?hostname=$HOSTNAME&myip=$IPV4" \
  -u "$USERNAME:$PASSWORD" || true)

# Registra no log
echo "$(date '+%Y-%m-%d %H:%M:%S') - IP: $IPV4 - Resposta: $RESPONSE" >> $LOG


# Nota: para atualizar periodicamente, adicione este script ao crontab.