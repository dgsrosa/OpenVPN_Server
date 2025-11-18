#!/bin/bash

# Habilita encaminhamento IP
sysctl -w net.ipv4.ip_forward=1
sudo sysctl -w net.ipv6.conf.all.forwarding=1

# ERRADO, PORTA DEVE SER 1194
# Aplica regra de firewall para permitir tráfego VPN
sudo iptables -A INPUT -p udp --dport 1194 -j ACCEPT
sudo iptables -A OUTPUT -p udp --sport 1194 -j ACCEPT


# Aplica regra de NAT para VPN
sudo iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o eth0 -j MASQUERADE
sudo iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o eth0 -j MASQUERADE
sudo ip6tables -A INPUT -p udp --dport 1194 -j ACCEPT

# Script OK, Reaplicado no BOOT -> OK
