
import projexui

from collections import OrderedDict
from projex.enum import enum
from xqt import QtCore, QtGui

from .xoverlaywidget import XOverlayWidget

class XOverlayWizardPage(QtGui.QWidget):
    completeChanged = QtCore.Signal()

    def __init__(self, parent=None):
        super(XOverlayWizardPage, self).__init__(parent)

        # define custom properties
        self._commitPage = False
        self._finalPage = False

        # create the title information
        font = self.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 2)

        # set the palette coloring
        pal = self.palette()
        pal.setColor(pal.WindowText, QtGui.QColor('white'))
        self.setPalette(pal)

        # create the title labels
        self._titleLabel = QtGui.QLabel('', self)
        self._titleLabel.setFont(font)
        self._titleLabel.setPalette(pal)
        self._subTitleLabel = QtGui.QLabel('', self)
        self._subTitleLabel.setPalette(pal)

        self.adjustMargins()

    def adjustMargins(self):
        """
        Adjusts the margins to incorporate enough room for the widget's title and sub-title.
        """
        y = 0
        height = 0
        if self._titleLabel.text():
            height += self._titleLabel.height() + 3
            y += height

        if self._subTitleLabel.text():
            self._subTitleLabel.move(0, y)
            height += self._subTitleLabel.height() + 3

        self.setContentsMargins(0, height, 0, 0)

    def cleanupPage(self):
        """
        Performs any cleanup operations that are necessary for this page.
        """
        pass

    def commit(self):
        """
        Commits any data for this wizard page.
        """
        pass

    def field(self, name):
        """
        Returns the field value for this page from its wizard.

        :param      name | <str>

        :return     <variant>
        """
        return self.wizard().field(name)

    def isCommitPage(self):
        """
        Returns whether or not this is a page that requires the commit button to be displayed.

        :return     <bool>
        """
        return self._commitPage

    def isComplete(self):
        """
        Returns whether or not this page has fully completed its operations.

        :return     <bool>
        """
        return False

    def isFinalPage(self):
        """
        Returns whether or not this is the final page within the wizard.

        :return     <bool>
        """
        return self._finalPage or self.nextId() == -1

    def initializePage(self):
        """
        Performs any initialization operations that are necessary for this page.
        """
        pass

    def nextId(self):
        """
        Returns the next id for this page.  By default, it will provide the next id from the wizard, but
        this method can be overloaded to create a custom path.  If -1 is returned, then it will be considered
        the final page.

        :return     <int>
        """
        wizard = self.wizard()
        curr_id = wizard.currentId()
        all_ids = wizard.pageIds()
        try:
            return all_ids[all_ids.index(curr_id)+1]
        except IndexError:
            return -1

    def setCommitPage(self, state):
        """
        Sets whether or not this is a commit page for the wizard.

        :param      state | <bool>
        """
        self._commitPage = state

    def setField(self, name, value):
        """
        Sets the field value for this page from its wizard.

        :param      name  | <str>
                    value | <variant>
        """
        return self.wizard().setField(name, value)

    def setFinalPage(self, state):
        """
        Sets whether or not this is a final page for the wizard.

        :param      state | <bool>
        """
        self._finalPage = state

    def setSubTitle(self, title):
        """
        Sets the sub-title for this page to the inputed title.

        :param      title | <str>
        """
        self._subTitleLabel.setText(title)
        self._subTitleLabel.adjustSize()
        self.adjustMargins()

    def setTitle(self, title):
        """
        Sets the title for this page to the inputed title.

        :param      title | <str>
        """
        self._titleLabel.setText(title)
        self._titleLabel.adjustSize()
        self.adjustMargins()

    def subTitle(self):
        """
        Returns the sub-title for this page.

        :return     <str>
        """
        return self._subTitleLabel.text()

    def title(self):
        """
        Returns the title for this page.

        :return     <str>
        """
        return self._titleLabel.text()

    def wizard(self):
        """
        Returns the wizard associated with this page.

        :return     <projexui.widgets.xoverlaywizard.XOverlayWizard>
        """
        return projexui.ancestor(self, XOverlayWizard)

#------------------------------------

class XOverlayWizard(XOverlayWidget):
    WizardButton = enum(BackButton=0,
                        NextButton=1,
                        CommitButton=2,
                        FinishButton=3,
                        CancelButton=4,
                        HelpButton=5,
                        RetryButton=6)

    WizardButtonColors = {
        WizardButton.BackButton: '#58A6D6',
        WizardButton.NextButton: '#58A6D6',
        WizardButton.CommitButton: '#49B84D',
        WizardButton.FinishButton: '#369939',
        WizardButton.CancelButton: '#B0B0B0',
        WizardButton.HelpButton: '#8CA4E6',
        WizardButton.RetryButton: '#D93D3D'
    }

    currentIdChanged = QtCore.Signal(int)
    helpRequested = QtCore.Signal()
    pageAdded = QtCore.Signal(int)
    pageRemoved = QtCore.Signal(int)

    def __init__(self, parent=None):
        super(XOverlayWizard, self).__init__(parent)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # define custom properties
        self._fixedPageSize = QtCore.QSize()
        self._minimumPageSize = QtCore.QSize(0, 0)
        self._maximumPageSize = QtCore.QSize(10000, 10000)
        self._currentId = -1
        self._startId = -1
        self._pages = OrderedDict()
        self._buttons = {}
        self._fields = {}
        self._navigation = []

        # create the buttons
        self._buttons[self.WizardButton.HelpButton] = QtGui.QPushButton(self.tr('Help'), self)
        self._buttons[self.WizardButton.BackButton] = QtGui.QPushButton(self.tr('Back'), self)
        self._buttons[self.WizardButton.NextButton] = QtGui.QPushButton(self.tr('Next'), self)
        self._buttons[self.WizardButton.CommitButton] = QtGui.QPushButton(self.tr('Commit'), self)
        self._buttons[self.WizardButton.FinishButton] = QtGui.QPushButton(self.tr('Finish'), self)
        self._buttons[self.WizardButton.CancelButton] = QtGui.QPushButton(self.tr('Cancel'), self)
        self._buttons[self.WizardButton.RetryButton] = QtGui.QPushButton(self.tr('Retry'), self)

        # don't show any buttons by default
        pal = self.palette()
        for which, btn in self._buttons.items():
            pal.setColor(pal.Button, QtGui.QColor(self.WizardButtonColors[which]))
            pal.setColor(pal.ButtonText, QtGui.QColor('white'))
            btn.setPalette(pal)
            btn.setFixedSize(QtCore.QSize(120, 30))
            btn.hide()

        # create connections
        self._buttons[self.WizardButton.HelpButton].clicked.connect(self.helpRequested)
        self._buttons[self.WizardButton.BackButton].clicked.connect(self.back)
        self._buttons[self.WizardButton.NextButton].clicked.connect(self.next)
        self._buttons[self.WizardButton.CommitButton].clicked.connect(self.commit)
        self._buttons[self.WizardButton.FinishButton].clicked.connect(self.accept)
        self._buttons[self.WizardButton.CancelButton].clicked.connect(self.reject)
        self._buttons[self.WizardButton.RetryButton].clicked.connect(self.retry)

    def addPage(self, page):
        """
        Adds a new overlay wizard page to this wizard.

        :param      page | <projexui.widgets.xoverlaywizard.XOverlayWizardPage>
        """
        self.setPage(len(self._pages), page)

    def adjustSize(self, size):
        """
        Adjusts the size of this wizard and its page contents to the inputed size.

        :param      size | <QtCore.QSize>
        """
        super(XOverlayWizard, self).adjustSize(size)
        self.adjustPage()

    def adjustPage(self):
        """
        Adjusts the page layout composition for this wizard.
        """
        page_size = self.pageSize()

        # resize the current page to the inputed size
        x = (self.width() - page_size.width()) / 2
        y = (self.height() - page_size.height()) / 2
        btn_height = max([btn.height() for btn in self._buttons.values()])

        for page in self._pages.values():
            page.resize(page_size.width(), page_size.height() - btn_height - 6)

        page = self.currentPage()
        if page:
            page.move(x, y)

        # move the left most buttons
        y += page_size.height() - btn_height
        left_btns = (self._buttons[self.WizardButton.HelpButton], self._buttons[self.WizardButton.BackButton])
        for btn in left_btns:
            if btn.isVisible():
                btn.move(x, y)
                btn.raise_()
                x += btn.width() + 6

        # move the right buttons
        x = self.width() - (self.width() - page_size.width()) / 2
        for key in reversed(sorted(self._buttons.keys())):
            btn = self._buttons[key]
            if not btn.isVisible() or btn in left_btns:
                continue

            btn.move(x - btn.width(), y)
            btn.raise_()
            x -= btn.width() + 6

    def back(self):
        """
        Goes to the previous page for this wizard.
        """
        try:
            pageId = self._navigation[self._navigation.index(self.currentId())-1]
            last_page = self.page(pageId)
        except IndexError:
            return

        curr_page = self.currentPage()
        if not (last_page and curr_page):
            return

        self._currentId = pageId

        y = curr_page.y()

        last_page.move(-last_page.width(), y)
        last_page.show()

        # animate the last page in
        anim_in = QtCore.QPropertyAnimation(self)
        anim_in.setTargetObject(last_page)
        anim_in.setPropertyName('pos')
        anim_in.setStartValue(last_page.pos())
        anim_in.setEndValue(curr_page.pos())
        anim_in.setDuration(500)
        anim_in.setEasingCurve(QtCore.QEasingCurve.Linear)

        # animate the current page out
        anim_out = QtCore.QPropertyAnimation(self)
        anim_out.setTargetObject(curr_page)
        anim_out.setPropertyName('pos')
        anim_out.setStartValue(curr_page.pos())
        anim_out.setEndValue(QtCore.QPoint(self.width()+curr_page.width(), y))
        anim_out.setDuration(500)
        anim_out.setEasingCurve(QtCore.QEasingCurve.Linear)

        # create the anim group
        anim_grp = QtCore.QParallelAnimationGroup(self)
        anim_grp.addAnimation(anim_in)
        anim_grp.addAnimation(anim_out)
        anim_grp.finished.connect(curr_page.hide)
        anim_grp.finished.connect(anim_grp.deleteLater)
        anim_grp.start()

        self.currentIdChanged.emit(pageId)

        # update the button states
        self._buttons[self.WizardButton.BackButton].setVisible(self.canGoBack())
        self._buttons[self.WizardButton.NextButton].setVisible(True)
        self._buttons[self.WizardButton.CommitButton].setVisible(last_page.isCommitPage())
        self._buttons[self.WizardButton.FinishButton].setVisible(last_page.isFinalPage())
        self.adjustPage()

    def button(self, which):
        """
        Returns the button associated with the inputed wizard button.

        :param      which | <XOverlayWizard.WizardButton>

        :return     <bool> || None
        """
        return self._buttons.get(which)

    def buttonText(self, which):
        """
        Returns the button text for a given wizard button.

        :param      which | <XOverlayWizard.WizardButton>
        """
        try:
            return self._buttons[which].text()
        except KeyError:
            return ''

    def canGoBack(self):
        """
        Returns whether or not this wizard can move forward.

        :return     <bool>
        """
        try:
            backId = self._navigation.index(self.currentId())-1
            if backId >= 0:
                self._navigation[backId]
            else:
                return False
        except StandardError:
            return False
        else:
            return True

    def canGoForward(self):
        """
        Returns whether or not this wizard can move forward.

        :return     <bool>
        """
        try:
            return not self.currentPage().isFinalPage()
        except AttributeError:
            return False

    def commit(self):
        """
        Commits the current page information.
        """
        try:
            self.currentPage().commit()
        except AttributeError:
            pass

    def currentId(self):
        """
        Returns the page ID of the current page that this wizard is on.

        :return     <int>
        """
        return self._currentId

    def currentPage(self):
        """
        Returns the current page for this wizard.

        :return     <projexui.widgets.xoverlaywizard.XOverlayWizardPage> || None
        """
        try:
            return self._pages[self.currentId()]
        except KeyError:
            return None

    def field(self, name):
        """
        Returns the value for the inputed field property for this wizard.

        :param      name | <str>

        :return     <variant>
        """
        return self._fields.get(name)

    def fixedPageSize(self):
        """
        Returns the fixed page size for this wizard's contents.

        :return     <QtCore.QSize>
        """
        return self._fixedPageSize

    def hasVisitedPage(self, pageId):
        """
        Returns whether or not the user has seen the inputed page id.

        :return     <bool>
        """
        return False

    def minimumPageSize(self):
        """
        Returns the minimum page size for this wizard's contents.

        :return     <QtCore.QSize>
        """
        return self._minimumPageSize

    def maximumPageSize(self):
        """
        Returns the maximum page size for this wizard's contents.

        :return     <QtCore.QSize>
        """
        return self._maximumPageSize

    def next(self):
        """
        Goes to the previous page for this wizard.
        """
        curr_page = self.currentPage()
        if not curr_page:
            return

        pageId = curr_page.nextId()
        try:
            next_page = self._pages[pageId]
        except KeyError:
            return

        self._currentId = pageId
        if not pageId in self._navigation:
            self._navigation.append(pageId)

        y = curr_page.y()

        next_page.move(self.width()+next_page.width(), y)
        next_page.show()

        # animate the last page in
        anim_in = QtCore.QPropertyAnimation(self)
        anim_in.setTargetObject(curr_page)
        anim_in.setPropertyName('pos')
        anim_in.setStartValue(curr_page.pos())
        anim_in.setEndValue(QtCore.QPoint(-curr_page.width(), y))
        anim_in.setDuration(500)
        anim_in.setEasingCurve(QtCore.QEasingCurve.Linear)

        # animate the current page out
        anim_out = QtCore.QPropertyAnimation(self)
        anim_out.setTargetObject(next_page)
        anim_out.setPropertyName('pos')
        anim_out.setStartValue(next_page.pos())
        anim_out.setEndValue(curr_page.pos())
        anim_out.setDuration(500)
        anim_out.setEasingCurve(QtCore.QEasingCurve.Linear)

        # create the anim group
        anim_grp = QtCore.QParallelAnimationGroup(self)
        anim_grp.addAnimation(anim_in)
        anim_grp.addAnimation(anim_out)
        anim_grp.finished.connect(curr_page.hide)
        anim_grp.finished.connect(anim_grp.deleteLater)
        anim_grp.start()

        self.currentIdChanged.emit(pageId)
        next_page.initializePage()

        # update the button states
        self._buttons[self.WizardButton.BackButton].setVisible(True)
        self._buttons[self.WizardButton.NextButton].setVisible(self.canGoForward())
        self._buttons[self.WizardButton.CommitButton].setVisible(next_page.isCommitPage())
        self._buttons[self.WizardButton.FinishButton].setVisible(next_page.isFinalPage())
        self.adjustPage()

    def page(self, pageId):
        """
        Returns the page at the inputed id.

        :return     <projexui.widgets.xoverlaywizard.XOverlayWizardPage> || None
        """
        return self._pages.get(pageId)

    def pageIds(self):
        """
        Returns a list of all the page ids for this wizard.

        :return     [<int>, ..]
        """
        return self._pages.keys()

    def pageSize(self):
        """
        Returns the current page size for this wizard.

        :return     <QtCore.QSize>
        """

        # update the size based on the new size
        page_size = self.fixedPageSize()
        if page_size.isEmpty():
            w = self.width() - 80
            h = self.height() - 80

            min_w = self.minimumPageSize().width()
            min_h = self.minimumPageSize().height()
            max_w = self.maximumPageSize().width()
            max_h = self.maximumPageSize().height()

            page_size = QtCore.QSize(min(max(min_w, w), max_w), min(max(min_h, h), max_h))
        return page_size

    def exec_(self):
        """
        Executes this wizard within the system.
        """
        self.show()
        self.adjustSize(self.size())
        self.restart()

    def restart(self):
        """
        Restarts the whole wizard from the beginning.
        """
        # hide all of the pages
        for page in self._pages.values():
            page.hide()

        pageId = self.startId()
        try:
            first_page = self._pages[pageId]
        except KeyError:
            return

        self._currentId = pageId
        self._navigation = [pageId]

        page_size = self.pageSize()
        x = (self.width() - page_size.width()) / 2
        y = (self.height() - page_size.height()) / 2

        first_page.move(self.width()+first_page.width(), y)
        first_page.show()

        # animate the current page out
        anim_out = QtCore.QPropertyAnimation(self)
        anim_out.setTargetObject(first_page)
        anim_out.setPropertyName('pos')
        anim_out.setStartValue(first_page.pos())
        anim_out.setEndValue(QtCore.QPoint(x, y))
        anim_out.setDuration(500)
        anim_out.setEasingCurve(QtCore.QEasingCurve.Linear)
        anim_out.finished.connect(anim_out.deleteLater)
        anim_out.start()

        self.currentIdChanged.emit(pageId)

        # update the button states
        self._buttons[self.WizardButton.BackButton].setVisible(False)
        self._buttons[self.WizardButton.NextButton].setVisible(self.canGoForward())
        self._buttons[self.WizardButton.CommitButton].setVisible(first_page.isCommitPage())
        self._buttons[self.WizardButton.FinishButton].setVisible(first_page.isFinalPage())
        self.adjustPage()

    def removePage(self, pageId):
        """
        Removes the inputed page from this wizard.

        :param      pageId | <int>
        """
        try:
            self._pages[pageId].deleteLater()
            del self._pages[pageId]
        except KeyError:
            pass

    def retry(self):
        """
        Reruns the current page operation.
        """
        try:
            self.currentPage().initializePage()
        except AttributeError:
            pass

    def setButton(self, which, button):
        """
        Sets the button for this wizard for the inputed type.

        :param      which  | <XOverlayWizard.WizardButton>
                    button | <QtGui.QPushButton>
        """
        try:
            self._buttons[which].deleteLater()
        except KeyError:
            pass

        button.setParent(self)
        self._buttons[which] = button

    def setButtonText(self, which, text):
        """
        Sets the display text for the inputed button to the given text.

        :param      which | <XOverlayWizard.WizardButton>
                    text  | <str>
        """
        try:
            self._buttons[which].setText(text)
        except KeyError:
            pass

    def setField(self, name, value):
        """
        Sets the field value for this wizard to the given value.

        :param      name | <str>
                    value | <variant>
        """
        self._fields[name] = value

    def setFixedPageSize(self, size):
        """
        Sets the page size for the wizard.  This will define the width/height for the contents
        for this wizards page widgets as well as the bounding information for the buttons.  If
        an empty size is given, then the size will automatically be recalculated as the widget sizes.

        :param      size | <QtCore.QSize>
        """
        self._fixedPageSize = size
        self.adjustPage()

    def setMinimumPageSize(self, size):
        """
        Sets the page size for the wizard.  This will define the width/height for the contents
        for this wizards page widgets as well as the bounding information for the buttons.  If
        an empty size is given, then the size will automatically be recalculated as the widget sizes.

        :param      size | <QtCore.QSize>
        """
        self._minimumPageSize = size
        self.adjustPage()

    def setMaximumPageSize(self, size):
        """
        Sets the page size for the wizard.  This will define the width/height for the contents
        for this wizards page widgets as well as the bounding information for the buttons.  If
        an empty size is given, then the size will automatically be recalculated as the widget sizes.

        :param      size | <QtCore.QSize>
        """
        self._maximumPageSize = size
        self.adjustPage()

    def setPage(self, pageId, page):
        """
        Sets the page and id for the given page vs. auto-constructing it.  This will allow the
        developer to create a custom order for IDs.

        :param      pageId | <int>
                    page   | <projexui.widgets.xoverlaywizard.XOverlayWizardPage>
        """
        page.setParent(self)

        # create the drop shadow effect
        effect = QtGui.QGraphicsDropShadowEffect(page)
        effect.setColor(QtGui.QColor('black'))
        effect.setBlurRadius(50)
        effect.setOffset(0, 0)

        page.setGraphicsEffect(effect)

        self._pages[pageId] = page
        if self._startId == -1:
            self._startId = pageId

    def setStartId(self, pageId):
        """
        Sets the starting page id for this wizard to the inputed page id.

        :param      pageId | <int>
        """
        self._startId = pageId

    def startId(self):
        """
        Returns the starting id for this wizard.

        :return     <int>
        """
        return self._startId