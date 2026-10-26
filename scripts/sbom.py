#!/usr/bin/env python3
"""Emit an SPDX 2.3 SBOM derived from .flox/env/manifest.lock.

This is not a scan. Every package, version, and store path comes straight
from the lockfile that flox resolved, so the SBOM describes exactly what
`flox activate`, `flox build`, and `flox containerize` will produce.
"""
import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path


def current_system() -> str:
    arch = {"arm64": "aarch64", "x86_64": "x86_64"}.get(platform.machine(), platform.machine())
    os_name = {"darwin": "darwin", "linux": "linux"}[sys.platform]
    return f"{arch}-{os_name}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lock", default=".flox/env/manifest.lock")
    ap.add_argument("--system", default=current_system())
    ap.add_argument("--name", default=Path.cwd().name)
    args = ap.parse_args()

    lock = json.loads(Path(args.lock).read_text())
    pkgs = [p for p in lock["packages"] if p["system"] == args.system]
    ns = f"https://github.com/smorin/deterministic-builds-google/sbom/{args.name}/{args.system}"

    spdx_pkgs, rels = [], []
    for p in sorted(pkgs, key=lambda p: p["install_id"]):
        spdx_id = f"SPDXRef-{p['install_id']}"
        spdx_pkgs.append({
            "SPDXID": spdx_id,
            "name": p["attr_path"],
            "versionInfo": p["version"],
            "downloadLocation": p["locked_url"],
            "licenseConcluded": p.get("license") or "NOASSERTION",
            "filesAnalyzed": False,
            "externalRefs": [{
                "referenceCategory": "PACKAGE-MANAGER",
                "referenceType": "purl",
                "referenceLocator": f"pkg:nix/{p['attr_path']}@{p['version']}?system={p['system']}",
            }],
            "annotations": [{
                "annotationType": "OTHER",
                "annotator": "Tool: flox-lock-sbom",
                "annotationDate": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "comment": "store-path " + p["outputs"]["out"],
            }],
        })
        rels.append({"spdxElementId": "SPDXRef-DOCUMENT", "relatedSpdxElement": spdx_id,
                     "relationshipType": "DESCRIBES"})

    doc = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"{args.name} ({args.system})",
        "documentNamespace": ns,
        "creationInfo": {
            "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "creators": ["Tool: flox-lock-sbom", "Tool: flox"],
            "comment": "Derived from manifest.lock, not from a filesystem scan.",
        },
        "packages": spdx_pkgs,
        "relationships": rels,
    }
    json.dump(doc, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
