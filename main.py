import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

from utils.styles import APP_STYLE
from ui.launcher_window import LauncherWindow

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLE)
    
    icon_path = Path(__file__).resolve().parent / "icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
        
    win = LauncherWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
