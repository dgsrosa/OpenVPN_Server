Contributing

Thanks for wanting to contribute! This repository contains system-level scripts (OpenVPN, iptables, Suricata, SSH/PAM) that can affect network connectivity and SSH access. Please review the safety notes below before running anything on a production machine.

Quick start

- Fork the repository
- Create a feature branch from `main`
- Make focused changes (one feature/fix per PR whenever possible)
- Test in a disposable VM/container or a spare device
- Open a Pull Request with a clear summary + test notes

Safety first (important)

- Test in a VM: these scripts modify `/etc/`, services, firewall rules and can lock you out.
- Keep a recovery path: have local console access (keyboard/HDMI) before touching SSH or firewall rules.
- Avoid destructive writes: do not overwrite system files like `/etc/sysctl.conf` entirely; update only the needed keys.
- Make changes idempotent: scripts that run on boot should not keep appending duplicate firewall rules.

Development guidelines

- Python:
  - Prefer `subprocess.run([...], check=True)` over `shell=True` when possible.
  - Validate inputs before using them to generate configs.
  - Fail fast with helpful error messages.
- Shell:
  - Use `set -euo pipefail` where reasonable.
  - Make firewall rules idempotent (`iptables -C ... || iptables -A ...`).
  - Parameterize interfaces (`WAN_IFACE`, etc.) instead of hard-coding `eth0`.
- Docs:
  - Keep instructions copy/paste friendly.
  - Document defaults and how to change them.

How to test

There’s no automated CI yet. For PRs, please include a short “Test plan” such as:

- OS/distro tested (example: Kali 2025.1 / Debian / Ubuntu)
- Ran installer script end-to-end
- Verified OpenVPN service starts and listens on UDP 1194
- Confirmed `.ovpn` files are generated and connect successfully
- Confirmed Suricata service starts and logs

Submitting changes

- Use descriptive branch names (examples: `docs/readme-install`, `fix/iptables-idempotent`, `feat/suricata-service`)
- Write clear commit messages explaining the why
- In your PR, include:
  - Summary: what changed and why
  - Test plan: what you ran and on what system
  - Risk: anything that could break users’ connectivity

