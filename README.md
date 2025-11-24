Please, run Install_OpenVPN_EasyRSA.py script with Sudo. This should be enough to set your server listenning on 1194.

- Ensure with you Internet Provider to redirect this traffic to this port and set a staticl LAN Ipv4 for the server.

- Im trying to figure out how reflect the real IP out of CGNAT to use NoIP, i was not able to complete this task yet.

- MTU was set by default. Ensure to adjust the better MTU for the server and Client, run a Iperf3 (I pretend to automate this).

- Adjust your interface on wakeup_VPN_config.sh

- The OVPN File will be generated in the same Path of ./Scripts folder.

- If you want, Install suri_openVPN.py to have a silly alert when someone connects to your VPN. I will refine this.. add a callmebot notification also. Be patient. 

TESTED AND WORKED ON:

Distributor ID:	Kali
Description:	Kali GNU/Linux Rolling
Release:	2025.1
Codename:	kali-rolling
                                                                                                                     
5.15.44-Re4son-v7+

