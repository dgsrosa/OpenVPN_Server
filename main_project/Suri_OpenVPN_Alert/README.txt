
- Modify the interface name in SuriOpenVPN to match the WAN interface on your system. By default, this is eth0.

- Suricata will run persistently as a service managed by systemctl.

- The provided script adds the GeoIP feature to suricata.yaml. This allows you to see the country of origin for connection attempts to your VPN.

- On a Raspberry Pi Zero 2 W, the default Suricata ruleset is too heavy and may cause crashes. For lightweight deployments, keep rules disabled. If you deploy on a more powerful machine, re‑enable rules in suricata.yaml and update them with: