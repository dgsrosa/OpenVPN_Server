#!/usr/bin/env python3
import subprocess
import os
import sys

def run_cmd(cmd):
    print(f"[*] Running: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def require_root() -> None:
    if os.name != "posix":
        return
    if hasattr(os, "geteuid") and os.geteuid() != 0:
        print("Error: run with sudo (e.g. sudo python3 SSH_Impl.py).", file=sys.stderr)
        sys.exit(1)

def set_or_append_config(lines: list[str], key: str, value: str) -> list[str]:
    """
    Replace key in sshd_config-style file, preserving other lines.
    If not found, append at end.
    """
    out = []
    found = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(f"{key} " ) or stripped.startswith(f"{key}\t") or stripped.startswith(f"#{key} "):
            out.append(f"{key} {value}\n")
            found = True
        else:
            out.append(line)
    if not found:
        if out and not out[-1].endswith("\n"):
            out[-1] = out[-1] + "\n"
        out.append(f"\n{key} {value}\n")
    return out

def main():
    require_root()
    target_user = os.environ.get("SUDO_USER") or os.environ.get("USER") or "root"

    # Step 1: Update packages
    run_cmd("sudo apt update")
    
    # Step 4: Install Google Authenticator PAM module
    run_cmd("sudo apt install -y libpam-google-authenticator")
    run_cmd(f"sudo -u {target_user} google-authenticator -t -d -f -r 3 -R 30 -w 3")
    run_cmd(f"sudo -u {target_user} ls -la ~{target_user}/.google_authenticator")



    # Step 6: Update PAM configuration
    pam_file = "/etc/pam.d/sshd"
    with open(pam_file, "r") as f:
        lines = f.readlines()

    new_lines = []
    inserted = False
    already_present = any("pam_google_authenticator.so" in l for l in lines)
    for line in lines:
        new_lines.append(line)
        if "@include common-password" in line and not inserted and not already_present:
            new_lines.append("auth required pam_google_authenticator.so\n")
            inserted = True

    with open(pam_file, "w") as f:
        f.writelines(new_lines)

    print(f"[+] Updated {pam_file}")

    # Step 7: Update SSH configuration
    sshd_config = "/etc/ssh/sshd_config"
    with open(sshd_config, "r") as f:
        lines = f.readlines()

    # Preserve file, just ensure required keys exist
    new_lines = set_or_append_config(lines, "ChallengeResponseAuthentication", "yes")
    new_lines = set_or_append_config(new_lines, "UsePAM", "yes")

    with open(sshd_config, "w") as f:
        f.writelines(new_lines)

    print(f"[+] Updated {sshd_config}")

    # Step 8: Restart SSH service
    run_cmd("sudo systemctl restart sshd")
    print("[✓] SSH service restarted with MFA enabled.")

if __name__ == "__main__":
    main()