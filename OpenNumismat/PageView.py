from PyQt5 import QtCore
from PyQt5 import QtSql
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *

from OpenNumismat.ListView import ListView
from OpenNumismat.StatisticsView import statisticsAvailable
from OpenNumismat.StatisticsView import StatisticsView
from OpenNumismat.EditCoinDialog.ImageLabel import ImageLabel
from OpenNumismat.Collection.CollectionFields import FieldTypes as Type
from OpenNumismat.EditCoinDialog.EditCoinDialog import EditCoinDialog
from OpenNumismat.CustomizeTreeDialog import CustomizeTreeDialog
from OpenNumismat.Tools import Gui
from OpenNumismat.Tools.Converters import numberWithFraction
from OpenNumismat.Collection.CollectionFields import Statuses
from OpenNumismat.EditCoinDialog.DetailsTabWidget import DetailsTabWidget
from OpenNumismat.Settings import Settings


class ImageView(QWidget):

    def __init__(self, direction, parent=None):
        super().__init__(parent)

        self.currentIndex = None

        if direction == QBoxLayout.LeftToRight:
            layout = self.__createHorizontalLayout()
        else:
            layout = self.__createVerticalLayout()

        self.setLayout(layout)

    def __createVerticalLayout(self):
        layout = QVBoxLayout()

        self.imageLayout = QVBoxLayout()
        self.imageLayout.setContentsMargins(QtCore.QMargins())
        layout.addWidget(self.__layoutToWidget(self.imageLayout))

        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setAlignment(Qt.AlignCenter | Qt.AlignBottom)
        widget = self.__layoutToWidget(self.buttonLayout)
        widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        layout.addWidget(widget)

        return layout

    def __createHorizontalLayout(self):
        layout = QHBoxLayout()

        self.buttonLayout = QVBoxLayout()
        self.buttonLayout.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        widget = self.__layoutToWidget(self.buttonLayout)
        widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(widget)

        self.imageLayout = QHBoxLayout()
        self.imageLayout.setContentsMargins(QtCore.QMargins())
        layout.addWidget(self.__layoutToWidget(self.imageLayout))

        return layout

    def setModel(self, model):
        self.model = model

        self.imageFields = []
        for field in self.model.fields.userFields:
            if field.type in (Type.Image, Type.EdgeImage):
                self.imageFields.append(field)

        # By default show only first 2 images
        self.showedCount = Settings()['images_by_default']

        self.imageButtons = []
        for field in self.imageFields:
            button = QCheckBox(self)
            button.setToolTip(field.title)
            button.setDisabled(True)
            button.stateChanged.connect(self.buttonClicked)
            self.imageButtons.append(button)
            self.buttonLayout.addWidget(button)

    def clear(self):
        for _ in range(self.imageLayout.count()):
            item = self.imageLayout.itemAt(0)
            self.imageLayout.removeItem(item)
            item.widget().deleteLater()

    def buttonClicked(self, _state):
        self.clear()

        current = self.currentIndex
        self.showedCount = 0
        for i, field in enumerate(self.imageFields):
            if self.imageButtons[i].checkState() == Qt.Checked:
                index = self.model.index(current.row(), field.id)
                data = index.data(Qt.UserRole)
                img = self.model.getImage(data)
                image = ImageLabel(self)
                image.loadFromData(img)
                title = self.model.getImageTitle(data)
                image.setToolTip(title)
                self.imageLayout.addWidget(image)

                self.showedCount = self.showedCount + 1

    def rowChangedEvent(self, current):
        self.currentIndex = current
        self.clear()

        for i, field in enumerate(self.imageFields):
            self.imageButtons[i].stateChanged.disconnect(self.buttonClicked)
            self.imageButtons[i].setCheckState(Qt.Unchecked)
            self.imageButtons[i].setDisabled(True)

            index = self.model.index(current.row(), field.id)
            data = index.data(Qt.UserRole)
            img = self.model.getImage(data)
            if img and not img.isNull():
                if self.imageLayout.count() < self.showedCount:
                    image = ImageLabel(self)
                    image.loadFromData(img)
                    title = self.model.getImageTitle(data)
                    image.setToolTip(title)
                    self.imageLayout.addWidget(image)

                    self.imageButtons[i].setCheckState(Qt.Checked)

                self.imageButtons[i].setDisabled(False)

            self.imageButtons[i].stateChanged.connect(self.buttonClicked)

    def __layoutToWidget(self, layout):
        widget = QWidget(self)
        widget.setLayout(layout)
        return widget


class TreeWidgetItem(QTreeWidgetItem):

    def __lt__(self, other):
        left = self.data(0, Qt.UserRole + 3)
        right = other.data(0, Qt.UserRole + 3)

        if not left or not right:
            return super().__lt__(other)

        min_len = min(len(left), len(right))

        for i in reversed(range(min_len)):
            if left[i] == right[i]:
                pass
            else:
                if isinstance(left[i], str) or isinstance(right[i], str):
                    return str(left[i]) < str(right[i])
                else:
                    return left[i] < right[i]

        return len(left) < len(right)


class TreeView(QTreeWidget):
    FiltersRole = Qt.UserRole
    FieldsRole = Qt.UserRole + 1
    ParamRole = Qt.UserRole + 2
    SortDataRole = Qt.UserRole + 3

    def __init__(self, treeParam, parent=None):
        super().__init__(parent)

        self.show_tree_icons = treeParam.show_tree_icons
        self.convert_fraction = treeParam.convert_fraction

        self.setHeaderHidden(True)
        self.setAutoScroll(False)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenuEvent)

        self.currentItemChanged.connect(self.itemActivatedEvent)
        self.itemExpanded.connect(self.expandedEvent)
        self.collapsed.connect(self.collapsedEvent)

        self.treeParam = treeParam

        # Changing of TreeView is enabled (by signals from model or ListView)
        self.changingEnabled = True

    def setModel(self, model, reference):
        self.db = model.database()
        self.model = model
        self.reference = reference

        self.treeParam.rootTitle = model.title
        rootItem = QTreeWidgetItem([model.title, ])
        rootItem.setData(0, self.ParamRole, 0)
        rootItem.setData(0, self.FiltersRole, '')

        self.addTopLevelItem(rootItem)

    def expandedEvent(self, item):
        for i in range(item.childCount()):
            child = item.child(i)
            if child.childCount() == 0:
                paramIndex = child.data(0, self.ParamRole) + 1
                filters = child.data(0, self.FiltersRole)
                self.__updateChilds(child, paramIndex, filters)

        self.resizeColumnToContents(0)

    def collapsedEvent(self, parentItem):
        self.resizeColumnToContents(0)

    def __updateChilds(self, item, paramIndex=0, filters=''):
        fields = self.treeParam.fieldNames(paramIndex)
        if not fields:
            return

        sql = "SELECT DISTINCT %s FROM coins" % ','.join(fields)
        if filters:
            sql += " WHERE " + filters
        query = QtSql.QSqlQuery(sql, self.db)
        hasEmpty = False
        while query.next():
            record = query.record()
            data = []
            orig_data = []
            filterSql = []
            for i in range(record.count()):
                if record.isNull(i):
                    hasEmpty = True
                    continue

                orig_data.append(record.value(i))
                text = str(record.value(i))
                if text:
                    if fields[i] == 'status':
                        data.append(Statuses[text])
                    elif fields[i] == 'year':
                        label = text
                        try:
                            year = int(text)
                            if year < 0:
                                label = "%d BC" % -year
                        except ValueError:
                            pass
                        data.append(label)
                    elif fields[i] == 'value':
                        label, _ = numberWithFraction(text, self.convert_fraction)
                        data.append(label)
                    else:
                        data.append(text)
                    escapedText = text.replace("'", "''")
                    filterSql.append("%s='%s'" % (fields[i], escapedText))
                else:
                    hasEmpty = True

            if data:
                if len(data) > 1:
                    newFilters = ' AND '.join(filterSql)
                    text = ' '.join(data)
                    child = TreeWidgetItem([text, ])
                    child.setData(0, self.SortDataRole, orig_data)
                else:
                    newFilters = filterSql[0]
                    child = TreeWidgetItem(data)
                    child.setData(0, self.SortDataRole, orig_data)

                if filters:
                    newFilters = filters + ' AND ' + newFilters

                child.setData(0, self.ParamRole, paramIndex)
                child.setData(0, self.FiltersRole, newFilters)
                child.setData(0, self.FieldsRole, fields)

                if self.show_tree_icons:
                    icon = self.reference.getIcon(fields[0], data[0])
                    if icon:
                        child.setIcon(0, icon)

                item.addChild(child)

                # Restore selection
                if newFilters == self.model.extFilter:
                    self.currentItemChanged.disconnect(self.itemActivatedEvent)
                    self.setCurrentItem(child)
                    self.currentItemChanged.connect(self.itemActivatedEvent)

        item.sortChildren(0, Qt.AscendingOrder)

        if hasEmpty and len(fields) == 1 and item.childCount() > 0:
            text = self.tr("Other")
            newFilters = "ifnull(%s,'')=''" % fields[0]
            if filters:
                newFilters = filters + ' AND ' + newFilters

            child = QTreeWidgetItem([text, ])
            child.setData(0, self.ParamRole, paramIndex)
            child.setData(0, self.FiltersRole, newFilters)
            child.setData(0, self.FieldsRole, fields)
            item.addChild(child)

            # Restore selection
            if newFilters == self.model.extFilter:
                self.currentItemChanged.disconnect(self.itemActivatedEvent)
                self.setCurrentItem(child)
                self.currentItemChanged.connect(self.itemActivatedEvent)

        # Recursion for next field if nothing selected
        if item.childCount() == 0:
            self.__updateChilds(item, paramIndex + 1, filters)

    def modelChanged(self):
        if self.changingEnabled:
            self.collapseAll()
            rootItem = self.topLevelItem(0)

            self.currentItemChanged.disconnect(self.itemActivatedEvent)
            rootItem.takeChildren()  # remove all children
            self.currentItemChanged.connect(self.itemActivatedEvent)

            self.__updateChilds(rootItem)
            self.expandItem(rootItem)

    def rowChangedEvent(self, current):
        if self.changingEnabled:
            if current.isValid():
                self.collapseAll()
                self.scrollToIndex(current)

    def scrollToIndex(self, index, parent=None):
        if not parent:
            parent = self.topLevelItem(0)

        for i in range(parent.childCount()):
            subItem = parent.child(i)
            fields = subItem.data(0, self.FieldsRole)
            text1 = subItem.text(0)
            textPart = []
            for field in fields:
                index = self.model.index(index.row(),
                                         self.model.fieldIndex(field))
                if field in ('status', 'year'):
                    textPart.append(str(index.data()))
                else:
                    val = str(index.data(Qt.UserRole))
                    if val:
                        textPart.append(val)
            text2 = ' '.join(textPart)
            if text1 == text2 or (not text2 and text1 == self.tr("Other")):
                self.expandItem(parent)
                self.scrollToItem(subItem)
                self.scrollToIndex(index, subItem)
                break

    def scrollToItem(self, item, hint=QTreeWidget.EnsureVisible):
        super().scrollToItem(item, hint)

        parentItem = item.parent()
        if parentItem:
            itemRect = self.visualItemRect(parentItem)
            if itemRect.x() < 0:
                columnWidth = self.columnWidth(0)
                itemWidth = itemRect.width()
                self.horizontalScrollBar().setValue(columnWidth - itemWidth)
            elif self.viewport().width() / 2 < itemRect.x():
                columnWidth = self.columnWidth(0)
                itemWidth = itemRect.width()
                self.horizontalScrollBar().setValue(itemRect.x())

    def itemActivatedEvent(self, current, previous):
        self.scrollToItem(current)
        self.resizeColumnToContents(0)

        self.changingEnabled = False
        filter_ = current.data(0, self.FiltersRole)
        self.model.setAdditionalFilter(filter_)
        self.changingEnabled = True

    def contextMenuEvent(self, pos):
        menu = QMenu(self)
        act = menu.addAction(self.tr("Add new coin..."), self._addCoin)
        if not (self.model.rowCount() and self.selectedItems()):
            act.setDisabled(True)
        act = menu.addAction(self.tr("Edit coins..."), self._multiEdit)
        if not (self.model.rowCount() and self.selectedItems()):
            act.setDisabled(True)
        menu.addSeparator()
        menu.addAction(self.tr("Customize tree..."), self._customizeTree)
        menu.exec_(self.mapToGlobal(pos))

    def _customizeTree(self):
        dialog = CustomizeTreeDialog(self.model, self.treeParam, self)
        if dialog.exec_() == QDialog.Accepted:
            self.treeParam.save()
            self.modelChanged()

    def _addCoin(self):
        self.changingEnabled = False
        storedFilter = self.model.intFilter
        # TODO: This change ListView!
        self.model.setFilter('')
        self.changingEnabled = True

        newRecord = self.model.record()
        # Fill new record with values of first record
        for j in range(newRecord.count()):
            newRecord.setValue(j, self.model.record(0).value(j))

        for i in range(self.model.rowCount()):
            record = self.model.record(i)
            for j in range(newRecord.count()):
                value = record.value(j)
                if newRecord.value(j) != value or not value:
                    newRecord.setNull(j)

        self.model.addCoin(newRecord, self)

        self.model.setFilter(storedFilter)

    def _multiEdit(self):
        self.changingEnabled = False
        storedFilter = self.model.intFilter
        self.model.setFilter('')
        self.changingEnabled = True

        # Fill multi record for editing
        multiRecord = self.model.record(0)
        usedFields = [Qt.Checked] * multiRecord.count()
        for i in range(self.model.rowCount()):
            record = self.model.record(i)
            for j in range(multiRecord.count()):
                value = record.value(j)
                if multiRecord.value(j) != value or not value:
                    multiRecord.setNull(j)
                    usedFields[j] = Qt.Unchecked

        # TODO: Make identical with ListView._multiEdit
        dialog = EditCoinDialog(self.model, multiRecord, self, usedFields)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            progressDlg = Gui.ProgressDialog(self.tr("Updating records"),
                                self.tr("Cancel"), self.model.rowCount(), self)

            # Fill records by used fields in multi record
            multiRecord = dialog.getRecord()
            usedFields = dialog.getUsedFields()
            for i in range(self.model.rowCount()):
                progressDlg.setValue(i)
                if progressDlg.wasCanceled():
                    break

                record = self.model.record(i)
                for j in range(multiRecord.count()):
                    if usedFields[j] == Qt.Checked:
                        record.setValue(j, multiRecord.value(j))
                self.model.setRecord(i, record)

            self.model.submitAll()
            progressDlg.reset()

        self.model.setFilter(storedFilter)


class DetailsView(QWidget):

    def __init__(self, direction, parent=None):
        super().__init__(parent)

        self.direction = direction

        self.resize(120, 120)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

    def setModel(self, model):
        self.model = model

        self.widget = DetailsTabWidget(model, self.direction)
        self.layout.addWidget(self.widget)

    def rowChangedEvent(self, current):
        if current.isValid():
            record = self.model.record(current.row())
            self.widget.fillItems(record)
        else:
            self.widget.clear()


class Splitter(QSplitter):
    def __init__(self, title, orientation=Qt.Horizontal, parent=None):
        super().__init__(orientation, parent)

        self.title = title
        self.splitterMoved.connect(self.splitterPosChanged)

    def splitterPosChanged(self, pos, index):
        settings = QtCore.QSettings()
        settings.setValue('pageview/splittersizes' + self.title, self.sizes())

    def showEvent(self, e):
        settings = QtCore.QSettings()
        sizes = settings.value('pageview/splittersizes' + self.title)
        if sizes:
            for i in range(len(sizes)):
                sizes[i] = int(sizes[i])

            self.splitterMoved.disconnect(self.splitterPosChanged)
            self.setSizes(sizes)
            self.splitterMoved.connect(self.splitterPosChanged)


class PageView(Splitter):
    def __init__(self, pageParam, parent=None):
        super().__init__('0', parent=parent)

        imagesAtBottom = pageParam.images_at_bottom

        self._model = None
        self.param = pageParam
        self.id = pageParam.id
        self.treeView = TreeView(pageParam.treeParam, self)
        self.listView = ListView(pageParam.listParam, self)
        if imagesAtBottom:
            self.imageView = ImageView(QBoxLayout.LeftToRight, self)
            self.detailsView = DetailsView(QBoxLayout.TopToBottom, self)
        else:
            self.imageView = ImageView(QBoxLayout.TopToBottom, self)
            self.detailsView = DetailsView(QBoxLayout.LeftToRight, self)

        self.splitter1 = Splitter('1', Qt.Vertical, self)
        splitter2 = Splitter('2', parent=self.splitter1)
        splitter2.addWidget(self.treeView)
        splitter2.addWidget(self.listView)
        self.splitter1.addWidget(splitter2)
        if imagesAtBottom:
            self.splitter1.addWidget(self.imageView)
        else:
            self.splitter1.addWidget(self.detailsView)

        self.statisticsShowed = pageParam.statisticsParam['showed']
        if statisticsAvailable:
            self.statisticsView = StatisticsView(pageParam.statisticsParam, self)
            self.statisticsView.setMinimumHeight(200)
            if self.statisticsShowed:
                self.splitter1.insertWidget(2, self.statisticsView)
            else:
                self.splitter1.insertWidget(1, self.statisticsView)

        self.addWidget(self.splitter1)
        if imagesAtBottom:
            self.addWidget(self.detailsView)
        else:
            self.addWidget(self.imageView)

        self.listView.rowChanged.connect(self.imageView.rowChangedEvent)
        self.listView.rowChanged.connect(self.treeView.rowChangedEvent)
        self.listView.rowChanged.connect(self.detailsView.rowChangedEvent)
        self.splitterMoved.connect(self.splitterPosChanged)

    def setModel(self, model, reference):
        self._model = model

        self.treeView.setModel(model, reference)
        self.listView.setModel(model)
        self.imageView.setModel(model)
        self.detailsView.setModel(model)
        if statisticsAvailable:
            self.statisticsView.setModel(model)
            self.prepareStatistics(self.statisticsShowed)

        self._model.modelChanged.connect(self.modelChanged)

    def model(self):
        return self._model

    def modelChanged(self):
        self.treeView.modelChanged()
        self.listView.modelChanged()
        if statisticsAvailable and self.statisticsShowed:
            self.statisticsView.modelChanged()

    def prepareStatistics(self, show):
        if not statisticsAvailable:
            return

        sizes = self.splitter1.sizes()

        old_widget = self.splitter1.widget(1)
        old_widget.hide()
        new_widget = self.splitter1.widget(2)
        new_widget.show()
        self.splitter1.insertWidget(1, new_widget)

        if self.statisticsShowed != show:
            self.param.statisticsParam['showed'] = show

        self.statisticsShowed = show

        self.splitter1.setSizes(sizes)

    def showStatistics(self, show):
        self.prepareStatistics(show)
        if show:
            self.statisticsView.modelChanged()
