import sys
import pandas as pd
from PySide2 import QtCore


class TimeSheetTableModel(QtCore.QAbstractTableModel):

    def __init__(self, df=pd.DataFrame(), parent=None):
        super().__init__(parent)
        self._df = df

    def rowCount(self, parent=None):
        return self._df.shape[0]

    def columnCount(self, parent=None):
        return self._df.shape[1]

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                return str(self._df.iloc[index.row(), index.column()])
        return None

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self._df.columns[col]
        return None

    def flags(self, index):
        if (index.column() == 0):
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        elif (index.column() == (self.columnCount() - 1)):
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        elif (index.row() == (self.rowCount() - 1)):
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        else:
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        if role != QtCore.Qt.EditRole:
            return False
        row = index.row()
        if row < 0 or row >= len(self._df.values):
            return False
        column = index.column()
        if column < 0 or column >= self._df.columns.size:
            return False
        self._df.at[row, self._df.columns[column]] = value
        # self.dataChanged.emit(index, index)
        self.dataChanged.emit(index, index)
        return True
