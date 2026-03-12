#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


DEFAULT_REPO = "imadtg/TKUS-CE"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download a released TKUS-CE runner JAR and record exact provenance.")
    parser.add_argument("--repo", default=DEFAULT_REPO, help="GitHub repository in owner/name form.")
    parser.add_argument("--spec", default="latest", help="Release selector: latest, x.y.z, or vx.y.z.")
    parser.add_argument("--output-jar", required=True, help="Path to the downloaded JAR.")
    parser.add_argument("--output-json", required=True, help="Path to the provenance JSON.")
    return parser.parse_args()


def github_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "tkus-ce-release-fetcher",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def http_get_json(url: str) -> dict[str, Any]:
    request = Request(url, headers=github_headers())
    try:
        with urlopen(request) as response:
            return json.load(response)
    except HTTPError:
        if not shutil_which("gh"):
            raise
        result = subprocess.run(
            ["gh", "api", url],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout)


def http_get_bytes(url: str) -> bytes:
    request = Request(url, headers=github_headers())
    with urlopen(request) as response:
        return response.read()


def shutil_which(binary: str) -> str | None:
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(directory) / binary
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def gh_asset_bytes(asset_api_url: str) -> bytes:
    result = subprocess.run(
        ["gh", "api", asset_api_url, "-H", "Accept: application/octet-stream"],
        check=True,
        capture_output=True,
    )
    return result.stdout


def fetch_asset_bytes(asset: dict[str, Any]) -> bytes:
    try:
        return http_get_bytes(asset["browser_download_url"])
    except HTTPError:
        if not shutil_which("gh"):
            raise
        return gh_asset_bytes(asset["url"])


def resolve_release(repo: str, spec: str) -> dict[str, Any]:
    normalized = spec.strip()
    if normalized == "latest":
        url = f"https://api.github.com/repos/{repo}/releases/latest"
    else:
        tag = normalized if normalized.startswith("v") else f"v{normalized}"
        url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
    try:
        return http_get_json(url)
    except HTTPError as exc:
        raise SystemExit(f"Failed to resolve release '{spec}' from {repo}: HTTP {exc.code}") from exc


def find_asset(release: dict[str, Any], suffix: str) -> dict[str, Any] | None:
    for asset in release.get("assets", []):
        if str(asset.get("name", "")).endswith(suffix):
            return asset
    return None


def normalize_sha256(content: bytes) -> str:
    return content.decode().strip().split()[0]


def flatten_build_metadata(build_metadata: dict[str, Any]) -> dict[str, Any]:
    flattened = {}
    for key in ["version", "release_channel", "git_ref", "git_sha", "repository", "built_at_utc"]:
        if key in build_metadata:
            flattened[f"runner_{key}"] = build_metadata[key]
    return flattened


def main() -> int:
    args = parse_args()
    release = resolve_release(args.repo, args.spec)
    jar_asset = find_asset(release, ".jar")
    if jar_asset is None:
        raise SystemExit(f"No .jar asset found on release {release.get('tag_name')}")

    build_asset = find_asset(release, ".jar.build.json")
    sha_asset = find_asset(release, ".jar.sha256")

    jar_path = Path(args.output_jar).resolve()
    json_path = Path(args.output_json).resolve()
    jar_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    jar_bytes = fetch_asset_bytes(jar_asset)
    jar_path.write_bytes(jar_bytes)
    jar_sha256 = hashlib.sha256(jar_bytes).hexdigest()

    build_metadata: dict[str, Any] = {}
    if build_asset is not None:
        build_metadata = json.loads(fetch_asset_bytes(build_asset).decode())

    verified = None
    release_sha256 = None
    if sha_asset is not None:
        release_sha256 = normalize_sha256(fetch_asset_bytes(sha_asset))
        verified = release_sha256 == jar_sha256
        if not verified:
            raise SystemExit(f"Checksum mismatch for {jar_asset['name']}: expected {release_sha256}, got {jar_sha256}")

    provenance = {
        "runner_requested_spec": args.spec,
        "runner_repo": args.repo,
        "runner_resolved_tag": release.get("tag_name"),
        "runner_release_name": release.get("name"),
        "runner_release_id": release.get("id"),
        "runner_release_url": release.get("html_url"),
        "runner_release_published_at": release.get("published_at"),
        "runner_target_commitish": release.get("target_commitish"),
        "runner_asset_name": jar_asset.get("name"),
        "runner_asset_size_bytes": jar_asset.get("size"),
        "runner_asset_download_url": jar_asset.get("browser_download_url"),
        "runner_downloaded_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "runner_output_jar": str(jar_path),
        "runner_sha256": jar_sha256,
        "runner_sha256_from_release": release_sha256,
        "runner_sha256_verified": verified,
        **flatten_build_metadata(build_metadata),
        "release": release,
        "build_metadata": build_metadata,
    }
    if "runner_version" not in provenance and provenance["runner_resolved_tag"]:
        provenance["runner_version"] = str(provenance["runner_resolved_tag"]).removeprefix("v")
    if "runner_git_ref" not in provenance and provenance["runner_resolved_tag"]:
        provenance["runner_git_ref"] = provenance["runner_resolved_tag"]
    if "runner_git_sha" not in provenance and provenance["runner_target_commitish"]:
        provenance["runner_git_sha"] = provenance["runner_target_commitish"]

    json_path.write_text(json.dumps(provenance, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
