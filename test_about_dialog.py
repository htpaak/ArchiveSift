"""
AboutDialog 테스트 스크립트

이 스크립트는 AboutDialog를 독립적으로 테스트하기 위한 것입니다.
"""
import sys
from PyQt5.QtWidgets import QApplication
from ui.dialogs.about_dialog import AboutDialog

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = AboutDialog()
    dialog.exec_() 