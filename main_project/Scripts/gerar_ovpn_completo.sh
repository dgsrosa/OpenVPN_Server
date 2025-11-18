#!/bin/bash

# Diretórios base
PKI_DIR="$HOME/openvpn-ca/pki"
TA_KEY="/etc/openvpn/ta.key"
OUTPUT_DIR=""
REMOTE_HOST=""
PORTA=""
PROTOCOLO="udp"

# Lista de clientes
CLIENTES=()

if [[ -z "$OUTPUT_DIR" ]]; then
  echo "❌ Erro: OUTPUT_DIR não definido"
  exit 1
fi

# Cria pasta de saída se não existir
mkdir -p "$OUTPUT_DIR"

# Verifica se ta.key existe e é legível
if [[ ! -r "$TA_KEY" ]]; then
  echo "❌ Erro: não foi possível ler $TA_KEY. Execute com sudo ou ajuste permissões."
  exit 1
fi

# Loop para cada cliente, apartir daqui é interativo
# o cliente o script irá realizar o loop com base nos
# valores inseridos em validar_ovpn.sh
for CLIENTE in "${CLIENTES[@]}"; do
  CRT="$PKI_DIR/issued/$CLIENTE.crt"
  KEY="$PKI_DIR/private/$CLIENTE.key"
  CA="$PKI_DIR/ca.crt"

  if [[ -f "$CRT" && -f "$KEY" && -f "$CA" ]]; then
    echo "📦 Gerando $CLIENTE.ovpn..."

    cat > "$OUTPUT_DIR/$CLIENTE.ovpn" <<EOF
client
dev tun
proto $PROTOCOLO
remote $REMOTE_HOST $PORTA
resolv-retry infinite
nobind
persist-key
persist-tun
cipher AES-256-CBC
auth SHA256
remote-cert-tls server
dhcp-option DNS 8.8.8.8
tun-mtu 1400
mssfix 1360
verb 3

<ca>
$(cat "$CA")
</ca>

<cert>
$(awk '/BEGIN/,/END/' "$CRT")
</cert>

<key>
$(cat "$KEY")
</key>

<tls-auth>
$(cat "$TA_KEY")
</tls-auth>
key-direction 1
EOF

    echo "✔ Arquivo $CLIENTE.ovpn criado com sucesso em $OUTPUT_DIR"
  else
    echo "⚠ Erro: arquivos ausentes para $CLIENTE"
    echo "  CRT: $CRT"
    echo "  KEY: $KEY"
    echo "  CA: $CA"
  fi
done
