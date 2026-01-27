#!/bin/bash

set -euo pipefail
shopt -s nullglob

OVPN_DIR="$(dirname "$0")"
TA_KEY="/etc/openvpn/ta.key"
TLS_CRYPT_KEY="/etc/openvpn/tls-crypt.key"
REMOTE_IP="YOUR_SERVER"
PORTA="YOUR_PORT"
PROTO="udp"

echo "🔍 Validando arquivos .ovpn em $OVPN_DIR..."

files=("$OVPN_DIR"/*.ovpn)
if [[ ${#files[@]} -eq 0 ]]; then
  echo "⚠ Nenhum arquivo .ovpn encontrado em $OVPN_DIR"
  exit 0
fi

for FILE in "${files[@]}"; do
  echo -e "\n📁 Verificando: $(basename "$FILE")"

  # Verifica blocos essenciais (sempre necessários)
  for BLOCK in ca cert key; do
    if grep -q "<$BLOCK>" "$FILE"; then
      echo "✔ Bloco <$BLOCK> encontrado"
    else
      echo "❌ Bloco <$BLOCK> ausente"
    fi
  done

  has_tls_auth=false
  has_tls_crypt=false
  grep -q "<tls-auth>" "$FILE" && has_tls_auth=true
  grep -q "<tls-crypt>" "$FILE" && has_tls_crypt=true

  if $has_tls_auth; then
    echo "✔ Bloco <tls-auth> encontrado"
    if grep -q "key-direction 1" "$FILE"; then
      echo "✔ key-direction 1 presente (tls-auth)"
    else
      echo "❌ key-direction 1 ausente (tls-auth)"
    fi
  elif $has_tls_crypt; then
    echo "✔ Bloco <tls-crypt> encontrado"
    echo "ℹ tls-crypt em uso (key-direction não é necessário)"
  else
    echo "❌ Nenhum bloco <tls-auth> ou <tls-crypt> encontrado"
  fi

  # Verifica proto e remote
  if grep -q "proto $PROTO" "$FILE" && grep -q "remote $REMOTE_IP $PORTA" "$FILE"; then
    echo "✔ Protocolo e IP/porta corretos"
  else
    echo "❌ Erro em proto ou remote"
  fi

  # Verifica se o material TLS coincide com o do servidor (se o arquivo existir)
  if $has_tls_auth; then
    if [[ -r "$TA_KEY" ]]; then
      CLIENT_TA=$(awk '/<tls-auth>/,/<\/tls-auth>/' "$FILE" | grep -vE "<tls-auth>|</tls-auth>")
      SERVER_TA=$(grep -vE "^(#|$)" "$TA_KEY")
      if diff <(echo "$CLIENT_TA") <(echo "$SERVER_TA") >/dev/null; then
        echo "✔ tls-auth coincide com ta.key do servidor"
      else
        echo "❌ tls-auth diferente da ta.key do servidor"
      fi
    else
      echo "⚠ Não foi possível ler $TA_KEY para validar tls-auth"
    fi
  fi

  if $has_tls_crypt; then
    if [[ -r "$TLS_CRYPT_KEY" ]]; then
      CLIENT_TLS=$(awk '/<tls-crypt>/,/<\/tls-crypt>/' "$FILE" | grep -vE "<tls-crypt>|</tls-crypt>")
      SERVER_TLS=$(grep -vE "^(#|$)" "$TLS_CRYPT_KEY")
      if diff <(echo "$CLIENT_TLS") <(echo "$SERVER_TLS") >/dev/null; then
        echo "✔ tls-crypt coincide com tls-crypt.key do servidor"
      else
        echo "❌ tls-crypt diferente da tls-crypt.key do servidor"
      fi
    else
      echo "⚠ Não foi possível ler $TLS_CRYPT_KEY para validar tls-crypt"
    fi
  fi
done
