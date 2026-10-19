"""A minimal PySide6 file-drop starter window."""

import sys
from pathlib import Path
import main

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class FileDropArea(QFrame):
    """A simple drop target that accepts one or more local files."""

    files_dropped = Signal(list)

    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        self.setObjectName("dropArea")
        self.setMinimumHeight(220)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title = QLabel("Drop files here")
        self.title.setObjectName("dropTitle")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint = QLabel("or drag files from your file browser")
        self.hint.setObjectName("dropHint")
        self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title)
        layout.addWidget(self.hint)

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setProperty("active", True)
            self.style().unpolish(self)
            self.style().polish(self)

    def dragLeaveEvent(self, event) -> None:
        self.setProperty("active", False)
        self.style().unpolish(self)
        self.style().polish(self)
        event.accept()

    def dropEvent(self, event) -> None:
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()]
        self.setProperty("active", False)
        self.style().unpolish(self)
        self.style().polish(self)
        if paths:
            self.files_dropped.emit(paths)
            event.acceptProposedAction()

    def show_files(self, files: list[Path]) -> None:
        count = len(files)
        self.title.setText(f"{count} file{'s' if count != 1 else ''} ready")
        names = ", ".join(file.name for file in files[:3])
        if count > 3:
            names += ", …"
        self.hint.setText(names)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("File Starter")
        self.setMinimumSize(460, 360)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(18)

        self.drop_area = FileDropArea()
        self.drop_area.files_dropped.connect(self.on_files_dropped)
        self.start_button = QPushButton("Start")
        self.start_button.setObjectName("startButton")
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self.start)

        layout.addWidget(self.drop_area)
        layout.addWidget(self.start_button)
        self.setCentralWidget(container)
        self.files: list[Path] = []

    def on_files_dropped(self, files: list[Path]) -> None:
        self.files = files
        self.drop_area.show_files(files)
        self.start_button.setEnabled(True)

    def start(self) -> None:
        # Add your file-processing work here.
        self.start_button.setText("Started")
        self.start_button.setEnabled(False)


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QMainWindow { background: #f7f8fa; }
        #dropArea {
            background: white;
            border: 2px dashed #a8b2c1;
            border-radius: 14px;
        }
        #dropArea[active="true"] { border-color: #2563eb; background: #eff6ff; }
        #dropTitle { color: #1f2937; font-size: 19px; font-weight: 600; }
        #dropHint { color: #6b7280; font-size: 13px; }
        #startButton {
            background: #2563eb; color: white; border: none; border-radius: 8px;
            font-size: 15px; font-weight: 600; min-height: 42px;
        }
        #startButton:hover { background: #1d4ed8; }
        #startButton:disabled { background: #cbd5e1; color: #64748b; }
    """)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
