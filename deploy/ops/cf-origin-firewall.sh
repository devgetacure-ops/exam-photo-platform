#!/bin/bash
# Only Cloudflare may reach the site on 80 and 443 (DEC-106).
#
# The site is proxied by Cloudflare, but the origin still answered anyone who
# knew its address, so every protection bought at the edge -- the challenge,
# the rate limits, the WAF -- could be walked around by connecting to the IP.
# Docker publishes its ports past ufw, so the rule belongs in DOCKER-USER,
# which is the chain Docker leaves for exactly this.
#
# Ranges are fetched from Cloudflare and refreshed by a timer; if the fetch
# fails the existing rules are left alone rather than replaced by a guess.
# Port 22 is untouched: it is ufw's, and locking it here would be one bad
# fetch away from locking the owner out of their own server.
set -euo pipefail

V4_URL="https://www.cloudflare.com/ips-v4"
V6_URL="https://www.cloudflare.com/ips-v6"
PORTS="80,443"

v4="$(curl -fsS --max-time 20 "$V4_URL" || true)"
v6="$(curl -fsS --max-time 20 "$V6_URL" || true)"

if [ -z "$v4" ]; then
    echo "cf-origin-firewall: could not fetch IPv4 ranges; leaving rules as they are" >&2
    exit 1
fi

iptables -F DOCKER-USER
iptables -A DOCKER-USER -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN
while read -r range; do
    [ -n "$range" ] || continue
    iptables -A DOCKER-USER -s "$range" -p tcp -m multiport --dports "$PORTS" -j RETURN
done <<< "$v4"
# The server's own networks, so a health check or a container may still reach it.
for range in 127.0.0.0/8 10.0.0.0/8 172.16.0.0/12 192.168.0.0/16; do
    iptables -A DOCKER-USER -s "$range" -p tcp -m multiport --dports "$PORTS" -j RETURN
done
iptables -A DOCKER-USER -p tcp -m multiport --dports "$PORTS" -j DROP
iptables -A DOCKER-USER -j RETURN

if [ -n "$v6" ]; then
    ip6tables -F DOCKER-USER 2>/dev/null || true
    ip6tables -A DOCKER-USER -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN
    while read -r range; do
        [ -n "$range" ] || continue
        ip6tables -A DOCKER-USER -s "$range" -p tcp -m multiport --dports "$PORTS" -j RETURN
    done <<< "$v6"
    ip6tables -A DOCKER-USER -s ::1/128 -p tcp -m multiport --dports "$PORTS" -j RETURN
    ip6tables -A DOCKER-USER -s fc00::/7 -p tcp -m multiport --dports "$PORTS" -j RETURN
    ip6tables -A DOCKER-USER -p tcp -m multiport --dports "$PORTS" -j DROP
    ip6tables -A DOCKER-USER -j RETURN
fi

echo "cf-origin-firewall: $(echo "$v4" | grep -c .) IPv4 and $(echo "$v6" | grep -c .) IPv6 Cloudflare ranges allowed on $PORTS"
