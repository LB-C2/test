# Local DJ Mixer

A cross-platform desktop DJ mixing toolkit built with PyQt5. The app lets you
load downloaded tracks, automatically analyze their BPM, audition them, adjust
crossfade durations, and render the final mix to an audio file.

## Features

- **Track management** – Add or remove audio files via a table-based GUI.
- **Automatic BPM detection** – Uses `librosa` to analyze the tempo of each
  track.
- **Preview playback** – Audition individual tracks directly from the app via
  `simpleaudio`.
- **Crossfade control** – Adjustable transitions (1–30 seconds) between tracks.
- **Tempo-aware mixing** – Optional tempo matching using `pyrubberband` with a
  fallback resampling approach when the library is unavailable.
- **Export** – Render and export the mixed result to `.mp3` or `.wav` using
  `pydub`/`ffmpeg`.

## Getting Started

1. Create and activate a virtual environment.
2. Install system dependencies:
   - **FFmpeg** (required by `pydub` for decoding/encoding most formats).
   - **Rubber Band Library** (optional, enables high-quality time stretching via
     `pyrubberband`).
3. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Launch the application:

   ```bash
   python main.py
   ```

## Usage Tips

- Use the **Add Tracks** button to queue multiple audio files. BPM analysis
  runs automatically in the background.
- Select a track and click **Preview** to audition it. Use **Stop Preview** to
  halt playback.
- Drag the crossfade slider to configure how long transitions last between
  tracks.
- Click **Render Mix** to export a combined track. Choose `.mp3` or `.wav` in
  the save dialog.
- Tempo matching is applied automatically when BPM information is available for
  consecutive tracks.

## Troubleshooting

- If BPM detection fails, verify that `librosa` is installed and the audio file
  is readable.
- Preview playback requires `simpleaudio`. Install platform-specific
  dependencies as needed (e.g., `portaudio` on some Linux distributions).
- When `pyrubberband` is unavailable, the mixer falls back to basic resampling.
  Install the Rubber Band CLI for higher-fidelity stretching.

## Roadmap

Planned enhancements include waveform visualization, drag-and-drop support,
per-track cueing, and offline rendering progress feedback.
