#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QAction, QShortcut, QMessageBox, QDialog, QVBoxLayout, 
                            QLabel, QTableWidget, QTableWidgetItem, QHeaderView, 
                            QPushButton, QDialogButtonBox)
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QKeySequence

# 导入保存函数
from flowchart import save_functions

class KeyboardShortcutManager:
    """键盘快捷键管理器"""
    
    def __init__(self, main_window):
        """初始化快捷键管理器"""
        self.main_window = main_window
        self._setup_shortcuts()
    
    def _setup_shortcuts(self):
        """设置快捷键"""
        # 文件操作快捷键
        self._add_shortcut(QKeySequence.New, self.main_window.newFlowchart, "新建流程图")
        self._add_shortcut(QKeySequence.Open, self.main_window.openFlowchart, "打开流程图")
        self._add_shortcut(QKeySequence.Save, lambda: save_functions.save_flowchart(self.main_window), "保存流程图")
        self._add_shortcut(QKeySequence.SaveAs, lambda: save_functions.save_flowchart_as(self.main_window), "另存为")
        
        # 编辑操作快捷键
        self._add_shortcut(QKeySequence.Undo, self.main_window.undo, "撤销")
        self._add_shortcut(QKeySequence.Redo, self.main_window.redo, "重做")
        self._add_shortcut(QKeySequence.Delete, self.main_window.deleteSelected, "删除选中")
        
        # 视图操作快捷键 - 暂时移除缩放相关快捷键
        
        # 导出快捷键
        self._add_shortcut(QKeySequence(Qt.CTRL + Qt.Key_E), 
                          lambda: self.main_window.exporter.export_flowchart(), "导出")
        
        # 折叠/展开快捷键
        self._add_shortcut(QKeySequence(Qt.CTRL + Qt.Key_F), 
                          lambda: self.toggle_fold_selected(), "折叠/展开选中节点")
        
        # 自动布局快捷键
        self._add_shortcut(QKeySequence(Qt.CTRL + Qt.Key_L), 
                          lambda: AutoLayoutAlgorithm(self.main_window).apply_layout(), "自动布局")
        
        # 帮助快捷键
        self._add_shortcut(QKeySequence(Qt.Key_F1), self.show_shortcuts_help, "显示快捷键帮助")
    
    def _add_shortcut(self, key_sequence, callback, description=None):
        """添加快捷键"""
        shortcut = QShortcut(key_sequence, self.main_window)
        shortcut.activated.connect(callback)
        if description:
            shortcut.setWhatsThis(description)
    
    def toggle_fold_selected(self):
        """折叠/展开选中的节点"""
        selected_nodes = [item for item in self.main_window.scene.selectedItems() 
                         if hasattr(item, 'node_type')]
        
        if not selected_nodes:
            QMessageBox.information(self.main_window, "提示", "请先选择要折叠/展开的节点")
            return
        
        for node in selected_nodes:
            self._toggle_fold_node(node)
    
    def _toggle_fold_node(self, node):
        """折叠或展开单个节点"""
        # 获取节点的所有子节点
        child_nodes = node.get_child_nodes()
        
        # 如果节点没有子节点，则不做任何操作
        if not child_nodes:
            return
        
        # 检查节点是否已经被折叠
        is_folded = getattr(node, 'is_folded', False)
        
        # 如果有多层子节点，则询问用户是否要折叠所有层级
        all_descendants = node.getAllChildNodes()
        if len(all_descendants) > len(child_nodes) and not is_folded:
            # 如果这个节点有多个层级的子节点，询问用户是否要折叠所有层级
            reply = QMessageBox.question(
                self.main_window,
                "折叠选项",
                "这个节点有多层级的子节点，您想要折叠哪些层级？",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Cancel:
                return
            elif reply == QMessageBox.Yes:
                # 折叠所有层级
                self._fold_all_levels(node)
                return
            # 如果选择No，则只折叠第一层子节点，继续执行下面的代码
        
        if is_folded:
            # 展开节点
            self._expand_node(node, child_nodes)
        else:
            # 折叠节点
            self._collapse_node(node, child_nodes)
    
    def _fold_all_levels(self, node):
        """折叠节点的所有层级子节点"""
        # 获取所有子节点（包括子节点的子节点）
        all_descendants = node.getAllChildNodes()
        
        # 首先将所有子节点设置为可见
        for child in all_descendants:
            child.setVisible(True)
            if hasattr(child, 'is_folded') and child.is_folded:
                child.is_folded = False
        
        # 然后折叠当前节点，隐藏所有子节点
        direct_children = node.get_child_nodes()
        self._collapse_node(node, direct_children)
        
        # 对于所有具有子节点的子节点，也将其标记为折叠状态
        for child in direct_children:
            if child.get_child_nodes():
                child.is_folded = True
                
        # 更新场景
        node.scene().update()
    
    def _collapse_node(self, node, child_nodes):
        """折叠节点，隐藏其所有子节点"""
        # 保存子节点的原始可见性状态
        node.children_visibility = {}
        
        # 递归隐藏所有子节点
        for child in child_nodes:
            node.children_visibility[child] = child.isVisible()
            child.setVisible(False)
            
            # 隐藏连接线
            for conn in self.main_window.scene.items():
                if hasattr(conn, 'start_node') and hasattr(conn, 'end_node'):
                    if conn.start_node == node and conn.end_node == child:
                        conn.setVisible(False)
        
        # 标记节点为已折叠
        node.is_folded = True
        
        # 更新节点外观以指示其已折叠
        node.setBrush(node.color.darker(120))
        node.update()
    
    def _expand_node(self, node, child_nodes):
        """展开节点，显示其直接子节点"""
        # 恢复子节点的可见性
        if hasattr(node, 'children_visibility'):
            for child, was_visible in node.children_visibility.items():
                child.setVisible(was_visible)
                
                # 恢复连接线可见性
                for conn in self.main_window.scene.items():
                    if hasattr(conn, 'start_node') and hasattr(conn, 'end_node'):
                        if conn.start_node == node and conn.end_node == child:
                            conn.setVisible(True)
        
        # 标记节点为未折叠
        node.is_folded = False
        
        # 恢复节点外观
        node.setBrush(node.color)
        node.update()
    
    def show_shortcuts_help(self):
        """显示快捷键帮助对话框"""
        dialog = ShortcutsHelpDialog(self.main_window)
        dialog.exec_()


class ShortcutsHelpDialog(QDialog):
    """快捷键帮助对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("键盘快捷键帮助")
        self.setMinimumSize(400, 500)
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 添加标题
        title = QLabel("可用的键盘快捷键")
        title.setAlignment(Qt.AlignCenter)
        font = title.font()
        font.setPointSize(14)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        
        # 创建快捷键表格
        self.shortcuts_table = QTableWidget(0, 2)
        self.shortcuts_table.setHorizontalHeaderLabels(["快捷键", "功能"])
        self.shortcuts_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.shortcuts_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.shortcuts_table)
        
        # 填充快捷键信息
        self._populate_shortcuts()
        
        # 添加关闭按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _populate_shortcuts(self):
        """填充快捷键表格"""
        shortcuts = [
            ("Ctrl+N", "新建流程图"),
            ("Ctrl+O", "打开流程图"),
            ("Ctrl+S", "保存流程图"),
            ("Ctrl+Shift+S", "另存为"),
            ("Ctrl+Z", "撤销"),
            ("Ctrl+Y", "重做"),
            ("Delete", "删除选中"),
            ("Ctrl+A", "全选"),
            ("Ctrl++", "放大"),
            ("Ctrl+-", "缩小"),
            ("Ctrl+0", "重置缩放"),
            ("Ctrl+E", "导出流程图"),
            ("Ctrl+F", "折叠/展开选中节点"),
            ("Ctrl+L", "应用自动布局"),
            ("F1", "显示此帮助")
        ]
        
        self.shortcuts_table.setRowCount(len(shortcuts))
        
        for i, (key, description) in enumerate(shortcuts):
            self.shortcuts_table.setItem(i, 0, QTableWidgetItem(key))
            self.shortcuts_table.setItem(i, 1, QTableWidgetItem(description))


def extend_node_mouse_double_click_event(node, event, main_window):
    """处理节点的双击事件，用于折叠/展开"""
    # 获取节点的所有子节点
    child_nodes = node.get_child_nodes()
    
    # 如果节点没有子节点，则不做任何操作
    if not child_nodes:
        return
    
    # 检查节点是否已经被折叠
    is_folded = getattr(node, 'is_folded', False)
    
    # 创建快捷键管理器的实例（如果不存在）
    if not hasattr(main_window, 'shortcut_manager'):
        main_window.shortcut_manager = KeyboardShortcutManager(main_window)
    
    # 使用快捷键管理器的方法来折叠/展开节点
    if is_folded:
        main_window.shortcut_manager._expand_node(node, child_nodes)
    else:
        main_window.shortcut_manager._collapse_node(node, child_nodes)


class AutoLayoutAlgorithm:
    """自动布局算法"""
    
    def __init__(self, main_window):
        """初始化自动布局算法"""
        self.main_window = main_window
        self.scene = main_window.scene
        
        # 布局参数
        self.horizontal_spacing = 100  # 水平间距
        self.vertical_spacing = 80     # 垂直间距
        self.level_height = 120        # 每层高度
    
    def apply_layout(self):
        """应用自动布局算法"""
        # 获取所有节点
        nodes = [item for item in self.scene.items() if hasattr(item, 'node_type')]
        
        if not nodes:
            QMessageBox.information(self.main_window, "提示", "当前没有节点可布局")
            return
        
        # 找到根节点（没有父节点的节点）
        root_nodes = []
        for node in nodes:
            has_parent = False
            for conn in self.scene.items():
                if hasattr(conn, 'start_node') and hasattr(conn, 'end_node'):
                    if conn.end_node == node:
                        has_parent = True
                        break
            if not has_parent:
                root_nodes.append(node)
        
        if not root_nodes:
            # 如果没有找到根节点，使用第一个节点作为根节点
            root_nodes = [nodes[0]]
        
        # 为每个根节点应用布局
        x_offset = 0
        for root in root_nodes:
            # 计算树的宽度
            tree_width = self._calculate_tree_width(root)
            
            # 应用布局
            self._layout_subtree(root, x_offset, 0, tree_width)
            
            # 更新下一个树的水平偏移
            x_offset += tree_width + self.horizontal_spacing * 2
    
    def _calculate_tree_width(self, node, level=0, visited=None):
        """计算以node为根的树的宽度"""
        if visited is None:
            visited = set()
        
        # 避免循环引用
        if node in visited:
            return node.width
        
        visited.add(node)
        
        # 获取子节点
        children = self._get_children(node)
        
        if not children:
            return node.width
        
        # 计算所有子树的宽度总和
        total_width = sum(self._calculate_tree_width(child, level+1, visited) for child in children)
        
        # 考虑子节点之间的间距
        if len(children) > 1:
            total_width += self.horizontal_spacing * (len(children) - 1)
        
        # 返回最大宽度
        return max(node.width, total_width)
    
    def _layout_subtree(self, node, x, y, width, visited=None):
        """递归布局子树"""
        if visited is None:
            visited = set()
        
        # 避免循环引用
        if node in visited:
            return
        
        visited.add(node)
        
        # 设置节点位置
        node.setPos(x, y)
        
        # 获取子节点
        children = self._get_children(node)
        
        if not children:
            return
        
        # 计算子节点的水平位置
        child_x = x - width/2 + node.width/2
        
        for child in children:
            # 计算子树宽度
            child_width = self._calculate_tree_width(child)
            
            # 递归布局子树
            self._layout_subtree(child, child_x + child_width/2, y + self.level_height, child_width, visited)
            
            # 更新下一个子节点的水平位置
            child_x += child_width + self.horizontal_spacing
    
    def _get_children(self, node):
        """获取节点的所有子节点"""
        children = []
        for conn in self.scene.items():
            if hasattr(conn, 'start_node') and hasattr(conn, 'end_node'):
                if conn.start_node == node:
                    children.append(conn.end_node)
        return children
