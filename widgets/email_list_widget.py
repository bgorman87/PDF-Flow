from PySide6.QtCore import Qt, QMimeData
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QAbstractItemView
from PySide6.QtGui import QDrag


class EmailListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mouse_pressed = False
        self.mouse_moved = False
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setProperty("class", "email-list")
        self.setDragDropMode(QListWidget.InternalMove)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
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
                drag = QDrag(self)
                mimeData = QMimeData()
                mimeData.setText(self.currentItem().text())
                drag.setMimeData(mimeData)
                drag.exec(Qt.MoveAction)

    def mouseReleaseEvent(self, event):
        # Only edit item if mouse was clicked and not click dragged
        if self.mouse_pressed and not self.mouse_moved:
            if event.button() == Qt.LeftButton:
                item = self.itemAt(event.pos())
                if item is None:

                    # If list is empty just add blank item without checking last item
                    # Do this before checking last items text as well since it'll throw error otherwise
                    if self.count() == 0:
                        new_item = QListWidgetItem()
                        new_item.setFlags(new_item.flags() | Qt.ItemIsEditable)
                        self.addItem(new_item)

                    # If last item already blank, dont add another
                    elif self.item(self.count() - 1).text() == "":
                        return

                    # If last item isnt blank and count greater than zero add a blank item
                    else:
                        new_item = QListWidgetItem()
                        new_item.setFlags(new_item.flags() | Qt.ItemIsEditable)
                        self.addItem(new_item)
                else:
                    # Start editing item
                    self.editItem(item)
        self.mouse_pressed = False
        self.mouse_moved = False

    def dropEvent(self, event):
        if event.source() == self:
            event.setDropAction(Qt.MoveAction)
            super().dropEvent(event)
