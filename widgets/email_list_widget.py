from PySide6 import QtCore, QtGui, QtWidgets


class EmailListWidget(QtWidgets.QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mouse_pressed = False
        self.mouse_moved = False
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setProperty("class", "email-list")
        self.setDragDropMode(QtWidgets.QListWidget.InternalMove)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.mouse_pressed = True

    def mouseMoveEvent(self, event):
        # If click dragging, use to reorder the list items
        if self.mouse_pressed:
            self.mouse_moved = True
            # Get the index of the item being dragged
            index = self.indexAt(event.pos())
            if index.isValid():
                # Begin the drag operation
                self.setCurrentIndex(index)
                drag = QtGui.QDrag(self)
                mimeData = QtCore.QMimeData()
                mimeData.setText(self.currentItem().text())
                drag.setMimeData(mimeData)
                drag.exec(QtCore.Qt.MoveAction)

    def mouseReleaseEvent(self, event):
        # Only edit item if mouse was clicked and not click dragged
        if self.mouse_pressed and not self.mouse_moved:
            if event.button() == QtCore.Qt.LeftButton:
                item = self.itemAt(event.pos())
                if item is None:

                    # If list is empty just add blank item without checking last item
                    # Do this before checking last items text as well since it'll throw error otherwise
                    self.add_new_email()
                else:
                    # Start editing item
                    self.editItem(item)
        self.mouse_pressed = False
        self.mouse_moved = False

    def dropEvent(self, event):
        if event.source() == self:
            event.setDropAction(QtCore.Qt.MoveAction)
            super().dropEvent(event)

    def add_new_email(self):
        # If last item already blank, dont add another
        if self.count() > 0 and self.item(self.count() - 1).text() == "":
            item = self.item(self.count() - 1)
        else:
            new_item = QtWidgets.QListWidgetItem()
            new_item.setFlags(new_item.flags() | QtCore.Qt.ItemIsEditable)
            self.addItem(new_item)
            item = new_item
        
        self.editItem(item)

    def set_items(self, emails):
        self.clear()
        for email in emails:
            new_item = QtWidgets.QListWidgetItem(email)
            new_item.setFlags(new_item.flags() | QtCore.Qt.ItemIsEditable)
            self.addItem(new_item)
