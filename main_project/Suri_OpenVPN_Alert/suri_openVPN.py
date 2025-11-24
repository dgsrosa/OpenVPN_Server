import os
import subprocess

def run(cmd, cwd=None):
    print(f"Executando: {cmd}")
    subprocess.run(cmd, shell=True, cwd=cwd)

# Atualizar e instalar pacotes
run("sudo apt update")
run("sudo apt install geoip-database -y suricata -y")

#Open That:

with open("/etc/suricata/rules/local.rules", "w") as f:
	f.write('alert udp any any -> $HOME_NET 1194 (msg:"OpenVPN new connection attempt"; flow:to_server; threshold:type limit, track by_src, count 1, seconds 60; sid:1000013; rev:1;)')
print("Local rules file created at /etc/suricata/rules/local.rules")
		
		

# Atualizar Suricata.yaml.
with open("/etc/suricata/suricata.yaml", "r") as infile, open("/etc/suricata/suricata_modified.yaml", "w") as outfile:
    for line in infile:
        # Write the original line
        outfile.write(line)
        # If we find the alert block, insert geoip: true with correct indentation
        if line.strip() == "- alert:":
            # Add 2 spaces indentation (YAML requires spaces, not tabs)
            outfile.write("      geoip: true\n")
		if line.strip() == "- Rules:":
			# Comment original rules line
			outfile.write("#      - /etc/suricata/rules/\n")
			# Add local rules line
			outfile.write("      - /etc/suricata/rules/local.rules\n")
		

# Adicionando o Servico do Suricata ao Systemctl

# Path to systemd service file
service_path = "/etc/systemd/system/suricata.service"

# Service file content
service_content = """[Unit]
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
"""

# Write the service file
with open(service_path, "w") as f:
    f.write(service_content)

print(f"Service file written to {service_path}")

# Reload systemd to recognize the new service
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