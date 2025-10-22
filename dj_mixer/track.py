from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from pydub import AudioSegment


@dataclass
class Track:
    """Container that stores metadata and audio data for a track."""

    path: Path
    title: str
    bpm: Optional[float] = None
    audio: Optional[AudioSegment] = field(default=None, repr=False)

    @classmethod
    def from_file(cls, file_path: str | Path) -> "Track":
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(path)
        title = path.stem
        audio = AudioSegment.from_file(path)
        return cls(path=path, title=title, audio=audio)

    @property
    def duration_seconds(self) -> float:
        if self.audio is None:
            return 0.0
        return self.audio.duration_seconds

    def set_bpm(self, bpm: float) -> None:
        self.bpm = float(bpm)

    def formatted_duration(self) -> str:
        total_seconds = int(self.duration_seconds)
        minutes, seconds = divmod(total_seconds, 60)
        return f"{minutes}:{seconds:02d}"
