
from projexui.widgets.xtoolbutton import XToolButton
from projexui import resources
from xqt import QtCore, QtGui

class XOverlayWidget(QtGui.QWidget):
    finished = QtCore.Signal(int)

    def __init__(self, parent=None):
        super(XOverlayWidget, self).__init__(parent)

        # define custom properties
        self._centralWidget = None
        self._result = None
        self._closable = True
        self._closeButton = XToolButton(self)
        self._closeButton.setShadowed(True)
        self._closeButton.setIcon(QtGui.QIcon(resources.find('img/overlay/close.png')))
        self._closeButton.setIconSize(QtCore.QSize(24, 24))
        self._closeButton.setToolTip('Close')

        # create the coloring for the overlay
        palette = self.palette()
        clr = QtGui.QColor('black')
        clr.setAlpha(140)
        palette.setColor(palette.Window, clr)
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # listen to the parents event filter
        parent.installEventFilter(self)

        # initialize the widget
        self.hide()
        self.move(0, 0)
        self.resize(parent.size())
        self._closeButton.clicked.connect(self.reject)

    def accept(self):
        """
        Accepts this overlay and exits the modal window.
        """
        self.close()
        self.setResult(1)
        self.finished.emit(1)

    def adjustSize(self, size):
        """
        Adjusts the size of this widget as the parent resizes.
        """
        self.move(0, 0)
        self.resize(size)

    def centralWidget(self):
        """
        Returns the central widget for this overlay.  If there is one, then it will
        be automatically moved with this object.

        :return     <QtGui.QWidget>
        """
        return self._centralWidget

    def isClosable(self):
        """
        Returns whether or not the user should be able to close this overlay widget.

        :return     <bool>
        """
        return self._closable

    def keyPressEvent(self, event):
        """
        Exits the modal window on an escape press.

        :param      event | <QtCore.QKeyPressEvent>
        """
        if event.key() == QtCore.Qt.Key_Escape:
            self.reject()

        super(XOverlayWidget, self).keyPressEvent(event)

    def eventFilter(self, object, event):
        """
        Resizes this overlay as the widget resizes.

        :param      object | <QtCore.QObject>
                    event  | <QtCore.QEvent>

        :return     <bool>
        """
        if object == self.parent() and event.type() == QtCore.QEvent.Resize:
            self.adjustSize(event.size())
        elif event.type() == QtCore.QEvent.Close:
            self.setResult(0)
        return False

    def reject(self):
        """
        Rejects this overlay and exits the modal window.
        """
        self.close()
        self.setResult(1)
        self.finished.emit(1)

    def result(self):
        """
        Returns the result from this overlay widget.

        :return     <int>
        """
        return int(self._result)

    def resizeEvent(self, event):
        """
        Handles a resize event for this overlay, centering the central widget if
        one is found.

        :param      event | <QtCore.QEvent>
        """
        super(XOverlayWidget, self).resizeEvent(event)

        widget = self.centralWidget()
        if widget is not None:
            center = self.rect().center()
            widget.move(center.x() - widget.width() / 2, center.y() - widget.height() / 2)
            self._closeButton.move(self.width() - 38, 6)

    def setCentralWidget(self, widget):
        """
        Sets the central widget for this overlay to the inputed widget.

        :param      widget | <QtGui.QWidget>
        """
        self._centralWidget = widget

        if widget is not None:
            widget.setParent(self)

            widget.installEventFilter(self)

            # create the drop shadow effect
            effect = QtGui.QGraphicsDropShadowEffect(self)
            effect.setColor(QtGui.QColor('black'))
            effect.setBlurRadius(80)
            effect.setOffset(0, 0)
            widget.setGraphicsEffect(effect)

    def setClosable(self, state):
        """
        Sets whether or not the user should be able to close this overlay widget.

        :param      state | <bool>
        """
        self._closable = state

    def setResult(self, result):
        """
        Sets the result for this overlay to the inputed value.

        :param      result | <int>
        """
        self._result = result

    def setVisible(self, state):
        """
        Closes this widget and kills the result.
        """
        super(XOverlayWidget, self).setVisible(state)

        if not state:
            self.setResult(0)

    def showEvent(self, event):
        """
        Ensures this widget is the top-most widget for its parent.

        :param      event | <QtCore.QEvent>
        """
        super(XOverlayWidget, self).showEvent(event)

        # raise to the top
        self.raise_()
        self._closeButton.setVisible(self.isClosable())

        widget = self.centralWidget()
        if widget:
            center = self.rect().center()
            start_x = end_x = center.x() - widget.width() / 2
            start_y = -widget.height()
            end_y = center.y() - widget.height() / 2

            start = QtCore.QPoint(start_x, start_y)
            end = QtCore.QPoint(end_x,  end_y)

            # create the movement animation
            anim = QtCore.QPropertyAnimation(self)
            anim.setPropertyName('pos')
            anim.setTargetObject(widget)
            anim.setStartValue(start)
            anim.setEndValue(end)
            anim.setDuration(500)
            anim.setEasingCurve(QtCore.QEasingCurve.InOutQuad)
            anim.finished.connect(anim.deleteLater)
            anim.start()

    @staticmethod
    def modal(widget, parent=None):
        """
        Creates a modal dialog for this overlay with the inputed widget.  If the user
        accepts the widget, then 1 will be returned, otherwise, 0 will be returned.

        :param      widget | <QtCore.QWidget>
        """
        if parent is None:
            parent = QtGui.QApplication.instance().activeWindow()

        overlay = XOverlayWidget(parent)
        overlay.setCentralWidget(widget)
        overlay.show()
        return overlay

