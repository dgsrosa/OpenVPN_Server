import os
import subprocess
import sys
from pathlib import Path

def run(cmd, cwd=None):
    print(f"Executando: {cmd}")
    subprocess.run(cmd, shell=True, cwd=cwd, check=True)

def require_root() -> None:
    if os.name != "posix":
        return
    if hasattr(os, "geteuid") and os.geteuid() != 0:
        print("Erro: execute este script com sudo (ex: sudo python3 suri_openVPN.py).", file=sys.stderr)
        sys.exit(1)

def install_cron_line(line: str) -> None:
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    current = result.stdout if result.returncode == 0 else ""
    if line.strip() in {l.strip() for l in current.splitlines()}:
        return
    new_crontab = (current.rstrip("\n") + "\n" + line.rstrip("\n") + "\n") if current.strip() else (line.rstrip("\n") + "\n")
    subprocess.run(["crontab", "-"], input=new_crontab, text=True, check=True)

# Atualizar e instalar pacotes
require_root()
run("sudo apt update")
run("sudo apt install -y geoip-database suricata jq")


# Copiando arquivos de configuração do Suricata

config_dir = Path(__file__).resolve().parent.parent / "Config"

subprocess.run(["cp", str(config_dir / "local.rules"), "/etc/suricata/rules/"], check=True)
subprocess.run(["cp", str(config_dir / "suricata.yaml"), "/etc/suricata/"], check=True)

# Adicionando o Servico do Suricata ao Systemctl

# Path to systemd service file
service_path = "/etc/systemd/system/suricata.service"

# Service file content
service_content = """[Unit]
Description=Suricata Intrusion Detection Service
After=network.target

[Service]
ExecStart=/usr/bin/suricata -c /etc/suricata/suricata.yaml --af-packet
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=5
User=root
Group=root

[Install]
WantedBy=multi-user.target
"""

# Write the service file
with open(service_path, "w") as f:
    f.write(service_content)

print(f"Service file written to {service_path}")

# Adding DNS_Fetch to Suricata
script_dir = os.path.dirname(os.path.abspath(__file__))
dns_fetch_path = os.path.join(script_dir, "dns_fetch.sh")

subprocess.run(["bash", dns_fetch_path], check=True)
print("dns_fetch.sh script executed.")

# Build cron job string: run every 3 hours
cron_job = f"0 */3 * * * bash {Path(__file__).resolve().parent}/dns_fetch.sh # openvpn_server suricata dns_fetch"
install_cron_line(cron_job)
print("Cron job for dns_fetch.sh ensured.")


subprocess.run(["systemctl", "daemon-reload"], check=True)

# Enable service to start at boot
subprocess.run(["systemctl", "enable", "suricata"], check=True)

# Start service immediately
subprocess.run(["systemctl", "start", "suricata"], check=True)

print("Suricata service created, enabled, and started.")



"""
Add GeoIP

	sudo apt install geoip-database


sudo nano /etc/suricata/suricata.yaml

	Then change:
		
		af-packet:
		-interface: eth0
    			cluster-id: 99
    			cluster-type: cluster_flow
    			defrag: yes

	AND Enable GeoIP
		
		app-layer:
 		 protocols:
   		 tls:
      		enabled: yes

		outputs:
 		 - eve-log:
     		 enabled: yes
     		 filetype: regular
     		 filename: /var/log/suricata/eve.json
     		 types:
       		 - alert:
           	 geoip: true


Create a Service

	sudo nano /etc/systemd/system/suricata.service
	
	[Unit]
	Description=Suricata Intrusion Detection Service
	After=network.target

	[Service]
	ExecStart=/usr/bin/suricata -c /etc/suricata/suricata.yaml -i eth0
	ExecReload=/bin/kill -HUP $MAINPID
	Restart=always
	RestartSec=5
	User=root
	Group=root

	[Install]
	WantedBy=multi-user.target

Reload to recongnize a new service

	sudo systemctl daemon-reload

Enable Service at Boot

sudo systemctl enable suricata

Start service right now

sudo systemctl start suricata



Open That:

	sudo nano /etc/suricata/rules/local.rules
	
	then Add (Only the first flow of a CLient)
		
		alert udp any any -> $HOME_NET 1194 (msg:"OpenVPN new connection attempt"; flow:to_server; threshold:type limit, track by_src, count 1, seconds 60; sid:1000013; rev:1;)




Line Of add Local RUles - > 2191

	Add   - /etc/suricata/rules/local.rules
	
	And comment the original file of rules in SUricata.. to heavy for Raspi
	
Validate FIle

	sudo suricata -c /etc/suricata/suricata.yaml -i eth0 -v



Then

	sudo systemctl restart suricata

To test it.

	tail -f /var/log/suricata/fast.log


Force Suricata to Reload RUles

sudo suricata-update
sudo systemctl restart suricata



Provlemas. No external IP SENDED, without LOCATION

10.164.0.13 -> 192.168.2.111 [OpenVPN new connection attempt] Country:null
10.164.0.13 -> 192.168.2.111 [OpenVPN new connection attempt] Country:null

"""