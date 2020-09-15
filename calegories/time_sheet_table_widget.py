import sys
from PySide2.QtWidgets import QApplication, QTableWidget, QMenu
from PySide2.QtGui import QKeySequence
from PySide2.QtCore import Qt
from time_sheet_delegate import TimeSheetDelegate


class TimeSheetTableWidget(QTableWidget):

    def __init__(self, parent=None):
        super(TimeSheetTableWidget, self).__init__(parent)
        self.setItemDelegate(TimeSheetDelegate())
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu_requested)

    def context_menu_requested(self, position):
        menu = QMenu()
        copyAction = menu.addAction("Copy")
        action = menu.exec_(self.mapToGlobal(position))

        if action == copyAction:
            self.copy()

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Copy):
            self.copy()
        else:
            QTableWidget.keyPressEvent(self, event)

    def copy(self):
        ranges = self.selectedRanges()
        if len(ranges) < 1:
            # No row selected
            return
        text = ''
        for rng in ranges:
            r_top = rng.topRow()
            r_btm = rng.bottomRow()
            r_lft = rng.leftColumn()
            r_rgt = rng.rightColumn()
            for row in range(r_top, r_btm + 1):
                for col in range(r_lft, r_rgt + 1):
                    item = self.item(row, col)
                    if item:
                        text += item.text()
                        if col != r_rgt:
                            text += '\t'
                text += '\n'
        QApplication.clipboard().setText(text)
