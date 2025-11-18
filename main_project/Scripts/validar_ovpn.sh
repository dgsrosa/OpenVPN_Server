#!/bin/bash

OVPN_DIR="$(dirname "$0")"
TA_KEY="/etc/openvpn/ta.key"
REMOTE_IP="YOUR_SERVER"
PORTA="YOUR_PORT"
PROTO="udp"

echo "🔍 Validando arquivos .ovpn em $OVPN_DIR..."

for FILE in "$OVPN_DIR"/*.ovpn; do
  echo -e "\n📁 Verificando: $(basename "$FILE")"

  # Verifica blocos essenciais
  for BLOCK in ca cert key tls-auth; do
    if grep -q "<$BLOCK>" "$FILE"; then
      echo "✔ Bloco <$BLOCK> encontrado"
    else
      echo "❌ Bloco <$BLOCK> ausente"
    fi
  done

  # Verifica key-direction
  if grep -q "key-direction 1" "$FILE"; then
    echo "✔ key-direction 1 presente"
  else
    echo "❌ key-direction 1 ausente"
  fi

  # Verifica proto e remote
  if grep -q "proto $PROTO" "$FILE" && grep -q "remote $REMOTE_IP $PORTA" "$FILE"; then
    echo "✔ Protocolo e IP/porta corretos"
  else
    echo "❌ Erro em proto ou remote"
  fi

  # Verifica se tls-auth bate com ta.key
  CLIENT_TA=$(awk '/<tls-auth>/,/<\/tls-auth>/' "$FILE" | grep -vE "<tls-auth>|</tls-auth>")
  SERVER_TA=$(grep -vE "^(#|$)" "$TA_KEY")

  if diff <(echo "$CLIENT_TA") <(echo "$SERVER_TA") >/dev/null; then
    echo "✔ tls-auth coincide com ta.key do servidor"
  else
    echo "❌ tls-auth diferente da ta.key do servidor"
  fi
done
