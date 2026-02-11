from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Tuple


import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .email_monitor import IncomingEmail
from .llm_client import LLMClient
from .onedrive_client import OneDriveClient, ResearchFile


@dataclass
class WorkflowOutput:
    subject: str
    body: str
    graph_path: Path | None


class InvestmentWorkflow:
    def __init__(self, onedrive: OneDriveClient, llm: LLMClient):
        self.onedrive = onedrive
        self.llm = llm

    def run(self, keyword: str, update_email: IncomingEmail) -> WorkflowOutput:
        research_files = self.onedrive.fetch_research_files()
        context = self._build_context(research_files)

        result = self.llm.synthesize(
            keyword=keyword,
            trigger_email=f"Subject: {update_email.subject}\nFrom: {update_email.from_email}\n\n{update_email.body}",
            history_context=context,
        )

        graph_path = self._build_graph(research_files, keyword)
        subject = f"{keyword} update detected: {update_email.subject}"
        body = result.formatted_email
        return WorkflowOutput(subject=subject, body=body, graph_path=graph_path)

    def _build_context(self, files: List[ResearchFile]) -> str:
        chunks: list[str] = []
        for f in files:
            snippet = f.content[:2500]
            chunks.append(f"### File: {f.name}\n{snippet}")
        return "\n\n".join(chunks)

    def _build_graph(self, files: List[ResearchFile], keyword: str) -> Path | None:
        points = _extract_scored_points(files)
        if not points:
            return None

        output_dir = Path("artifacts")
        output_dir.mkdir(parents=True, exist_ok=True)
        output = output_dir / f"{keyword}_trend.png"

        dates, scores = zip(*points)
        fig, ax = plt.subplots(figsize=(8, 4))
        try:
            ax.plot(dates, scores, marker="o")
            ax.set_title(f"{keyword} historical opinion trend")
            ax.set_xlabel("Date")
            ax.set_ylabel("Score")
            ax.grid(True, alpha=0.3)
            fig.tight_layout()
            fig.savefig(output)
        finally:
            plt.close(fig)

        return output


def _extract_scored_points(files: List[ResearchFile]) -> List[Tuple[datetime, float]]:
    points: list[Tuple[datetime, float]] = []

    for file in files:
        name_lower = file.name.lower()
        content = file.content

        if name_lower.endswith(".json"):
            points.extend(_extract_from_json(content))
        elif name_lower.endswith(".csv"):
            points.extend(_extract_from_csv(content))
        else:
            points.extend(_extract_from_text(content))

    return sorted(points, key=lambda t: t[0])


def _extract_from_json(content: str) -> List[Tuple[datetime, float]]:
    out: list[Tuple[datetime, float]] = []
    try:
        value = json.loads(content)
    except json.JSONDecodeError:
        return out

    items = value if isinstance(value, list) else [value]
    for item in items:
        if not isinstance(item, dict):
            continue
        date_raw = item.get("date")
        score_raw = item.get("score")
        point = _normalize_point(date_raw, score_raw)
        if point:
            out.append(point)
    return out


def _extract_from_csv(content: str) -> List[Tuple[datetime, float]]:
    out: list[Tuple[datetime, float]] = []
    reader = csv.DictReader(content.splitlines())
    for row in reader:
        point = _normalize_point(row.get("date"), row.get("score"))
        if point:
            out.append(point)
    return out


def _extract_from_text(content: str) -> List[Tuple[datetime, float]]:
    out: list[Tuple[datetime, float]] = []
    # Matches lines like: 2025-01-08 score: 0.42
    pattern = re.compile(r"(\d{4}-\d{2}-\d{2}).{0,20}?score[:=]\s*(-?\d+(?:\.\d+)?)", re.IGNORECASE)
    for date_raw, score_raw in pattern.findall(content):
        point = _normalize_point(date_raw, score_raw)
        if point:
            out.append(point)
    return out


def _normalize_point(date_raw: str | None, score_raw: str | float | int | None) -> Tuple[datetime, float] | None:
    if not date_raw or score_raw is None:
        return None
    try:
        date = datetime.fromisoformat(str(date_raw))
        score = float(score_raw)
    except (ValueError, TypeError):
        return None
    return date, score
