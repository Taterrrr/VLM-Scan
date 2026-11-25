"""A small PySide6 file-drop launcher."""

import shutil
import sys
import traceback
from pathlib import Path

import main

from PySide6.QtCore import QElapsedTimer, QThread, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


PROJECT_ROOT = Path(__file__).resolve().parent
DESTINATION_FOLDER = PROJECT_ROOT / "processing" / "pre_bucket"


class FileDropArea(QFrame):
    files_ready = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            "FileDropArea { border: 2px dashed #6a8caf; border-radius: 10px; "
            "background: #f4f8fc; }"
        )

        self.idle_text = "Drop one or more files here"
        self.label = QLabel(self.idle_text)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            self.label.setText("Release to add these files")
            event.acceptProposedAction()

    def dragLeaveEvent(self, event) -> None:
        self.label.setText(self.idle_text)
        event.accept()

    def dropEvent(self, event) -> None:
        urls = [url for url in event.mimeData().urls() if url.isLocalFile()]
        event.acceptProposedAction()

        if not urls:
            return

        moved_files = []
        errors = []

        try:
            DESTINATION_FOLDER.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            self.label.setText(f"Could not create {DESTINATION_FOLDER}: {error}")
            return

        for url in urls:
            source = Path(url.toLocalFile())

            try:
                if not source.is_file():
                    errors.append(f"Skipped invalid item: {source.name}")
                    continue

                destination = DESTINATION_FOLDER / source.name
                if destination.exists():
                    destination = self._available_name(destination)

                moved_files.append(Path(shutil.move(str(source), str(destination))))
            except OSError as error:
                errors.append(f"Could not move {source.name}: {error}")

        if moved_files:
            self.label.setText(f"Ready: {len(moved_files)} file(s) queued")
            self.files_ready.emit(moved_files)

        if errors:
            prefix = f"{len(moved_files)} queued - " if moved_files else ""
            self.label.setText(prefix + errors[0])

    @staticmethod
    def _available_name(path: Path) -> Path:
        """Avoid overwriting an existing destination file."""
        index = 1

        while True:
            candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
            if not candidate.exists():
                return candidate
            index += 1


class FileProcessingThread(QThread):
    file_started = Signal(object)
    processing_finished = Signal(int, list)

    def __init__(self, file_paths: list[Path]) -> None:
        super().__init__()
        self.file_paths = file_paths

    def run(self) -> None:
        errors = []
        completed = 0

        for file_path in self.file_paths:
            self.file_started.emit(file_path)

            try:
                image_list = main.pdf_to_images(file_path)
                for path in image_list:
                    main.main(path) 
                completed += 1
            except Exception:
                errors.append(
                    f"Error occurred during processing: {file_path.name}\n\n"
                    f"{traceback.format_exc()}"
                )

        self.processing_finished.emit(completed, errors)


class FileRunnerWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.file_paths = []
        self.processing_thread = None
        self.current_file_name = ""

        self.elapsed_timer = QElapsedTimer()
        self.display_timer = QTimer(self)
        self.display_timer.setInterval(100)
        self.display_timer.timeout.connect(self.update_processing_status)

        self.setWindowTitle("File Runner")
        self.resize(600, 400)

        self.drop_area = FileDropArea()
        self.drop_area.files_ready.connect(self.add_file_paths)

        self.file_list = QListWidget()

        self.empty_list_label = QLabel("Dropped files will appear here")
        self.empty_list_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_list_label.setStyleSheet("color: #777; padding: 8px;")

        self.processing_label = QLabel()
        self.processing_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.processing_label.setStyleSheet(
            "color: #1f5d91; font-weight: bold; padding: 6px;"
        )
        self.processing_label.hide()

        self.start_button = QPushButton("Start")
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_program)

        layout = QVBoxLayout(self)
        layout.addWidget(self.drop_area, 1)
        layout.addWidget(self.empty_list_label)
        layout.addWidget(self.file_list)
        layout.addWidget(self.processing_label)
        layout.addWidget(self.start_button)

    def add_file_paths(self, file_paths: list[Path]) -> None:
        self.file_paths.extend(file_paths)

        for file_path in file_paths:
            self.file_list.addItem(str(file_path))

        self.empty_list_label.hide()
        self.start_button.setEnabled(True)

    def start_program(self) -> None:
        if not self.file_paths or self.processing_thread is not None:
            return

        self.start_button.setEnabled(False)
        self.drop_area.setEnabled(False)

        self.processing_thread = FileProcessingThread(self.file_paths.copy())
        self.processing_thread.file_started.connect(self.begin_file_processing)
        self.processing_thread.processing_finished.connect(self.finish_processing)
        self.processing_thread.finished.connect(self.processing_thread.deleteLater)
        self.processing_thread.start()

    def begin_file_processing(self, file_path: Path) -> None:
        self.current_file_name = file_path.name
        self.elapsed_timer.start()
        self.processing_label.show()
        self.update_processing_status()
        self.display_timer.start()

    def update_processing_status(self) -> None:
        if not self.elapsed_timer.isValid():
            return

        elapsed_seconds = self.elapsed_timer.elapsed() // 1000
        minutes, seconds = divmod(elapsed_seconds, 60)

        self.processing_label.setText(
            f"Processing: {self.current_file_name} — {minutes:02}:{seconds:02}"
        )

    def finish_processing(self, completed: int, errors: list[str]) -> None:
        self.display_timer.stop()
        self.processing_label.setText(f"Finished processing {completed} file(s).")

        self.drop_area.setEnabled(True)
        self.start_button.setEnabled(bool(self.file_paths))
        self.processing_thread = None

        if errors:
            error_dialog = QMessageBox(self)
            error_dialog.setIcon(QMessageBox.Icon.Critical)
            error_dialog.setWindowTitle("Some files failed")
            error_dialog.setText(
                f"{len(errors)} file(s) failed during processing."
            )
            error_dialog.setDetailedText("\n\n".join(errors))
            error_dialog.exec()
        else:
            QMessageBox.information(
                self,
                "Finished",
                f"Finished processing {completed} file(s).",
            )


def launch_file_runner() -> int:
    app = QApplication(sys.argv)
    window = FileRunnerWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(launch_file_runner())