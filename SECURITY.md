Security Policy

If you believe you have found a security vulnerability in this project:

- Do not open a public issue with exploit details.
- Prefer responsible disclosure by contacting the maintainer privately.

What to include

- A clear description of the issue and impact
- Steps to reproduce
- Any logs or configuration snippets that help (redact secrets)
- Your environment (distro/version, OpenVPN/Suricata versions)

Scope notes

This repo contains scripts that can modify system configuration and services. Please be especially careful with:

- file permission changes
- firewall rules
- SSH/PAM configuration
- scripts that run at boot via cron/systemd

