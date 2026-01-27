Run the installer with `sudo`. This should be enough to set your server listening on UDP 1194.

Installer path:

- `main_project/Scripts/Install_OpenVPN_EasyRSA.py`

Example:

```bash
sudo python3 main_project/Scripts/Install_OpenVPN_EasyRSA.py
```

At the end, it will ask if you want to install Suricata IDS (select yes to install it).

- Ensure your Internet provider/router forwards UDP 1194 to your server and your server has a static LAN IPv4.

- If you are behind CGNAT, dynamic DNS (No-IP) may not be enough by itself. You may need port forwarding on a public IP / VPN / tunnel solution.

- MTU is set by default. You may need to tune MTU/MSS (`tun-mtu`, `mssfix`) depending on your network. (Future: automate with iperf3.)

- Adjust your WAN interface in `main_project/Scripts/wakeup_VPN_config.sh` (default is `eth0`).

- The `.ovpn` files are generated inside `main_project/Scripts/` (same folder as the scripts).

- If you want, install Suricata IDS to inspect your WAN interface (default configured as `eth0`).

- I used "[Scapy](https://github.com/secdev/scapy): Python-based interactive packet manipulation library" for testing Suricata Rules. There is another branch created only for tests, "scapy-Suri-tests.py".

Safety notes

These scripts can modify system configuration (`/etc/`), firewall rules and SSH/PAM. Test in a VM first.


TESTED AND WORKED ON:

Distributor ID:	Kali
Description:	Kali GNU/Linux Rolling
Release:	2025.1
Codename:	kali-rolling
                                                                                                                     
5.15.44-Re4son-v7+

