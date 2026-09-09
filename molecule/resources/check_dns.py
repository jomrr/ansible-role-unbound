"""Exercise resolver transports, zone routing, access control and response policies."""

import ipaddress
from pathlib import Path
import socket
import ssl
import struct
import sys
import time


def query(name: str, transport: str = "udp", host: str = "127.0.0.1",
          record_type: int = 1) -> bytes:
    """Return one complete DNS response, authenticating the DoT endpoint."""
    labels = b"".join(bytes([len(part)]) + part.encode("ascii")
                      for part in name.rstrip(".").split(".")) + b"\x00"
    packet = struct.pack("!6H", 1234, 0x100, 1, 0, 0, 0)
    packet += labels + struct.pack("!2H", record_type, 1)
    if transport == "udp":
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
            connection.settimeout(15)
            connection.sendto(packet, (host, 53))
            return connection.recv(65535)
    port = 853 if transport == "tls" else 53
    with socket.create_connection((host, port), timeout=15) as connection:
        if transport == "tls":
            context = ssl.create_default_context(cafile="/etc/unbound/tls/molecule.pem")
            with context.wrap_socket(
                connection, server_hostname="resolver.molecule.test"
            ) as secure:
                return exchange(secure, packet)
        return exchange(connection, packet)


def exchange(connection: socket.socket, packet: bytes) -> bytes:
    """Exchange a length-prefixed DNS message over TCP or TLS."""
    connection.sendall(struct.pack("!H", len(packet)) + packet)
    size = struct.unpack("!H", receive(connection, 2))[0]
    return receive(connection, size)


def receive(connection: socket.socket, size: int) -> bytes:
    """Read the entire DNS frame even when split between TCP segments."""
    result = b""
    while len(result) < size:
        part = connection.recv(size - len(result))
        if not part:
            raise RuntimeError("Truncated DNS response")
        result += part
    return result


def expect(name: str, address: str, transport: str = "udp") -> None:
    """Require successful resolution containing the expected address."""
    response = query(name, transport)
    assert response[3] & 0xF == 0, (name, response.hex())
    assert struct.unpack("!H", response[6:8])[0] > 0, name
    assert ipaddress.ip_address(address).packed in response, (name, response.hex())
    print(f"PASS {transport}: {name} -> {address}")


def main() -> None:
    """Verify role-owned DNS behavior without depending on public resolvers."""
    control_socket = (
        "/run/unbound.ctl" if sys.argv[2] == "Debian" else "/run/unbound/control.sock"
    )
    assert not Path(control_socket).exists(), control_socket
    print("PASS remote control disabled")
    for obsolete in (
        "/etc/unbound/unbound.conf.d/obsolete.conf",
        "/etc/unbound/conf.d/obsolete.conf",
        "/etc/unbound/local.d/obsolete.conf",
        "/etc/unbound/obsolete-zone",
        "/var/lib/unbound/rpz/obsolete.zone",
        "/var/lib/unbound/auth/obsolete.zone",
    ):
        assert not Path(obsolete).exists(), obsolete
    for retained in (
        "/etc/unbound/auth-test.zone", "/etc/unbound/allow-test.rpz",
        "/etc/unbound/tls/molecule.key", "/etc/unbound/tls/molecule.pem",
        "/var/lib/unbound/root.key",
    ):
        assert Path(retained).is_file(), retained
    if sys.argv[2] == "Debian":
        assert Path("/etc/unbound/unbound.conf.d/root-auto-trust-anchor-file.conf").is_file()
    print("PASS obsolete includes/zones removed; active zones, TLS and DNSSEC files retained")
    for transport in ("udp", "tcp", "tls"):
        expect("local.molecule.test", "192.0.2.53", transport)
    expect("included.molecule.test", "192.0.2.90")
    expect("server-include.molecule.test", "192.0.2.91")
    expect("www.forward.test", "192.0.2.80")
    expect("www.stub.test", "192.0.2.81")
    expect("www.auth.test", "192.0.2.82")
    expect("www.encrypted.test", "192.0.2.83")
    expect("allowed.forward.test", "192.0.2.84")
    expect("private-allowed.forward.test", "10.23.0.7")
    reverse = query("53.2.0.192.in-addr.arpa", record_type=12)
    assert reverse[3] & 0xF == 0 and b"local" in reverse, reverse.hex()
    text = query("text.molecule.test", record_type=16)
    assert text[3] & 0xF == 0 and b"hello unbound's resolver" in text, text.hex()
    reverse_forward = query("10.2.0.192.in-addr.arpa", record_type=12)
    assert reverse_forward[3] & 0xF == 0 and b"dc1" in reverse_forward, reverse_forward.hex()
    rebind = query("private.forward.test")
    assert ipaddress.ip_address("10.23.0.8").packed not in rebind, rebind.hex()
    refused = query("local.molecule.test", host=sys.argv[1])
    assert refused[3] & 0xF == 5, refused.hex()
    print("PASS PTR, TXT, reverse forwarding, rebinding protection and refused client")
    for _attempt in range(30):
        blocked = query("blocked.forward.test")
        if blocked[3] & 0xF == 3:
            break
        time.sleep(1)
    else:
        raise AssertionError("HTTPS RPZ feed did not produce NXDOMAIN")
    expect("allowed.forward.test", "192.0.2.84")
    print("PASS HTTPS RPZ download, blocking and preceding local allow policy")
    bogus = query("www.bogus.test")
    assert bogus[3] & 0xF == 2, bogus.hex()
    print("PASS DNSSEC rejects an unsigned answer below a configured trust anchor")
    # The certificate does not authenticate wrong.molecule.test. No plaintext fallback is allowed.
    bad_tls = query("www.bad-tls.test")
    assert bad_tls[3] & 0xF == 2, bad_tls.hex()
    print("PASS rejection of an incorrectly authenticated DoT upstream")


if __name__ == "__main__":
    main()
