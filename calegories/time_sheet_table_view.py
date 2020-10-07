import sys
from PySide2 import QtWidgets, QtGui, QtCore
from positive_double_delegate import PositiveDoubleDelegate


class TimeSheetTableView(QtWidgets.QTableView):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu_requested)
        self._delegates = {
            'PositiveDoubleDelegate': PositiveDoubleDelegate(),
        }

    def context_menu_requested(self, position):
        menu = QtWidgets.QMenu()
        copyAction = menu.addAction("Copy")
        action = menu.exec_(self.mapToGlobal(position))

        if action == copyAction:
            self.copy()

    def keyPressEvent(self, event):
        if event.matches(QtGui.QKeySequence.Copy):
            self.copy()
        else:
            QtWidgets.QTableView.keyPressEvent(self, event)

    def copy(self):
        indices = self.selectionModel().selectedIndexes()
        if len(indices) < 1:
            # Nothing selected
            return

        text = ''
        r_top = indices[0].row()
        r_btm = indices[-1].row()
        r_lft = indices[0].column()
        r_rgt = indices[-1].column()
        for row in range(r_top, r_btm + 1):
            for col in range(r_lft, r_rgt + 1):
                index = self.model().index(row, col)
                item = self.model().data(index)
                if item:
                    text += item
                    if col != r_rgt:
                        text += '\t'
            text += '\n'
        QtWidgets.QApplication.clipboard().setText(text)
