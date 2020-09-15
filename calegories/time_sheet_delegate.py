from PySide2.QtWidgets import QLineEdit, QItemDelegate
from PySide2.QtGui import QDoubleValidator


class TimeSheetDelegate(QItemDelegate):
    """ Delegate for QTableWidget """

    def __init__(self):
        super(TimeSheetDelegate, self).__init__()

    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(QDoubleValidator(bottom=0.0))
        return editor
