from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QWidget, QTableWidget, QTableView, QTableWidgetItem, QVBoxLayout, QPushButton, QColorDialog, QTreeWidget, QTreeWidgetItem
# from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize

# Taken from https://www.hardcoded.net/articles/how-to-customize-qtableview-editing-behavior
# Currently unused
class EditCapableTableView(QTableView):
    def _firstEditableIndex(self, originalIndex, columnIndexes=None):
        """Returns the first editable index in `originalIndex`'s row or None.

        If `columnIndexes` is not None, the scan for an editable index will be
        limited to these columns.
        """
        model = self.model()
        h = self.horizontalHeader()
        editedRow = originalIndex.row()
        if columnIndexes is None:
            # We use logicalIndex() because it's possible the columns have been
            # re-ordered.
            columnIndexes = [h.logicalIndex(i) for i in range(h.count())]
        create = lambda col: model.createIndex(editedRow, col, None)
        scannedIndexes = [create(i) for i in columnIndexes if not h.isSectionHidden(i)]
        isEditable = lambda index: model.flags(index) &amp; Qt.ItemIsEditable
        editableIndexes = filter(isEditable, scannedIndexes)
        return editableIndexes[0] if editableIndexes else None

    def _previousEditableIndex(self, originalIndex):
        """Returns the first editable index at the left of `originalIndex` or None.
        """
        h = self.horizontalHeader()
        myCol = originalIndex.column()
        columnIndexes = [h.logicalIndex(i) for i in range(h.count())]
        # keep only columns before myCol
        columnIndexes = columnIndexes[:columnIndexes.index(myCol)]
        # We want the previous item, the columns have to be in reverse order
        columnIndexes = reversed(columnIndexes)
        return self._firstEditableIndex(originalIndex, columnIndexes)

    def _nextEditableIndex(self, originalIndex):
        """Returns the first editable index at the right of `originalIndex` or None.
        """
        h = self.horizontalHeader()
        myCol = originalIndex.column()
        columnIndexes = [h.logicalIndex(i) for i in range(h.count())]
        # keep only columns after myCol
        columnIndexes = columnIndexes[columnIndexes.index(myCol)+1:]
        return self._firstEditableIndex(originalIndex, columnIndexes)

    def closeEditor(self, editor, hint):
        # The problem we're trying to solve here is the edit-and-go-away problem. 
        # When ending the editing with submit or return, there's no problem, the
        # model's submit()/revert() is correctly called. However, when ending
        # editing by clicking away, submit() is never called. Fortunately,
        # closeEditor is called and, AFAIK, it's the only case where it's called
        # with NoHint (0). So, in these cases, we want to call model.submit()
        if hint == QAbstractItemDelegate.NoHint:
            QTableView.closeEditor(self, editor,
                QAbstractItemDelegate.SubmitModelCache)

        # And here, what we're trying to solve is the problem with editing
        # next/previous lines. If there are no more editable indexes, stop
        # editing right there. Additionally, we are making tabbing step over
        # non-editable cells
        elif hint in (QAbstractItemDelegate.EditNextItem,
                      QAbstractItemDelegate.EditPreviousItem):
            if hint == QAbstractItemDelegate.EditNextItem:
                editableIndex = self._nextEditableIndex(self.currentIndex())
            else:
                editableIndex = self._previousEditableIndex(self.currentIndex())
            if editableIndex is None:
                QTableView.closeEditor(self, editor,
                    QAbstractItemDelegate.SubmitModelCache)
            else:
                QTableView.closeEditor(self, editor, 0)
                self.setCurrentIndex(editableIndex)
                self.edit(editableIndex)
        else:
            QTableView.closeEditor(self, editor, hint)

    def keyPressEvent(self, event):
        if (event.key() == Qt.Key_Return) and \
            (self.state() != QAbstractItemView.EditingState):
            selectedRows = self.selectionModel().selectedRows()
            if selectedRows:
                selectedIndex = selectedRows[0]
                editableIndex = self._firstEditableIndex(selectedIndex)
                self.setCurrentIndex(editableIndex)
                self.edit(editableIndex)
        else:
            QTableView.keyPressEvent(self, event)