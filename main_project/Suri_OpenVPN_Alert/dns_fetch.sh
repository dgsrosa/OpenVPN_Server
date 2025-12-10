#!/bin/bash

RULE_FILE="/etc/suricata/rules/dns.bad_domains.rules"
SOURCE_URL="https://urlhaus.abuse.ch/downloads/json_online/"

# Backup old rules if present
if [ -f "$RULE_FILE" ]; then
    cp "$RULE_FILE" "${RULE_FILE}.bak.$(date +%F)"
fi

# Write header
echo "# Auto-generated bad DNS/IP rules $(date)" > "$RULE_FILE"

# Start SID counter in a safe custom range
sid=4000000

# Fetch URLhaus JSON, extract hostnames/IPs, deduplicate
curl -s "$SOURCE_URL" \
  | jq -r '.[] | .[] | .url' \
  | awk -F/ '{print $3}' \
  | sort -u \
  | while read host; do
      [ -z "$host" ] && continue

      # Check if it's an IP (with optional port)
      if [[ "$host" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+(:[0-9]+)?$ ]]; then
          ip=$(echo "$host" | cut -d: -f1)
          port=$(echo "$host" | cut -s -d: -f2)

          if [ -n "$port" ]; then
              echo "alert tcp any any -> $ip $port (msg:\"Traffic to malicious IP $ip:$port\"; sid:$sid; rev:1;)" >> "$RULE_FILE"
          else
              echo "alert ip any any -> $ip any (msg:\"Traffic to malicious IP $ip\"; sid:$sid; rev:1;)" >> "$RULE_FILE"
          fi
      else
          # It's a domain
          echo "alert dns any any -> any any (msg:\"Malicious domain $host accessed\"; dns.query; content:\"$host\"; nocase; sid:$sid; rev:1;)" >> "$RULE_FILE"
      fi

      sid=$((sid+1))
  done

# Test Suricata config before reload
if ! suricata -T -c /etc/suricata/suricata.yaml; then
    echo "Suricata config test failed. Not reloading."
    exit 1
fi

# Reload Suricata to apply new rules
systemctl reload suricata
