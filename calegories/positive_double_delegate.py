from PySide2 import QtWidgets, QtGui, QtCore


class PositiveDoubleDelegate(QtWidgets.QItemDelegate):
    """ Delegate for QTableView """

    def __init__(self):
        super(PositiveDoubleDelegate, self).__init__()

    def createEditor(self, parent, option, index):
        editor = QtWidgets.QLineEdit(parent)
        editor.setValidator(QtGui.QDoubleValidator(bottom=0.0))
        return editor

    def setModelData(self, editor, model, index):
        text = editor.text()
        model.setData(index, text, role=QtCore.Qt.EditRole)
