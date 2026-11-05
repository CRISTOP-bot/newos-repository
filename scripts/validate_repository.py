#!/usr/bin/env python3
"""Validate NEWOS repository indexes and immutable NEW1 package artifacts."""
import argparse, hashlib, json, pathlib, re, struct, sys, zlib

HEX64 = re.compile(r"^[0-9a-f]{64}$")
NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+~-]{0,62}$")
MAX_META, MAX_MANIFEST, MAX_FILES, MAX_PACKAGE = 4096, 65536, 1024, 32 * 1024 * 1024
ALLOWED = ("/bin/", "/sbin/", "/lib/", "/etc/", "/usr/", "/opt/", "/var/", "/home/", "/root/", "/tmp/")

def fail(s): raise ValueError(s)
def crc(b): return zlib.crc32(b) & 0xffffffff

def read_new(path):
    b = path.read_bytes()
    if len(b) < 48 or b[:4] != b"NEW1": fail(f"{path}: missing NEW1 header")
    version, flags = struct.unpack_from("<HH", b, 4)
    if version != 1 or flags != 0: fail(f"{path}: unsupported format version/flags")
    ml, fl, pl = struct.unpack_from("<III", b, 8)
    hc, mc, fc, pc, nf = struct.unpack_from("<IIIII", b, 20)
    if any(b[40:48]): fail(f"{path}: reserved header bytes must be zero")
    if ml == 0 or ml > MAX_META or fl == 0 or fl > MAX_MANIFEST or nf > MAX_FILES or len(b) != 48 + ml + fl + pl or len(b) > MAX_PACKAGE: fail(f"{path}: invalid section sizes")
    if crc(b[:20] + b[24:48]) != hc: fail(f"{path}: header CRC mismatch")
    meta_b, man_b, payload = b[48:48+ml], b[48+ml:48+ml+fl], b[48+ml+fl:]
    if crc(meta_b) != mc or crc(man_b) != fc or crc(payload) != pc: fail(f"{path}: section CRC mismatch")
    try: meta_text, man_text = meta_b.decode("utf-8"), man_b.decode("utf-8")
    except UnicodeDecodeError: fail(f"{path}: metadata/manifest is not UTF-8")
    meta = {}
    for line in meta_text.splitlines():
        k, sep, v = line.partition(": ")
        if not sep or not k or k in meta: fail(f"{path}: malformed/duplicate metadata key")
        meta[k] = v
    required = ("name", "version", "arch", "desc", "license", "maintainer", "build", "newos-min", "depends")
    if any(k not in meta for k in required) or any(not meta[k] for k in required if k != "depends"): fail(f"{path}: required metadata missing")
    if not NAME.fullmatch(meta['name']): fail(f"{path}: invalid package name")
    lines = man_text.splitlines()
    if not man_b.endswith(b"\n") or len(lines) != nf: fail(f"{path}: manifest count/terminator mismatch")
    prev, total = "", 0
    for line in lines:
        parts=line.split(" ",3)
        if len(parts)!=4: fail(f"{path}: malformed manifest entry")
        mode,size_s,crc_s,dst=parts
        if len(mode) not in (3,4) or any(c not in '01234567' for c in mode): fail(f"{path}: invalid file mode")
        if not re.fullmatch(r"[0-9a-f]{8}",crc_s): fail(f"{path}: invalid file CRC")
        if not dst.startswith(ALLOWED) or dst.endswith('/') or '//' in dst or any(x in ('.','..','') for x in dst[1:].split('/')) or any(not (c.isalnum() or c in '._+~@%=-/') for c in dst): fail(f"{path}: unsafe install path {dst!r}")
        if dst <= prev: fail(f"{path}: manifest must be strictly sorted")
        try: size=int(size_s)
        except ValueError: fail(f"{path}: invalid file size")
        if size < 0 or size > 8*1024*1024: fail(f"{path}: invalid file size")
        prev=dst; total += size
    if total != pl: fail(f"{path}: manifest payload size mismatch")
    # Verify individual file CRCs against their exact sequential payload slices.
    off=0
    for line in lines:
        mode,size_s,crc_s,dst=line.split(' ',3); size=int(size_s)
        if crc(payload[off:off+size]) != int(crc_s,16): fail(f"{path}: payload CRC mismatch for {dst}")
        off += size
    return meta, b

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); a=ap.parse_args(); root=pathlib.Path(a.root).resolve(); seen=set(); count=0
    for index in sorted(root.glob('repository/*/*/index.json')):
        rel=index.relative_to(root).parts
        if len(rel)!=4: fail(f"unexpected index path: {index}")
        _, channel, arch, _=rel
        data=json.loads(index.read_text(encoding='utf-8'))
        if data.get('schema_version') != 1 or data.get('channel') != channel or data.get('architecture') != arch: fail(f"{index}: schema/channel/arch mismatch")
        if not isinstance(data.get('packages'),list): fail(f"{index}: packages must be an array")
        for e in data['packages']:
            key=(e.get('name'),e.get('version'),e.get('architecture'))
            if key in seen: fail(f"duplicate package tuple: {key}")
            seen.add(key)
            if not NAME.fullmatch(e.get('name','')) or not e.get('version') or e.get('architecture')!=arch: fail(f"{index}: invalid package identity")
            if not HEX64.fullmatch(e.get('sha256','')): fail(f"{index}: invalid SHA-256")
            if not isinstance(e.get('depends'),list): fail(f"{index}: depends must be an array")
            loc=e.get('location','')
            if not loc or loc.startswith('/') or '\\' in loc or any(x in ('','.','..') for x in loc.split('/')): fail(f"{index}: unsafe artifact location")
            artifact=(index.parent / loc).resolve()
            if root not in artifact.parents or not artifact.is_file(): fail(f"{index}: missing/escaping package artifact {loc}")
            pkg, raw=read_new(artifact)
            if hashlib.sha256(raw).hexdigest()!=e['sha256'] or len(raw)!=e.get('size'): fail(f"{index}: size/SHA-256 mismatch for {key}")
            meta_expect={'name':e['name'],'version':e['version'],'arch':arch,'desc':e.get('description'),'license':e.get('license'),'maintainer':e.get('author')}
            for k,v in meta_expect.items():
                if v is None or pkg.get(k)!=str(v): fail(f"{index}: index/package metadata mismatch for {k}")
            if e.get('format')!='NEW1': fail(f"{index}: unsupported format field")
            count+=1
    print(f"repository validation: PASS ({count} packages, {len(seen)} unique identities)")
if __name__=='__main__':
    try: main()
    except Exception as ex: print(f"repository validation: FAIL: {ex}",file=sys.stderr); sys.exit(1)
