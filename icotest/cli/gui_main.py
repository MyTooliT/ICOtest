"""Entry point for the ICOtest graphical user interface"""

import sys
from PySide6.QtWidgets import QApplication


def main():
    """Start the ICOtest Production Assistant GUI"""

    # Imports inside main to avoid Qt loading if someone just imports cli
    # module
    from icotest.gui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("ICOtest Production Assistant")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
