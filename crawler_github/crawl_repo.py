from __future__ import annotations
import asyncio, base64, json, os, mimetypes
from pathlib import Path
from urllib.parse import urlparse

import aiofiles, httpx
from shared.db import github_collection
from tqdm import tqdm

GITHUB_API = "https://api.github.com"
TOKEN_ENV_VAR = "GITHUB_TOKEN"
FILE_SNIPPET_LIMIT = 100_000  

# ---------- extensión → “kind” ---------------------------------------▲
EXT_KIND = {
    ".py": "python",
    ".ipynb": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".md": "markdown",
    ".rst": "markdown",
    ".txt": "text",
    ".csv": "text",
    ".json": "text",
    ".html": "text",
    ".docx": "document",
    ".xlsx": "document",
    ".pdf": "pdf",
    ".png": "images",
    ".jpg": "images",
    ".jpeg": "images",
    ".gif": "images",
    ".mp4": "video",
    ".pbix": "binary",
    ".pyc": "binary",
}

def classify(path: str) -> str:
    # Classify a file path by its extension.
    return EXT_KIND.get(Path(path).suffix.lower(), "others")

class GithubRepoCrawler:
    def __init__(self, repo_url: str):
        self.owner, self.repo, self.branch = self._parse(repo_url.rstrip("/"))
        self.repo_url = repo_url

    async def run(self):
        headers = {
            "User-Agent": "GitHubCrawler-Python/0.1",
            "Accept": "application/vnd.github+json",
        }
        if token := os.getenv(TOKEN_ENV_VAR):
            headers["Authorization"] = f"token {token}"

        async with httpx.AsyncClient(headers=headers, http2=True, timeout=30) as cli:
            if self.branch is None:
                self.branch = await self._get_default_branch(cli)

            tree = (await cli.get(
                f"{GITHUB_API}/repos/{self.owner}/{self.repo}/git/trees/{self.branch}?recursive=1"
            )).json()["tree"]

            for item in tqdm(tree, desc=f"{self.owner}/{self.repo}", unit="item"):
                if item["type"] != "blob":
                    continue

                kind = classify(item["path"])
                await self._save_blob_to_mongo(cli, item, kind)

        print(f"✔︎ Repository data inserted in MongoDB: {self.owner}/{self.repo}")


    async def _save_blob_to_mongo(self, cli: httpx.AsyncClient, item: dict, kind: str):
        blob = await cli.get(item["url"])
        blob.raise_for_status()

        content_b64 = blob.json()["content"]
        raw_bytes = base64.b64decode(content_b64)
        file_size = len(raw_bytes)
        file_name = Path(item["path"]).name
        file_path = item["path"]

        document = {
            "repo_url": self.repo_url,
            "owner": self.owner,
            "repo": self.repo,
            "branch": self.branch,
            "path": file_path,
            "name": file_name,
            "kind": kind,
            "size_bytes": file_size,
        }

        # Text-based files: store content as UTF-8 string
        if kind in {"python", "markdown", "text", "javascript", "typescript", "c", "cpp", "java"}:
            try:
                document["content"] = raw_bytes.decode("utf-8")
            except UnicodeDecodeError:
                document["content"] = None  # fallback

        # Binary files: store base64 string or skip if too large
        elif kind in {"images", "pdf", "others"}:
            if file_size < 1_000_000:  # 1 MB max
                document["content_base64"] = content_b64
            else:
                document["content_base64"] = None  # too big, just skip content

        # Otros: registrar sin contenido
        else:
            document["content"] = None

        # Inserción (usa upsert por si ya existe)
        github_collection.update_one(
            {"repo_url": self.repo_url, "path": file_path},
            {"$set": document},
            upsert=True
        )


    async def _get_default_branch(self, cli: httpx.AsyncClient) -> str:
        # Get the default branch of the repository.
        repo_r = await cli.get(f"{GITHUB_API}/repos/{self.owner}/{self.repo}")
        repo_r.raise_for_status()
        return repo_r.json()["default_branch"]

    @staticmethod
    def _parse(url: str) -> tuple[str, str, str | None]:
        # Parse the GitHub repository URL to extract owner, repo, and branch.
        parts = urlparse(url).path.strip("/").split("/")
        owner, repo, *rest = parts if len(parts) >= 2 else (_ for _ in ()).throw(ValueError("Invalid URL"))
        branch = rest[2] if len(rest) >= 3 and rest[0] == "tree" else None
        return owner, repo, branch

# ----------------------------------------------------------------------
def crawl_repo(url: str, _max_pages: int | None = None):
    asyncio.run(GithubRepoCrawler(url).run())
