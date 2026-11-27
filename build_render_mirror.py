"""Build the Render update site from the official TidalIsle release assets."""

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


RELEASES = "https://github.com/xia-skot/TidalIsle-Releases/releases"
ARCHIVE = ("1.2.2.3", "1.2.2.4", "1.2.2.5", "1.2.3.1")
SITE = os.environ["RENDER_EXTERNAL_URL"].rstrip("/")
PUBLIC = Path("public")
CURL = ["curl", "--fail", "--silent", "--show-error", "--location",
        "--proto", "=https", "--proto-redir", "=https", "--retry", "3"]


def read_manifest(path):
    data = subprocess.check_output([*CURL, f"{RELEASES}/{path}/latest.json"])
    manifest = json.loads(data.decode("utf-8-sig"))
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+){3}", manifest["Version"]):
        raise ValueError("Invalid release version")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", manifest["Sha256"]):
        raise ValueError("Invalid release hash")
    return manifest


def mirror(version, manifest):
    if manifest["Version"] != version:
        raise ValueError(f"Manifest does not match release {version}")
    name = f"TidalIsle-Setup-{version}.exe"
    target = PUBLIC / name
    subprocess.run([*CURL, f"{RELEASES}/download/v{version}/{name}",
                    "--output", str(target)], check=True)
    with target.open("rb") as package:
        digest = hashlib.sha256()
        for block in iter(lambda: package.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != manifest["Sha256"].lower():
        raise ValueError(f"Checksum mismatch for {name}")
    return f"{SITE}/{name}"


def main():
    PUBLIC.mkdir(exist_ok=True)
    latest = read_manifest("latest/download")
    for version in dict.fromkeys((*ARCHIVE, latest["Version"])):
        if version == latest["Version"]:
            latest["Url"] = mirror(version, latest)
        else:
            mirror(version, read_manifest(f"download/v{version}"))
    (PUBLIC / "latest.json").write_text(json.dumps(latest), encoding="utf-8")


if __name__ == "__main__":
    main()
