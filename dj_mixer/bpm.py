from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import numpy as np

try:
    import librosa
except Exception as exc:  # pragma: no cover - handled gracefully at runtime
    librosa = None
    _LIBROSA_ERROR = exc
else:
    _LIBROSA_ERROR = None

logger = logging.getLogger(__name__)


@dataclass
class BPMResult:
    path: Path
    bpm: float


class BPMAnalyzer:
    """Analyze BPM values for tracks using librosa."""

    def __init__(self, hop_length: int = 512) -> None:
        if librosa is None:
            raise RuntimeError(
                "librosa could not be imported. Install it to enable BPM detection"
            ) from _LIBROSA_ERROR
        self.hop_length = hop_length

    def detect(self, audio_path: str | Path) -> BPMResult:
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(path)
        logger.info("Loading audio for BPM detection: %s", path)
        y, sr = librosa.load(path.as_posix(), mono=True)
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=self.hop_length)
        if tempo is None or np.isnan(tempo):
            raise ValueError(f"Unable to detect BPM for {path}")
        return BPMResult(path=path, bpm=float(tempo))

    def bulk_detect(self, paths: Iterable[str | Path]) -> list[BPMResult]:
        return [self.detect(path) for path in paths]


def safe_detect(analyzer: BPMAnalyzer, track: "Track") -> Optional[BPMResult]:
    from .track import Track  # Local import to avoid circular dependency

    if track.audio is None:
        return None
    try:
        return analyzer.detect(track.path)
    except Exception:  # pragma: no cover - fallback path
        logger.exception("Failed to detect BPM for track: %s", track.path)
        return None
