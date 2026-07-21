"""
Scan a project's Python files for Discord emoji markdown (<:name:id> /
<a:name:id>) and download every unique emoji's image into an `emojis/`
folder, ready to be re-uploaded as application emojis.

Usage:
    python download_emojis.py /path/to/project
    python download_emojis.py /path/to/project --out ./emojis
"""

import argparse
import re
import sys
import time
from pathlib import Path

import requests

EMOJI_PATTERN = re.compile(r"<(a?):(\w+):(\d+)>")
CDN_URL = "https://cdn.discordapp.com/emojis/{id}.{ext}"

# Discord's CDN sits behind Cloudflare, which can 403 requests that don't
# look enough like a real browser (missing Accept/Referer/etc.), or that
# arrive too fast back-to-back. A fuller header set + a small delay between
# requests + a session (reused connection) generally gets past this.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://discord.com/",
}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def fetch(url: str, retries: int = 3, delay: float = 0.5) -> bytes:
    last_error = None
    for attempt in range(retries):
        try:
            resp = SESSION.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.content
            last_error = f"HTTP {resp.status_code}"
        except requests.RequestException as e:
            last_error = str(e)
        time.sleep(delay * (attempt + 1))  # back off a bit longer each retry
    raise RuntimeError(last_error)


def find_emojis(root: Path, extensions: tuple[str, ...] = (".py",)) -> dict[str, dict]:
    results: dict[str, dict] = {}

    for path in root.rglob("*"):
        if path.suffix not in extensions or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError as e:
            print(f"  ! could not read {path}: {e}", file=sys.stderr)
            continue

        for animated_flag, name, emoji_id in EMOJI_PATTERN.findall(text):
            animated = animated_flag == "a"
            entry = results.setdefault(name, {"id": emoji_id, "animated": animated})
            if entry["id"] != emoji_id:
                print(
                    f"  ! WARNING: '{name}' has conflicting IDs "
                    f"({entry['id']} vs {emoji_id}) in {path}",
                    file=sys.stderr,
                )

    return results


def download_images(emojis: dict[str, dict], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    ok, failed = 0, 0

    for name, info in sorted(emojis.items()):
        ext = "gif" if info["animated"] else "png"
        url = CDN_URL.format(id=info["id"], ext=ext)
        dest = out_dir / f"{name}.{ext}"
        try:
            data = fetch(url)
            dest.write_bytes(data)
            print(f"  ok: {name}.{ext}")
            ok += 1
        except Exception as e:
            print(f"  ! failed: {name} ({url}) -> {e}", file=sys.stderr)
            failed += 1
        time.sleep(0.3)  # be polite to the CDN across ~100+ sequential requests

    print(f"\nDone. {ok} downloaded, {failed} failed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path, help="Path to your project root")
    parser.add_argument(
        "--ext",
        nargs="+",
        default=[".py"],
        help="File extensions to scan (default: .py)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("emojis"),
        help="Output folder (default: ./emojis)",
    )
    args = parser.parse_args()

    root = args.project_root.resolve()
    if not root.exists():
        print(f"Path does not exist: {root}", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning {root} for emoji markdown ({', '.join(args.ext)})...")
    emojis = find_emojis(root, tuple(args.ext))
    print(f"Found {len(emojis)} unique emoji(s).\n")

    print(f"Downloading into {args.out.resolve()}...")
    download_images(emojis, args.out)


if __name__ == "__main__":
    main()
