#!/usr/bin/env python3
import subprocess

def run_cmd(cmd):
    print(f"[*] Running: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

def main():
    # Step 1: Update packages
    run_cmd("sudo apt update")
    
    # Step 4: Install Google Authenticator PAM module
    run_cmd("sudo apt install -y libpam-google-authenticator")
    run_cmd("sudo -u dougl google-authenticator -t -d -f -r 3 -R 30 -w 3")
    run_cmd("ls -la /home/dougl/.google_authenticator")


    # Step 6: Update PAM configuration
    pam_file = "/etc/pam.d/sshd"
    with open(pam_file, "r") as f:
        lines = f.readlines()

    new_lines = []
    inserted = False
    for line in lines:
        new_lines.append(line)
        if "@include common-password" in line and not inserted:
            new_lines.append("auth required pam_google_authenticator.so\n")
            inserted = True

    with open(pam_file, "w") as f:
        f.writelines(new_lines)

    print(f"[+] Updated {pam_file}")

    # Step 7: Update SSH configuration
    sshd_config = "/etc/ssh/sshd_config"
    with open(sshd_config, "r") as f:
        lines = f.readlines()

    # Always put ChallengeResponseAuthentication at the first line
    new_lines = ["ChallengeResponseAuthentication yes\n"]

    # Then rewrite the rest, ensuring UsePAM is set
    found_usepam = False
    for line in lines:
        if line.strip().startswith("ChallengeResponseAuthentication"):
            continue  # skip old entries
        elif line.strip().startswith("UsePAM"):
            new_lines.append("UsePAM yes\n")
            found_usepam = True
        else:
            new_lines.append(line)

    if not found_usepam:
        new_lines.append("UsePAM yes\n")

    with open(sshd_config, "w") as f:
        f.writelines(new_lines)

    print(f"[+] Updated {sshd_config}")

    # Step 8: Restart SSH service
    run_cmd("sudo systemctl restart sshd")
    print("[✓] SSH service restarted with MFA enabled.")

if __name__ == "__main__":
    main()