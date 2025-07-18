try:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
except ImportError:
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *

from libs.utils import new_icon, label_validator, trimmed

BB = QDialogButtonBox


class LabelDialog(QDialog):

    def __init__(self, text="Enter object label", parent=None, list_item=None):
        super(LabelDialog, self).__init__(parent)

        self.edit = QLineEdit()
        self.edit.setText(text)
        self.edit.setValidator(label_validator())
        self.edit.editingFinished.connect(self.post_process)

        model = QStringListModel()
        model.setStringList(list_item)
        completer = QCompleter()
        completer.setModel(model)
        self.edit.setCompleter(completer)

        self.button_box = bb = BB(BB.Ok | BB.Cancel, Qt.Horizontal, self)
        bb.button(BB.Ok).setIcon(new_icon('done'))
        bb.button(BB.Cancel).setIcon(new_icon('undo'))
        bb.accepted.connect(self.validate)
        bb.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(bb, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.edit)

        if list_item is not None and len(list_item) > 0:
            self.list_widget = QListWidget(self)
            # 设置为多选模式
            self.list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
            for item in list_item:
                self.list_widget.addItem(item)
            self.list_widget.itemClicked.connect(self.list_item_click)
            self.list_widget.itemDoubleClicked.connect(self.list_item_double_click)
            layout.addWidget(self.list_widget)

        self.setLayout(layout)

    def validate(self):
        # 检查输入框中的内容是否有效
        if trimmed(self.edit.text()):
            # 提交前重置标签控件状态
            if hasattr(self, 'list_widget'):
                self.list_widget.clearSelection()
            # 接受输入
            self.accept()

    def post_process(self):
        self.edit.setText(trimmed(self.edit.text()))

    def pop_up(self, text='', move=True):
        """
        Shows the dialog, setting the current text to `text`, and blocks the caller until the user has made a choice.
        If the user entered a label, that label is returned, otherwise (i.e. if the user cancelled the action)
        `None` is returned.
        """
        # 重置标签控件状态
        if hasattr(self, 'list_widget'):
            self.list_widget.clearSelection()
            
            # 自动选中下拉列表中对应的项目
            if text:
                if ',' in text:  # 多个标签情况
                    labels = [label.strip() for label in text.split(',') if label.strip()]
                else:  # 单个标签情况
                    labels = [text.strip()]

                for i in range(self.list_widget.count()):
                    item = self.list_widget.item(i)
                    if item.text() in labels:
                        item.setSelected(True)
        
        self.edit.setText(text)
        self.edit.setSelection(0, len(text))
        self.edit.setFocus(Qt.PopupFocusReason)
        if move:
            cursor_pos = QCursor.pos()

            # move OK button below cursor
            btn = self.button_box.buttons()[0]
            self.adjustSize()
            btn.adjustSize()
            offset = btn.mapToGlobal(btn.pos()) - self.pos()
            offset += QPoint(btn.size().width() // 4, btn.size().height() // 2)
            cursor_pos.setX(max(0, cursor_pos.x() - offset.x()))
            cursor_pos.setY(max(0, cursor_pos.y() - offset.y()))

            parent_bottom_right = self.parentWidget().geometry()
            max_x = parent_bottom_right.x() + parent_bottom_right.width() - self.sizeHint().width()
            max_y = parent_bottom_right.y() + parent_bottom_right.height() - self.sizeHint().height()
            max_global = self.parentWidget().mapToGlobal(QPoint(max_x, max_y))
            if cursor_pos.x() > max_global.x():
                cursor_pos.setX(max_global.x())
            if cursor_pos.y() > max_global.y():
                cursor_pos.setY(max_global.y())
            self.move(cursor_pos)
        return trimmed(self.edit.text()) if self.exec_() else None

    def list_item_click(self, t_qlist_widget_item):
        # 获取所有选中的项目
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            # 将多个选中的标签用逗号分隔
            selected_texts = [trimmed(item.text()) for item in selected_items]
            combined_text = ', '.join(selected_texts)
            self.edit.setText(combined_text)
        else:
            # 如果没有选中项，清空编辑框
            self.edit.setText('')

    def list_item_double_click(self, t_qlist_widget_item):
        self.list_item_click(t_qlist_widget_item)
        self.validate()
