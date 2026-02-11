from __future__ import annotations

from dataclasses import dataclass
from typing import List


from .config import OneDriveConfig

GRAPH_ROOT = "https://graph.microsoft.com/v1.0"


@dataclass
class ResearchFile:
    name: str
    content: str


class OneDriveClient:
    def __init__(self, config: OneDriveConfig):
        self.config = config
        self.access_token = config.access_token

    def update_token(self, token: str) -> None:
        self.access_token = token

    def fetch_research_files(self) -> List[ResearchFile]:
        import requests

        headers = {"Authorization": f"Bearer {self.access_token}"}
        folder_url = (
            f"{GRAPH_ROOT}/drives/{self.config.drive_id}/root:/{self.config.folder_path}:/children"
        )
        response = requests.get(folder_url, headers=headers, timeout=30)
        response.raise_for_status()

        items = response.json().get("value", [])
        files: list[ResearchFile] = []
        for item in items[: self.config.max_files]:
            if "file" not in item:
                continue
            name = item.get("name", "unknown")
            if not any(name.lower().endswith(ext) for ext in [".txt", ".md", ".json", ".csv"]):
                continue

            download_url = item.get("@microsoft.graph.downloadUrl")
            if not download_url:
                continue
            content = requests.get(download_url, timeout=30).text
            files.append(ResearchFile(name=name, content=content))

        return files
