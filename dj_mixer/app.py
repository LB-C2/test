from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

from PyQt5 import QtCore, QtWidgets

from .bpm import BPMAnalyzer
from .mixdown import MixdownEngine
from .playback import PreviewPlayer
from .track import Track

logger = logging.getLogger(__name__)


class BPMWorker(QtCore.QThread):
    bpmReady = QtCore.pyqtSignal(str, float)
    failed = QtCore.pyqtSignal(str, str)

    def __init__(self, analyzer: BPMAnalyzer, track: Track) -> None:
        super().__init__()
        self.analyzer = analyzer
        self.track = track

    def run(self) -> None:  # pragma: no cover - requires GUI runtime
        try:
            result = self.analyzer.detect(self.track.path)
        except Exception as exc:  # pragma: no cover
            logger.exception("BPM detection failed for %s", self.track.path)
            self.failed.emit(str(self.track.path), str(exc))
            return
        self.bpmReady.emit(str(result.path), float(result.bpm))


class MixWorker(QtCore.QThread):
    finishedMix = QtCore.pyqtSignal(object)
    failed = QtCore.pyqtSignal(str)

    def __init__(self, engine: MixdownEngine, tracks: List[Track], output_path: Optional[str]) -> None:
        super().__init__()
        self.engine = engine
        self.tracks = tracks
        self.output_path = output_path

    def run(self) -> None:  # pragma: no cover - requires GUI runtime
        try:
            result = self.engine.render(self.tracks, self.output_path)
        except Exception as exc:  # pragma: no cover
            logger.exception("Failed to render mix")
            self.failed.emit(str(exc))
            return
        self.finishedMix.emit(result)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Local DJ Mixer")
        self.resize(900, 600)

        self.tracks: List[Track] = []
        self.bpm_analyzer: Optional[BPMAnalyzer] = None
        self.preview_player: Optional[PreviewPlayer] = None
        self._bpm_workers: List[BPMWorker] = []
        self._mix_worker: Optional[MixWorker] = None

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Title", "BPM", "Duration", "Path"])
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        for i in range(1, 4):
            self.table.horizontalHeader().setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        add_button = QtWidgets.QPushButton("Add Tracks")
        remove_button = QtWidgets.QPushButton("Remove Selected")
        preview_button = QtWidgets.QPushButton("Preview")
        stop_preview_button = QtWidgets.QPushButton("Stop Preview")

        crossfade_label = QtWidgets.QLabel("Crossfade (seconds):")
        self.crossfade_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.crossfade_slider.setMinimum(1)
        self.crossfade_slider.setMaximum(30)
        self.crossfade_slider.setValue(10)
        self.crossfade_value = QtWidgets.QLabel("10")

        self.mix_button = QtWidgets.QPushButton("Render Mix")

        layout = QtWidgets.QVBoxLayout(central)
        layout.addWidget(self.table)

        controls_layout = QtWidgets.QHBoxLayout()
        controls_layout.addWidget(add_button)
        controls_layout.addWidget(remove_button)
        controls_layout.addWidget(preview_button)
        controls_layout.addWidget(stop_preview_button)
        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        crossfade_layout = QtWidgets.QHBoxLayout()
        crossfade_layout.addWidget(crossfade_label)
        crossfade_layout.addWidget(self.crossfade_slider)
        crossfade_layout.addWidget(self.crossfade_value)
        layout.addLayout(crossfade_layout)

        layout.addWidget(self.mix_button)

        add_button.clicked.connect(self.add_tracks)
        remove_button.clicked.connect(self.remove_selected_tracks)
        preview_button.clicked.connect(self.preview_selected_track)
        stop_preview_button.clicked.connect(self.stop_preview)
        self.crossfade_slider.valueChanged.connect(self.update_crossfade_label)
        self.mix_button.clicked.connect(self.render_mix)

    def ensure_dependencies(self) -> None:
        if self.bpm_analyzer is None:
            self.bpm_analyzer = BPMAnalyzer()
        if self.preview_player is None:
            self.preview_player = PreviewPlayer()

    def add_tracks(self) -> None:
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self,
            "Select audio files",
            str(Path.home()),
            "Audio Files (*.mp3 *.wav *.flac *.ogg *.m4a)"
        )
        if not files:
            return
        self.ensure_dependencies()
        for file in files:
            try:
                track = Track.from_file(file)
            except Exception as exc:
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to load {file}: {exc}")
                continue
            self.tracks.append(track)
            self._append_track_to_table(track)
            self._run_bpm_detection(track)

    def remove_selected_tracks(self) -> None:
        selected_rows = sorted({index.row() for index in self.table.selectedIndexes()}, reverse=True)
        for row in selected_rows:
            self.table.removeRow(row)
            del self.tracks[row]

    def _append_track_to_table(self, track: Track) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(track.title))
        bpm_item = QtWidgets.QTableWidgetItem("…")
        bpm_item.setTextAlignment(QtCore.Qt.AlignCenter)
        self.table.setItem(row, 1, bpm_item)
        self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(track.formatted_duration()))
        path_item = QtWidgets.QTableWidgetItem(str(track.path))
        path_item.setToolTip(str(track.path))
        self.table.setItem(row, 3, path_item)

    def _run_bpm_detection(self, track: Track) -> None:
        if self.bpm_analyzer is None:
            return
        worker = BPMWorker(self.bpm_analyzer, track)
        worker.bpmReady.connect(self._handle_bpm_ready)
        worker.failed.connect(self._handle_bpm_failed)
        worker.start()
        self._bpm_workers.append(worker)

    @QtCore.pyqtSlot(str, float)
    def _handle_bpm_ready(self, path: str, bpm: float) -> None:  # pragma: no cover - GUI slot
        for index, track in enumerate(self.tracks):
            if str(track.path) == path:
                track.set_bpm(bpm)
                item = self.table.item(index, 1)
                if item:
                    item.setText(f"{bpm:.2f}")
                break

    @QtCore.pyqtSlot(str, str)
    def _handle_bpm_failed(self, path: str, error: str) -> None:  # pragma: no cover - GUI slot
        QtWidgets.QMessageBox.warning(
            self,
            "BPM Detection Failed",
            f"Could not analyze BPM for {path}: {error}"
        )

    def preview_selected_track(self) -> None:
        if self.preview_player is None:
            try:
                self.preview_player = PreviewPlayer()
            except Exception as exc:
                QtWidgets.QMessageBox.critical(self, "Preview unavailable", str(exc))
                return
        rows = {index.row() for index in self.table.selectedIndexes()}
        if not rows:
            QtWidgets.QMessageBox.information(self, "Select a track", "Choose a track to preview")
            return
        row = rows.pop()
        track = self.tracks[row]
        if track.audio is None:
            QtWidgets.QMessageBox.warning(self, "No audio", "Track audio has not been loaded")
            return
        self.preview_player.play(track.audio)

    def stop_preview(self) -> None:
        if self.preview_player:
            self.preview_player.stop()

    def update_crossfade_label(self, value: int) -> None:
        self.crossfade_value.setText(str(value))

    def render_mix(self) -> None:
        if not self.tracks:
            QtWidgets.QMessageBox.information(self, "No tracks", "Add tracks before mixing")
            return
        output_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export Mix",
            str(Path.home() / "mix.mp3"),
            "Audio Files (*.mp3 *.wav)"
        )
        if not output_path:
            return
        engine = MixdownEngine(
            crossfade_seconds=float(self.crossfade_slider.value()),
            tempo_matching=True,
        )
        self._mix_worker = MixWorker(engine, list(self.tracks), output_path)
        self._mix_worker.finishedMix.connect(self._handle_mix_ready)
        self._mix_worker.failed.connect(self._handle_mix_failed)
        self._mix_worker.start()
        self.mix_button.setEnabled(False)
        self.mix_button.setText("Mixing…")

    @QtCore.pyqtSlot(object)
    def _handle_mix_ready(self, result) -> None:  # pragma: no cover - GUI slot
        self.mix_button.setEnabled(True)
        self.mix_button.setText("Render Mix")
        if result.output_path:
            QtWidgets.QMessageBox.information(
                self,
                "Mix ready",
                f"Mix exported to {result.output_path}"
            )

    @QtCore.pyqtSlot(str)
    def _handle_mix_failed(self, error: str) -> None:  # pragma: no cover - GUI slot
        self.mix_button.setEnabled(True)
        self.mix_button.setText("Render Mix")
        QtWidgets.QMessageBox.critical(self, "Mix failed", error)


def run() -> None:
    import sys

    logging.basicConfig(level=logging.INFO)
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
