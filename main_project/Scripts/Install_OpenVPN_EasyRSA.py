#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Sequence, Union

Cmd = Union[str, Sequence[str]]

def run(cmd: Cmd, cwd: Optional[Union[str, Path]] = None) -> None:
    print(f"Executando: {cmd}")
    subprocess.run(
        cmd,
        shell=isinstance(cmd, str),
        cwd=str(cwd) if cwd else None,
        check=True,
    )

def require_root() -> None:
    # These scripts are intended for Linux. On Windows/macOS this check is skipped.
    if os.name != "posix":
        return
    if hasattr(os, "geteuid") and os.geteuid() != 0:
        print("Erro: execute este instalador com sudo (ex: sudo python3 Install_OpenVPN_EasyRSA.py).", file=sys.stderr)
        sys.exit(1)

def upsert_sysctl(path: str, key: str, value: str) -> None:
    """
    Update (or append) a single sysctl key without clobbering the whole file.
    """
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    new_lines = []
    found = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(f"{key}=") or stripped.startswith(f"{key} ="):
            new_lines.append(f"{key}={value}\n")
            found = True
        else:
            new_lines.append(line)

    if not found:
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines[-1] = new_lines[-1] + "\n"
        new_lines.append(f"\n{key}={value}\n")

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

def install_cron_line(line: str) -> None:
    """
    Idempotently add a line to root's crontab.
    """
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    current = result.stdout if result.returncode == 0 else ""
    if line.strip() in {l.strip() for l in current.splitlines()}:
        return
    new_crontab = (current.rstrip("\n") + "\n" + line.rstrip("\n") + "\n") if current.strip() else (line.rstrip("\n") + "\n")
    subprocess.run(["crontab", "-"], input=new_crontab, text=True, check=True)

# Diretório base do EasyRSA
require_root()
easyrsa_dir = Path.home() / "openvpn-ca"

# Perguntar IP/host e porta do servidor para validar .ovpn
remote_ip = input("Digite o IP ou host do servidor OpenVPN: ")
porta = input("Digite a porta do servidor OpenVPN(WAN): ")
if not remote_ip.strip():
    raise SystemExit("Erro: IP/host não pode ser vazio.")
if not porta.strip().isdigit():
    raise SystemExit("Erro: porta WAN deve ser um número.")


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
run("sudo apt install -y easy-rsa openvpn iptables")

# Preparar diretório EasyRSA
run(["mkdir", "-p", str(easyrsa_dir)])
run(["cp", "-r", "/usr/share/easy-rsa/.", str(easyrsa_dir)])

# Escrever variáveis no arquivo vars (antes de gerar certificados)
vars_path = easyrsa_dir / "vars"
existing = []
if vars_path.exists():
    existing = vars_path.read_text(encoding="utf-8", errors="ignore").splitlines(keepends=True)

keys = {
    "EASYRSA_REQ_COUNTRY": country,
    "EASYRSA_REQ_PROVINCE": province,
    "EASYRSA_REQ_CITY": city,
    "EASYRSA_REQ_ORG": org,
    "EASYRSA_REQ_EMAIL": email,
    "EASYRSA_REQ_OU": ou,
    "EASYRSA_REQ_CN": cn,
}

filtered = []
for line in existing:
    if any(line.strip().startswith(f'set_var {k} ') for k in keys):
        continue
    filtered.append(line)

filtered.append("\n")
for k, v in keys.items():
    filtered.append(f'set_var {k}    "{v}"\n')

vars_path.write_text("".join(filtered), encoding="utf-8")

# Se PKI já existir, perguntar antes de recriar
pki_dir = easyrsa_dir / "pki"
if pki_dir.exists():
    choice = input(f"PKI existente encontrada em {pki_dir}. Recriar do zero? (yes/no) ").strip().lower()
    if choice in ("yes", "y"):
        run(["rm", "-rf", str(pki_dir)])

# Inicializar PKI e construir CA
run("./easyrsa init-pki", cwd=easyrsa_dir)
run("./easyrsa build-ca nopass", cwd=easyrsa_dir)

# Gerar chave do servidor
run("./easyrsa gen-req server nopass", cwd=easyrsa_dir)
run("./easyrsa sign-req server server", cwd=easyrsa_dir)
run("./easyrsa gen-dh", cwd=easyrsa_dir)

# Gerar chave ta.key
run("mkdir -p keys", cwd=easyrsa_dir)
run("openvpn --genkey secret keys/ta.key", cwd=easyrsa_dir)

# Gerar TLS Crypt
run("openvpn --genkey --secret tls-crypt.key", cwd=easyrsa_dir)

# Gerar certificados de cliente
try:
    num_clients = int(input("Quantos certificados de cliente deseja gerar? "))
    if num_clients <= 0:
        raise ValueError()
    clientes_list = [f"client{i}" for i in range(1, num_clients + 1)]
    for client_name in clientes_list:
        run(f"./easyrsa gen-req {client_name} nopass", cwd=easyrsa_dir)
        run(f"./easyrsa sign-req client {client_name}", cwd=easyrsa_dir)
except ValueError:
    raise SystemExit("Entrada inválida. Por favor, insira um número inteiro maior que 0.")

#Adicionar FW IP and make it persitent
conffile = "/etc/sysctl.conf"
upsert_sysctl(conffile, "net.ipv4.ip_forward", "1")
run("sudo sysctl -p")

# Configurar ficheiro de servidor
run("cp /usr/share/doc/openvpn/examples/sample-config-files/server.conf /etc/openvpn/")
server_conf_path = "/etc/openvpn/server.conf"
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

# TLS Auth 
#tls-auth /etc/openvpn/ta.key 0
tls-crypt /etc/openvpn/tls-crypt.key

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

# Copiar certificados e chaves
run("sudo cp ~/openvpn-ca/pki/ca.crt /etc/openvpn/")
run("sudo cp ~/openvpn-ca/pki/issued/server.crt /etc/openvpn/")
run("sudo cp ~/openvpn-ca/pki/private/server.key /etc/openvpn/")
run("sudo cp ~/openvpn-ca/pki/dh.pem /etc/openvpn/")
run("sudo cp ~/openvpn-ca/keys/ta.key /etc/openvpn/")
run("sudo cp ~/openvpn-ca/tls-crypt.key /etc/openvpn/")

# Atualizar gerar_ovpn_completo.sh com os valores informados
script_dir = Path(__file__).resolve().parent
gerar_ovpn_path = script_dir / "gerar_ovpn_completo.sh"
if gerar_ovpn_path.exists():
    lines = gerar_ovpn_path.read_text(encoding="utf-8", errors="ignore").splitlines(keepends=True)
    with open(gerar_ovpn_path, "w", encoding="utf-8") as f:
        for line in lines:
            if line.startswith("OUTPUT_DIR="):
                f.write(f'OUTPUT_DIR="{script_dir}"\n')
            elif line.startswith("REMOTE_HOST="):
                f.write(f'REMOTE_HOST="{remote_ip}"\n')
            elif line.startswith("PORTA="):
                f.write(f'PORTA="{porta}"\n')
            elif "CLIENTES=" in line:
                clientes_str = " ".join([f'"{c}"' for c in clientes_list])
                f.write(f'CLIENTES=({clientes_str})\n')
            else:
                f.write(line)

print("\nLinha CLIENTES escrita no gerar_ovpn_completo.sh")

# Executar script para gerar arquivos .ovpn
run(["bash", str(gerar_ovpn_path)])

# Atualizar validar_ovpn.sh com os valores informados
validar_ovpn_path = script_dir / "validar_ovpn.sh"
if validar_ovpn_path.exists():
    lines = validar_ovpn_path.read_text(encoding="utf-8", errors="ignore").splitlines(keepends=True)
    with open(validar_ovpn_path, "w", encoding="utf-8") as f:
        for line in lines:
            if line.startswith("OVPN_DIR="):
                f.write(f'OVPN_DIR="{script_dir}"\n')
            elif line.startswith("REMOTE_IP="):
                f.write(f'REMOTE_IP="{remote_ip}"\n')
            elif line.startswith("PORTA="):
                f.write(f'PORTA="{porta}"\n')
            else:
                f.write(line)

# Adicionar wakeup_VPN_config.sh ao cron
cron_job = f"@reboot bash {script_dir}/wakeup_VPN_config.sh # openvpn_server wakeup"
install_cron_line(cron_job)

# Iniciar e habilitar OpenVPN
run("sudo systemctl start openvpn@server")
run("sudo systemctl enable openvpn@server")

# Executar validação dos arquivos .ovpn
run(["bash", str(validar_ovpn_path)])

# Executar validação dos arquivos .ovpn
run(["bash", str(script_dir / "wakeup_VPN_config.sh")])


def SuriInstall():
    print("Do you want to install Suricata IDS? (yes/no)")
    choice = input("> ").strip().lower()

    if choice in ["yes", "y"]:
        script_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "Suri_OpenVPN_Alert", "suri_openVPN.py"
        )
        script_path = os.path.normpath(script_path)

        if os.path.exists(script_path):
            print(f"Running Suricata installer: {script_path}")
            subprocess.run(["python3", script_path], check=True)
        else:
            print("Error: Suricata script not found at", script_path)
    else:
        print("Suricata installation skipped.")

if __name__ == "__main__":
    SuriInstall()


print("\n✅ DOne EnJoY.")

