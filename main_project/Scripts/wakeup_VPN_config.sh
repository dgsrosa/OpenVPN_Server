#!/bin/bash

set -euo pipefail

VPN_PORT="${VPN_PORT:-1194}"
VPN_NET="${VPN_NET:-10.8.0.0/24}"
WAN_IFACE="${WAN_IFACE:-eth0}"

# Habilita encaminhamento IP
sysctl -w net.ipv4.ip_forward=1 >/dev/null
sysctl -w net.ipv6.conf.all.forwarding=1 >/dev/null || true

# Aplica regra de firewall para permitir tráfego VPN
iptables -C INPUT -p udp --dport "$VPN_PORT" -j ACCEPT 2>/dev/null || \
  iptables -A INPUT -p udp --dport "$VPN_PORT" -j ACCEPT
iptables -C OUTPUT -p udp --sport "$VPN_PORT" -j ACCEPT 2>/dev/null || \
  iptables -A OUTPUT -p udp --sport "$VPN_PORT" -j ACCEPT


# Aplica regra de NAT para VPN
iptables -t nat -C POSTROUTING -s "$VPN_NET" -o "$WAN_IFACE" -j MASQUERADE 2>/dev/null || \
  iptables -t nat -A POSTROUTING -s "$VPN_NET" -o "$WAN_IFACE" -j MASQUERADE

ip6tables -C INPUT -p udp --dport "$VPN_PORT" -j ACCEPT 2>/dev/null || \
  ip6tables -A INPUT -p udp --dport "$VPN_PORT" -j ACCEPT

# Script OK, Reaplicado no BOOT -> OK
