import os
import subprocess

def run(cmd, cwd=None):
    print(f"Executando: {cmd}")
    subprocess.run(cmd, shell=True, cwd=cwd)

# Diretório base do EasyRSA
easyrsa_dir = os.path.expanduser("~/openvpn-ca")

# Perguntar IP/host e porta do servidor para validar .ovpn
remote_ip = input("Digite o IP ou host do servidor OpenVPN: ")
porta = input("Digite a porta do servidor OpenVPN(WAN): ")


# Solicitar variáveis ao usuário
print("\nPor favor, insira os dados para configurar os certificados:")
country = input("País CN (eg: España -> ES): ")
province = input("Estado/Província (eg: Pontevedra): ")
city = input("Cidade (eg: Santiago de Compostela): ")
org = input("Organização (eg: Minha Empresa): ")
email = input("Email (eg: email@exemplo.com): ")
ou = input("Unidade Organizacional (eg: TI): ")
cn = input("Nome Comum (eg: servidor1): ")

# Atualizar e instalar pacotes
run("sudo apt update")
run("sudo apt install easy-rsa openvpn -y")

# Evitando o Warning futuro para a substituiçao da PKI

run("sudo chmod 666 /root/openvpn-ca/pki")
run("sudo rm -rf /root/openvpn-ca/pki")
run("sudo chmod 644 /root/openvpn-ca/pki")

# Preparar diretório EasyRSA
run(f"mkdir -p {easyrsa_dir}")
run(f"cp -r /usr/share/easy-rsa/* {easyrsa_dir}")

# Inicializar PKI e construir CA
run("./easyrsa init-pki", cwd=easyrsa_dir)
run("./easyrsa build-ca nopass", cwd=easyrsa_dir)

# Escrever variáveis no arquivo vars
vars_path = os.path.join(easyrsa_dir, "vars")
with open(vars_path, "a") as f:
    f.write(f'\nset_var EASYRSA_REQ_COUNTRY    "{country}"\n')
    f.write(f'set_var EASYRSA_REQ_PROVINCE   "{province}"\n')
    f.write(f'set_var EASYRSA_REQ_CITY       "{city}"\n')
    f.write(f'set_var EASYRSA_REQ_ORG        "{org}"\n')
    f.write(f'set_var EASYRSA_REQ_EMAIL      "{email}"\n')
    f.write(f'set_var EASYRSA_REQ_OU         "{ou}"\n')
    f.write(f'set_var EASYRSA_REQ_CN         "{cn}"\n')


# Gerar chave do servidor
run("./easyrsa gen-req server nopass", cwd=easyrsa_dir)
run("./easyrsa sign-req server server", cwd=easyrsa_dir)
run("./easyrsa gen-dh", cwd=easyrsa_dir)

# Gerar chave ta.key
run("mkdir -p keys", cwd=easyrsa_dir)
run("openvpn --genkey secret keys/ta.key", cwd=easyrsa_dir)

# Gerar certificados de cliente
try:
    num_clients = int(input("Quantos certificados de cliente deseja gerar? "))
    clientes_list = [f"client{i}" for i in range(1, num_clients + 1)]
    for client_name in clientes_list:
        run(f"./easyrsa gen-req {client_name} nopass", cwd=easyrsa_dir)
        run(f"./easyrsa sign-req client {client_name}", cwd=easyrsa_dir)
except ValueError:
    print("Entrada inválida. Por favor, insira um número inteiro.")

#Adicionar FW IP and make it persitent
conffile = "/etc/sysctl.conf"
with open(conffile, "w") as f:
    f.write("net.ipv4.ip_forward=1\n")
run("sudo sysctl -p")

# Configurar ficheiro de servidor
run("cp /usr/share/doc/openvpn/examples/sample-config-files/server.conf /etc/openvpn/")
server_conf_path = "/etc/openvpn/server.conf"
run("sudo chmod 666 /etc/openvpn/server.conf")
with open(server_conf_path, "w") as f:
    f.write(f"""
port 1194
proto udp
dev tun

# Certificados gerados com Easy-RSA
ca /etc/openvpn/ca.crt
cert /etc/openvpn/server.crt
key /etc/openvpn/server.key
dh /etc/openvpn/dh.pem

# TLS Auth (opcional, mas recomendado)
tls-auth /etc/openvpn/ta.key 0
key-direction 0

# Segurança
cipher AES-256-CBC
auth SHA256
data-ciphers AES-256-GCM:AES-128-GCM:AES-256-CBC
tls-version-min 1.2

# Compressão (opcional)
allow-compression no

# Rede da VPN
server 10.8.0.0 255.255.255.0
ifconfig-pool-persist ipp.txt
tun-mtu 1400
mssfix 1360

# Manter conexão
keepalive 10 60
persist-key
persist-tun

# Log e verbosidade
status /var/log/openvpn-status.log
log /var/log/openvpn.log
verb 3

# Habilitar encaminhamento de IP (se quiser rotear internet)
push "redirect-gateway def1 bypass-dhcp"
push "dhcp-option DNS 8.8.8.8"
""")
run("sudo chmod 644 /etc/openvpn/server.conf")

# Copiar certificados e chaves
run("sudo cp ~/openvpn-ca/pki/ca.crt /etc/openvpn/")
run("sudo cp ~/openvpn-ca/pki/issued/server.crt /etc/openvpn/")
run("sudo cp ~/openvpn-ca/pki/private/server.key /etc/openvpn/")
run("sudo cp ~/openvpn-ca/pki/dh.pem /etc/openvpn/")
run("sudo cp ~/openvpn-ca/keys/ta.key /etc/openvpn/")

# Atualizar gerar_ovpn_completo.sh com os valores informados
gerar_ovpn_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gerar_ovpn_completo.sh")
if os.path.exists(gerar_ovpn_path):
    with open(gerar_ovpn_path, "r") as f:
        lines = f.readlines()
    with open(gerar_ovpn_path, "w") as f:
        for line in lines:
            if line.startswith("OUTPUT_DIR="):
                f.write(f'OUTPUT_DIR="{os.path.dirname(os.path.abspath(__file__))}"\n')
            elif line.startswith("REMOTE_HOST="):
                f.write(f'REMOTE_HOST="{remote_ip}"\n')
            elif line.startswith("PORTA="):
                f.write(f'PORTA="{porta}"\n')
            elif "CLIENTES=" in line:
                clientes_str = " ".join([f'"{c}"' for c in clientes_list])
                f.write(f'CLIENTES=({clientes_str})\n')
            else:
                f.write(line)

print("\nLinha CLIENTES escrita")
run("sudo cat gerar_ovpn_completo.sh | grep CLIENTES")

# Executar script para gerar arquivos .ovpn
run(f"bash {gerar_ovpn_path}")
run("wait")

# Atualizar validar_ovpn.sh com os valores informados
validar_ovpn_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "validar_ovpn.sh")
if os.path.exists(validar_ovpn_path):
    with open(validar_ovpn_path, "r") as f:
        lines = f.readlines()
    with open(validar_ovpn_path, "w") as f:
        for line in lines:
            if line.startswith("OVPN_DIR="):
                f.write(f'OVPN_DIR="{os.path.dirname(os.path.abspath(__file__))}"\n')
            elif line.startswith("REMOTE_IP="):
                f.write(f'REMOTE_IP="{remote_ip}"\n')
            elif line.startswith("PORTA="):
                f.write(f'PORTA="{porta}"\n')
            else:
                f.write(line)

# Adicionar wakeup_VPN_config.sh ao cron
cron_job = f"@reboot bash {os.path.dirname(os.path.abspath(__file__))}/wakeup_VPN_config.sh\n"
run(f'(sudo crontab -l 2>/dev/null; echo "{cron_job}") | crontab -')

# Iniciar e habilitar OpenVPN
run("sudo systemctl start openvpn@server")
run("sudo systemctl enable openvpn@server")

# Executar validação dos arquivos .ovpn
run(f"sudo bash {validar_ovpn_path}")

# Executar validação dos arquivos .ovpn
run(f"sudo bash ./wakeup_VPN_config.sh")

print("\n✅ DOne EnJoY.")

