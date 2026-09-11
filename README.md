# Ansible Role: unbound

![GitHub](https://img.shields.io/github/license/jomrr/ansible-role-unbound)
![GitHub last commit](https://img.shields.io/github/last-commit/jomrr/ansible-role-unbound)
![GitHub issues](https://img.shields.io/github/issues-raw/jomrr/ansible-role-unbound)
[![dev](https://img.shields.io/github/actions/workflow/status/jomrr/ansible-role-unbound/dev.yml?branch=dev&event=push&label=dev)](https://github.com/jomrr/ansible-role-unbound/actions/workflows/dev.yml?query=branch%3Adev)
[![main](https://img.shields.io/github/actions/workflow/status/jomrr/ansible-role-unbound/main.yml?branch=main&event=push&label=main)](https://github.com/jomrr/ansible-role-unbound/actions/workflows/main.yml?query=branch%3Amain)

Ansible role for a hardened Unbound DNS resolver with DoT, DNSSEC and response
policy zones.

## Purpose

Configure Unbound with DNS/DoT listeners, DNSSEC validation, DoT upstreams,
stub/forward/auth zones, local records, RPZ policies and hardening.

## Scope

### Managed

- Unbound packages, configuration, DNSSEC trust anchors and service
- Declared includes, static zone files and directories for zone downloads

### Not Managed

- Certificate issuance, deployment or renewal
- Firewall rules and SELinux/AppArmor adjustments for custom paths or ports

## Requirements

- DoT certificate chains and private keys must already exist and be readable by
  the unbound user.

## Dependencies

```yaml
collections:
  - name: community.general
    version: '>=12.0.0'
  - name: community.crypto
    version: '>=3.4.0'
  - name: ansible.posix
    version: '>=2.0.0'
  - name: containers.podman
    version: '>=1.20.0'
```

## Role Variables

### `unbound_backup`

Type: `bool`. Required: `false`.

Back up existing configuration and local zone files before replacing them.

Default:

```yaml
unbound_backup: true
```

### `unbound_interfaces`

Type: `list`. Required: `false`.

Listener addresses in address@port notation. Add a TLS-port listener and both
tls-service-key and tls-service-pem in unbound_server to serve DoT.

Default:

```yaml
unbound_interfaces:
  - 127.0.0.1@53
  - ::1@53
```

### `unbound_access_control`

Type: `list`. Required: `false`.

Client network access policies. The default refuses clients outside loopback.

Default:

```yaml
unbound_access_control:
  - net: 0.0.0.0/0
    action: refuse
  - net: ::/0
    action: refuse
  - net: 127.0.0.0/8
    action: allow
  - net: ::1/128
    action: allow
```

### `unbound_server_defaults`

Type: `dict`. Required: `false`.

Portable server baseline. Native option names; strings are quoted, booleans
become yes/no and lists repeat a directive. Prefer unbound_server for individual
changes.

Default:

```yaml
unbound_server_defaults:
  interface-automatic: false
  ip-transparent: false
  ip-freebind: false
  do-ip4: true
  do-ip6: true
  do-udp: true
  do-tcp: true
  tls-port: 853
  module-config: respip validator iterator
  val-permissive-mode: false
  ignore-cd-flag: true
  val-clean-additional: true
  hide-identity: true
  hide-version: true
  hide-trustanchor: true
  minimal-responses: true
  harden-short-bufsize: true
  harden-glue: true
  harden-dnssec-stripped: true
  harden-below-nxdomain: true
  qname-minimisation: true
  qname-minimisation-strict: false
  aggressive-nsec: true
  do-not-query-localhost: true
  harden-referral-path: false
  harden-algo-downgrade: false
  harden-large-queries: false
  use-caps-for-id: false
  private-address:
    - 10.0.0.0/8
    - 172.16.0.0/12
    - 192.168.0.0/16
    - 169.254.0.0/16
    - fc00::/7
    - fe80::/10
    - ::ffff:0:0/96
  num-threads: 2
  msg-cache-size: 32m
  rrset-cache-size: 64m
  num-queries-per-thread: 1024
  outgoing-range: 2048
  incoming-num-tcp: 128
  outgoing-num-tcp: 64
  so-reuseport: true
  so-rcvbuf: 0
  so-sndbuf: 0
  edns-buffer-size: 1232
  max-udp-size: 1232
  prefetch: true
  prefetch-key: true
  cache-min-ttl: 0
  cache-max-ttl: 86400
  cache-max-negative-ttl: 60
  serve-expired: false
  use-syslog: true
  verbosity: 1
  log-queries: false
  log-replies: false
  log-tag-queryreply: true
  log-servfail: true
  val-log-level: 1
  statistics-interval: 0
  statistics-cumulative: true
  extended-statistics: true
```

### `unbound_server`

Type: `dict`. Required: `false`.

Native server options merged over platform defaults and unbound_server_defaults.
Lists replace the baseline list. Use dedicated variables for interfaces, ACLs,
local zones and records.

Default:

```yaml
unbound_server: {}
```

### `unbound_remote_control_defaults`

Type: `dict`. Required: `false`.

Local control baseline. The default socket is /run/unbound.ctl on Debian/Ubuntu
and /run/unbound/control.sock on RedHat/Suse.

Default:

```yaml
unbound_remote_control_defaults:
  control-enable: false
  control-use-cert: false
```

### `unbound_remote_control`

Type: `dict`. Required: `false`.

Native remote-control options merged over unbound_remote_control_defaults.
Certificate-free control is intended only for a Unix socket.

Default:

```yaml
unbound_remote_control: {}
```

### `unbound_forward_zones`

Type: `list`. Required: `false`.

Forward zones. Use forward-tls-upstream with address@853#certificate-name for
authenticated DoT.

Default:

```yaml
unbound_forward_zones: []
```

### `unbound_stub_zones`

Type: `list`. Required: `false`.

Stub zones using authoritative DNS servers, optionally over DoT.

Default:

```yaml
unbound_stub_zones: []
```

### `unbound_auth_zones`

Type: `list`. Required: `false`.

Authority zones with local content rendered into zonefile, or AXFR/IXFR and
HTTP(S) sources.

Default:

```yaml
unbound_auth_zones: []
```

### `unbound_rpz_zones`

Type: `list`. Required: `false`.

Response policy zones in evaluation order; place local allow zones before block
feeds. Local content is rendered into zonefile. HTTP(S) URLs must serve complete
RPZ files, which Unbound downloads and refreshes into the zonefile cache.

Default:

```yaml
unbound_rpz_zones: []
```

### `unbound_local_zones`

Type: `list`. Required: `false`.

Local zone policies. Transparent internal forward/reverse zones prevent built-in
reverse-zone handling from intercepting queries.

Default:

```yaml
unbound_local_zones: []
```

### `unbound_local_data`

Type: `list`. Required: `false`.

Local records in DNS presentation format, without additional Unbound quoting.

Default:

```yaml
unbound_local_data: []
```

### `unbound_local_data_ptr`

Type: `list`. Required: `false`.

PTR shorthand records in address hostname notation.

Default:

```yaml
unbound_local_data_ptr: []
```

### `unbound_include_files`

Type: `list`. Required: `false`.

Configuration files written and included by their exact paths. Files in the
native local.d directory contain server options; other files require section
headers. Undeclared files are retained.

Default:

```yaml
unbound_include_files: []
```

### `unbound_includes`

Type: `list`. Required: `false`.

Additional top-level include paths or globs. Explicit globs load all matching
files.

Default:

```yaml
unbound_includes: []
```

## Managed Files

- `/etc/unbound/unbound.conf` Main configuration
- `/etc/unbound/unbound.conf.d/` Declared Debian/Ubuntu includes,
  remote-control.conf and the packaged root-auto-trust-anchor-file.conf
- `/etc/unbound/conf.d/ and /etc/unbound/local.d/` Declared
  AlmaLinux/Fedora/openSUSE includes and conf.d/remote-control.conf; local.d
  contains server options without a section header
- `/etc/unbound/<zonefile>` Local RPZ and authority files rendered from each
  zone's content
- `/var/lib/unbound/rpz and /var/lib/unbound/auth` Directories for caches
  downloaded or transferred by Unbound

## Service Behavior

Configuration changes are validated with unbound-checkconf and restart Unbound.
Certificate renewal must notify the restart handler or restart Unbound
separately.

### Handlers

- UNBOUND | Restart resolver

## Security Notes

- DoT upstream addresses need a certificate name, e.g.
  9.9.9.9@853#dns.quad9.net; without it, any certificate signed by a trusted CA
  is accepted.
- Keep forward-first false to prevent fallback when an encrypted forwarder
  fails.
- domain-insecure exempts unsigned internal zones from DNSSEC; private-domain
  permits private addresses in their answers.

## Operational Notes

- Declare include files in unbound_include_files; the role loads their exact
  paths.
  Removing an include or zone declaration leaves its files on disk but removes
  its
  configuration reference. Additional unbound_includes globs still load every
  matching file.
- Use one TLS authentication name per upstream IP/port with packages lacking the
  [Unbound 1.25 connection-reuse
  fix](https://www.nlnetlabs.nl/news/2026/Apr/29/unbound-1.25.0-released/).
  Older implementations may reuse a connection authenticated for a different
  name.
- Each RPZ entry contains its options and either local content or an external
  url/primary.
  Local content is rendered into zonefile. Place allow zones before block feeds;
  URLs must
  serve complete RPZ files with SOA/NS records. Use /var/lib/unbound/rpz for
  download caches.

## Supported Platforms

| OS Family | Distribution | Version | Container Image |
| --------- | ------------ | ------- | --------------- |
| RedHat | AlmaLinux | latest | [jomrr/molecule-almalinux:latest](https://hub.docker.com/r/jomrr/molecule-almalinux) |
| Debian | Debian | latest | [jomrr/molecule-debian:latest](https://hub.docker.com/r/jomrr/molecule-debian) |
| RedHat | Fedora | latest | [jomrr/molecule-fedora:latest](https://hub.docker.com/r/jomrr/molecule-fedora) |
| Suse | OpenSuse Leap | latest | [jomrr/molecule-opensuse-leap:latest](https://hub.docker.com/r/jomrr/molecule-opensuse-leap) |
| Suse | OpenSuse Tumbleweed | latest | [jomrr/molecule-opensuse-tumbleweed:latest](https://hub.docker.com/r/jomrr/molecule-opensuse-tumbleweed) |
| Debian | Ubuntu | latest | [jomrr/molecule-ubuntu:latest](https://hub.docker.com/r/jomrr/molecule-ubuntu) |

## Example Playbook

### Loopback validating resolver

The default enables DNSSEC recursion and loopback DNS without requiring
a TLS certificate.

```yaml
---
- name: Configure local resolver
  hosts: resolvers
  roles:
    - role: jomrr.unbound
```

### DoT service, AD forwarding and ordered RPZ

Replace example addresses, domains, certificates and the HTTPS feed
with real values.
Provision the TLS files before applying the role. The optional root forward zone
sends external queries over authenticated DoT. AD and reverse zones
use port 53.

```yaml
---
- name: Configure network resolver
  hosts: resolvers
  roles:
    - role: jomrr.unbound
      unbound_interfaces:
        - 127.0.0.1@53
        - 192.0.2.53@53
        - 192.0.2.53@853
      unbound_access_control:
        - {net: 0.0.0.0/0, action: refuse}
        - {net: '::/0', action: refuse}
        - {net: 127.0.0.0/8, action: allow}
        - {net: 192.0.2.0/24, action: allow}
        - {net: 198.51.100.0/24, action: allow}
      unbound_server:
        tls-service-key: /etc/unbound/tls/server.key
        tls-service-pem: /etc/unbound/tls/fullchain.pem
        private-domain: [ad.example.org.]
        domain-insecure: [ad.example.org., 2.0.192.in-addr.arpa.]
        use-syslog: false
        logfile: ""
        log-queries: true
        log-replies: true
      unbound_local_zones:
        - {name: ad.example.org., type: transparent}
        - {name: 2.0.192.in-addr.arpa., type: transparent}
      unbound_local_data:
        - resolver.example.org. 300 IN A 192.0.2.53
      unbound_forward_zones:
        - name: ad.example.org.
          forward-addr: [192.0.2.10@53, 192.0.2.11@53]
          forward-first: false
          forward-tls-upstream: false
          forward-no-cache: true
        - name: 2.0.192.in-addr.arpa.
          forward-addr: [192.0.2.10@53, 192.0.2.11@53]
          forward-first: false
          forward-tls-upstream: false
          forward-no-cache: true
        - name: .
          forward-addr:
            - 9.9.9.9@853#dns.quad9.net
            - 149.112.112.112@853#dns.quad9.net
          forward-tls-upstream: true
          forward-first: false
      unbound_rpz_zones:
        - name: local-allow.rpz.invalid.
          zonefile: /etc/unbound/rpz-allow.zone
          content: |
            $ORIGIN local-allow.rpz.invalid.
            @ 3600 IN SOA localhost. hostmaster.localhost. 1 3600 600 86400 60
            @ 3600 IN NS localhost.
            trusted.example.org 60 IN CNAME rpz-passthru.
          rpz-log: false
          for-downstream: false
        - name: security.rpz.example.org.
          url: [https://feeds.example.org/security.rpz]
          zonefile: /var/lib/unbound/rpz/blocklist.zone
          rpz-action-override: nxdomain
          rpz-log: true
          rpz-log-name: security-feed
          for-downstream: false
```

### Authoritative stub and static local authority

Stub zones require authoritative servers; forward zones require
recursive resolvers.

```yaml
unbound_stub_zones:
  - name: lab.example.org.
    stub-addr: [192.0.2.20@53, 192.0.2.21@53]
    stub-first: false
    stub-prime: false
unbound_server:
  domain-insecure: [lab.example.org., local.example.org.]
unbound_auth_zones:
  - name: local.example.org.
    zonefile: /etc/unbound/local.example.org.zone
    content: |
      $ORIGIN local.example.org.
      @ 300 IN SOA ns.local.example.org. hostmaster.local.example.org. (
        1 3600 600 86400 60 )
      @ 300 IN NS ns.local.example.org.
      ns 300 IN A 192.0.2.53
      app 300 IN A 192.0.2.80
    for-downstream: true
    for-upstream: true
```

## References

- <https://unbound.docs.nlnetlabs.nl/en/latest/manpages/unbound.conf.html>
- <https://unbound.docs.nlnetlabs.nl/en/latest/manpages/unbound-checkconf.html>
- <https://unbound.docs.nlnetlabs.nl/en/latest/topics/filtering/rpz.html>

## Author

[Jonas Mauer](https://github.com/jomrr)

## License

This project is licensed under the MIT License.
See [LICENSE](LICENSE) for the full license text.

Copyright (c) 2026 Jonas Mauer.
