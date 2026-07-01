"""Entry point for the ICOtest graphical user interface"""

import sys


from PySide6.QtWidgets import QApplication  # pylint: disable=no-name-in-module


def main():
    """Start the ICOtest Production Assistant GUI"""

    # pylint: disable=import-outside-toplevel

    # Imports inside main to avoid Qt loading if someone just imports cli
    # module
    from icotest.gui.main_window import MainWindow

    # pylint: enable=import-outside-toplevel

    app = QApplication(sys.argv)
    app.setApplicationName("ICOtest Production Assistant")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
