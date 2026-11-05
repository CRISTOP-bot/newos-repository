# NEWOS official package repository

This repository distributes native NEWOS `.new` artifacts. It is an initial **testing-only** feed, not yet a trusted production repository. The current `.new` v1 format protects against accidental corruption with CRC32, but that CRC is not publisher authentication. Testing metadata also carries SHA-256 for transport-integrity checks; until the index has a client-verified signature, it does not establish who published the package.

## Layout

- `repository/<channel>/<architecture>/index.json`: versioned JSON catalogue.
- `repository/<channel>/<architecture>/packages/`: immutable, version-named `.new` artifacts.
- `scripts/validate_repository.py`: validates catalog metadata, SHA-256, package format and CRC32 sections.
- `.github/workflows/validate.yml`: runs validation for pushes and pull requests.
- `metadata/`: repository protocol and release policy.

The `testing/x86_64` index contains `hello-new` 1.0.0 from NEWOS's committed sample artifact. `stable/x86_64` is intentionally empty pending authenticated index signing and real install/reboot testing.

## Current compatibility boundary

The current NEWOS kernel network stack implements Ethernet, ARP, IPv4 and ICMP only. It has no TCP, DNS, TLS, HTTP or userland downloader, and `newpkg` has no remote-index client. Thus this repository is consumable today by ordinary GitHub clients and host-side tooling, **not by `newpkg update/install` on NEWOS**. Do not advertise remote install commands until that client is implemented, compiled and tested against this protocol.

## Contributing

Submit a pull request with a `.new` artifact in the appropriate channel and architecture directory plus an updated index entry. CI rejects malformed metadata, unsupported package format, bad checksums, wrong SHA-256, duplicate package versions and unsafe artifact paths. Stable publication requires a maintainer review and a signed index; unsigned pull requests must not be promoted automatically.
