#!/usr/bin/env python3
"""Stage a patched TCE2 game module and its selected features into a Linux x86-64 server home."""
import argparse
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZIP_DEFLATED


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("features", choices=("voice", "bots", "both"))
    parser.add_argument("modules", type=Path, help="game-build/bin")
    parser.add_argument("home", type=Path, help="server fs_homepath")
    args = parser.parse_args()
    target = args.home / "tce2"
    assets = Path(__file__).resolve().parent / "assets" / "bots" / "ixvo_phrases.txt"
    server = args.modules / "qagame.mp.x86_64.so"
    client = args.modules / "cgame.mp.x86_64.so"
    voice = args.features in ("voice", "both")
    bots = args.features in ("bots", "both")
    sources = [server] + ([client] if voice else []) + ([assets] if bots else [])
    for source in sources:
        if not source.is_file():
            parser.error(f"Missing file: {source}")
    target.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=target) as tmp:
        work = Path(tmp)
        shutil.copy2(server, work / server.name)
        if bots:
            (target / "bots").mkdir(exist_ok=True)
            shutil.copyfile(assets, work / assets.name)
        if voice:
            package = work / "z_ixvo-voice-linux64.pk3"
            with ZipFile(package, "w", ZIP_DEFLATED) as archive:
                archive.write(client, client.name)
                archive.writestr("ixvo/client.manifest", "1\n")
            package.replace(target / package.name)
        if bots:
            (work / assets.name).replace(target / "bots" / assets.name)
        (work / server.name).replace(target / server.name)
    print(f"Staged {args.features} in {target.resolve()}")


if __name__ == "__main__":
    main()
