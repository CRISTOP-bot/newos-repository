# Publishing policy

1. Build a native `.new` artifact with the builder shipped in NEWOS.
2. Put an immutable versioned artifact under `repository/<channel>/<arch>/packages/`.
3. Run `python3 scripts/generate_index.py` then `python3 scripts/validate_repository.py`.
4. Submit the artifact and regenerated index in a pull request. CI checks that index entries exactly match artifacts and verifies the NEW1 structure, CRCs and SHA-256.
5. A maintainer reviews provenance and executable compatibility before merging.

The initial workflow does not create releases or auto-promote to stable. GitHub Releases are not required for immutable artifacts served from the repository tree. Stable publication awaits client-side signed-index verification; no release URL should be consumed as authenticated metadata until that trust mechanism exists.
