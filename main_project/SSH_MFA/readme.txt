SSH_MFA Authentication

- Ensure that you have SSH access already installed. 

- For safety, create a .img backup. Any mistakes may cause you to lose SSH access.

    WARNING:

        - Test in another terminal that the access is OK, in case of fail:

            # Disable MFA in PAM
                
                sudo sed -i '/pam_google_authenticator.so/d' /etc/pam.d/sshd

            # Disable ChallengeResponseAuthentication

                sudo sed -i 's/^ChallengeResponseAuthentication.*/ChallengeResponseAuthentication no/' /etc/ssh/sshd_config

            # Restart SSH

                sudo systemctl restart sshd

- If you cannot connect, use HDMI and a keyboard to access the system locally.

- SSH access with MFA provides safe and reliable remote access to your server.

- Add the QR code to your Authenticator app and save the secret keys securely.


