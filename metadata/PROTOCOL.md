# Repository protocol v1

Each channel/architecture has an `index.json` with `schema_version`, `repository`, `channel`, `architecture`, `generated_at`, and `packages`. Each package entry specifies name, version, architecture, description, license, author, dependency constraints, byte size, lowercase SHA-256, a path relative to the index, minimum NEWOS version and `.new` format version.

Consumers must reject unknown schema versions, mismatched channel/architecture, duplicate `(name, version, architecture)`, invalid paths escaping the channel package directory, size mismatch, SHA-256 mismatch and invalid `.new` header/section/file/payload checksums. Dependency resolution must use package constraints and the installed database, never run package scripts (v1 has none).

## Authenticity status

SHA-256 is not a signature. The current `.new` v1 package format has CRC32, which detects accidental damage but is not cryptographic authentication. This repository does not yet publish a trusted signing key or signed index. Stable must remain empty until a signing key is provisioned out-of-band, the public key fingerprint is verified and pinned by the eventual NEWOS client, and clients verify a detached signature over the exact index bytes before using any URL from it. Never trust a key supplied only by the same unsigned index. Do not commit private keys or use an unsigned index as a stable source.

Package payload authenticity is transitively provided by the signed index's SHA-256 entry; TLS is still required for privacy/transport safety once NEWOS supports it.
