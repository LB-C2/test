from __future__ import annotations

import threading
from typing import Optional

from pydub import AudioSegment

try:  # pragma: no cover - optional dependency
    import simpleaudio
except Exception as exc:  # pragma: no cover - runtime feedback
    simpleaudio = None
    _SIMPLEAUDIO_ERROR = exc
else:
    _SIMPLEAUDIO_ERROR = None


class PreviewPlayer:
    """Simple synchronous preview player built on top of simpleaudio."""

    def __init__(self) -> None:
        if simpleaudio is None:
            raise RuntimeError(
                "simpleaudio could not be imported. Install it to enable previews"
            ) from _SIMPLEAUDIO_ERROR
        self._play_obj: Optional[simpleaudio.PlayObject] = None
        self._lock = threading.Lock()

    def play(self, segment: AudioSegment) -> None:
        with self._lock:
            self.stop()
            data = segment.set_channels(2).set_frame_rate(44100).set_sample_width(2)
            play_obj = simpleaudio.play_buffer(
                data.raw_data,
                num_channels=data.channels,
                bytes_per_sample=data.sample_width,
                sample_rate=data.frame_rate,
            )
            self._play_obj = play_obj

    def stop(self) -> None:
        with self._lock:
            if self._play_obj is not None:
                self._play_obj.stop()
                self._play_obj = None

    def is_playing(self) -> bool:
        with self._lock:
            return bool(self._play_obj and self._play_obj.is_playing())
