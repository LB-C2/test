from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import numpy as np
from pydub import AudioSegment

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    import pyrubberband as pyrb
except Exception:  # pragma: no cover - optional dependency
    pyrb = None


@dataclass
class MixResult:
    audio: AudioSegment
    output_path: Optional[Path] = None


class MixdownEngine:
    """Combine audio tracks with crossfading and optional tempo matching."""

    def __init__(self, crossfade_seconds: float = 10.0, tempo_matching: bool = True) -> None:
        self.crossfade_seconds = crossfade_seconds
        self.tempo_matching = tempo_matching

    @property
    def crossfade_ms(self) -> int:
        return int(self.crossfade_seconds * 1000)

    def render(self, tracks: Iterable["Track"], output_path: Optional[str | Path] = None) -> MixResult:
        from .track import Track  # local import to avoid circular dependency

        tracks = [track for track in tracks if track.audio is not None]
        if not tracks:
            raise ValueError("No tracks loaded")

        mixed = tracks[0].audio
        previous_bpm = tracks[0].bpm
        for track in tracks[1:]:
            segment = track.audio
            if self.tempo_matching and previous_bpm and track.bpm:
                segment = self._match_tempo(segment, track.bpm, previous_bpm)
            mixed = mixed.append(segment, crossfade=self.crossfade_ms)
            previous_bpm = track.bpm

        result = MixResult(audio=mixed)
        if output_path:
            path = Path(output_path).expanduser().resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            format_ = path.suffix.lstrip(".") or "mp3"
            logger.info("Exporting final mix to %s", path)
            mixed.export(path.as_posix(), format=format_)
            result.output_path = path
        return result

    def _match_tempo(self, segment: AudioSegment, original_bpm: float, target_bpm: float) -> AudioSegment:
        if original_bpm <= 0 or target_bpm <= 0:
            return segment
        ratio = target_bpm / original_bpm
        if abs(ratio - 1.0) < 0.02:
            return segment
        logger.info("Time stretching track by ratio %.3f", ratio)
        if pyrb is not None:
            sample_width = segment.sample_width
            max_val = float(2 ** (8 * sample_width - 1))
            target_width = sample_width if sample_width in (2, 4) else 2
            target_max = float(2 ** (8 * target_width - 1))
            samples = np.array(segment.get_array_of_samples())
            if segment.channels > 1:
                samples = samples.reshape((-1, segment.channels)).T
            else:
                samples = samples.reshape((1, -1))
            normalized = samples.astype(np.float32) / max_val
            stretched = pyrb.time_stretch(normalized, segment.frame_rate, ratio)
            stretched = np.clip(stretched, -1.0, 1.0)
            dtype = np.int16 if target_width == 2 else np.int32
            scaled = (stretched * target_max).astype(dtype)
            if segment.channels > 1:
                scaled = scaled.T.reshape(-1)
            else:
                scaled = scaled.reshape(-1)
            raw_data = scaled.tobytes()
            new_segment = AudioSegment(
                raw_data,
                frame_rate=segment.frame_rate,
                sample_width=target_width,
                channels=segment.channels,
            )
            return new_segment
        # Fallback to simple resampling via pydub
        new_frame_rate = int(segment.frame_rate * ratio)
        stretched = segment._spawn(segment.raw_data, overrides={"frame_rate": new_frame_rate})
        return stretched.set_frame_rate(segment.frame_rate)


def export_mix(tracks: Iterable["Track"], output_path: str | Path, crossfade_seconds: float = 10.0) -> Path:
    engine = MixdownEngine(crossfade_seconds=crossfade_seconds)
    result = engine.render(tracks, output_path=output_path)
    if result.output_path is None:
        raise RuntimeError("Failed to export mix")
    return result.output_path
