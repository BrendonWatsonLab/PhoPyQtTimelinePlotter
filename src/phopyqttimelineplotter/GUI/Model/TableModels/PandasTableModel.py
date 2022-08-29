import sys
import pandas as pd
from PyQt5.QtWidgets import QApplication, QTableView
from PyQt5.QtCore import QAbstractTableModel, Qt

# PandasTableModel.py

## INCLUDES:
# from GUI.Model.TableModels.PandasTableModel import PandasTableModel


""" PandasTableModel: https://learndataanalysis.org/display-pandas-dataframe-with-pyqt5-qtableview-widget/
    A QAbstractTableModel that displays a Pandas dataframe
"""
class PandasTableModel(QAbstractTableModel):

    def __init__(self, data, model_display_name):
        QAbstractTableModel.__init__(self)
        self._data = data
        self._model_display_name = model_display_name

    def get_model_display_name(self):
        return self._model_display_name

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parnet=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[col]
        return None



"""
df = pd.DataFrame({'a': ['Mary', 'Jim', 'John'],
                   'b': [100, 200, 300],
                   'c': ['a', 'b', 'c']})

model = pandasModel(df)
view = QTableView()
view.setModel(model)
view.resize(800, 600)
view.show()

"""