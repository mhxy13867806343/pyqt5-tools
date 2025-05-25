#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import math
import json
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QGraphicsScene, QGraphicsView,
                             QGraphicsItem, QGraphicsEllipseItem, QGraphicsRectItem,
                             QGraphicsLineItem, QGraphicsTextItem, QGraphicsPolygonItem,
                             QMenu, QAction, QInputDialog, QColorDialog, QMessageBox,
                             QToolBar, QComboBox, QPushButton, QVBoxLayout, QHBoxLayout,
                             QWidget, QLabel, QLineEdit, QDialog, QFormLayout, QDialogButtonBox,
                             QFileDialog, QGraphicsPathItem, QStackedWidget, QSlider)
from PyQt5.QtCore import Qt, QPointF, QRectF, QLineF, QSizeF, QSize, QMarginsF
from PyQt5.QtGui import QPen, QBrush, QColor, QPainterPath, QPolygonF, QFont, QIcon, QPainter, QPixmap, QFontMetrics, \
    QLinearGradient, QImage, QPdfWriter, QPageSize, QKeySequence

# 导入自定义模块
from flowchart import export, extensions, advanced, save_functions

# 节点类型
NODE_TYPES = {
    "中心主题": {"shape": "rounded_rect", "color": QColor(0, 176, 151)},  # 绿松石色
    "主要分支": {"shape": "rounded_rect", "color": QColor(135, 206, 250)},  # 浅蓝色
    "次要分支": {"shape": "rounded_rect", "color": QColor(255, 182, 193)},  # 浅粉色
    "叶子节点": {"shape": "rounded_rect", "color": QColor(211, 211, 211)},  # 浅灰色
    "备注": {"shape": "cloud", "color": QColor(255, 255, 153)},  # 浅黄色
}

# 添加扩展节点类型
NODE_TYPES.update(extensions.EXTENDED_NODE_TYPES)

class FlowchartNode(QGraphicsItem):
    """思维导图节点"""
    
    def __init__(self, node_type, text="", pos=QPointF(0, 0), parent=None):
        super().__init__(parent)
        self.node_type = node_type
        self.node_text = text
        
        # 根据文本长度自适应节点大小
        font = QFont()
        font.setPointSize(10)
        metrics = QFontMetrics(font)
        text_width = metrics.width(text) + 40  # 添加一些填充
        text_height = metrics.height() * (1 + text.count('\n')) + 20
        
        self.width = max(120, text_width)  # 最小宽度
        self.height = max(40, text_height)  # 最小高度
        
        self.color = NODE_TYPES[node_type]["color"]
        self.shape_type = NODE_TYPES[node_type]["shape"]
        self.connections = []  # 存储连接到此节点的连接线
        
        # 设置节点属性
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        
        # 设置位置
        self.setPos(pos)
    
    def boundingRect(self):
        """返回节点的边界矩形"""
        # 为了保证云形状等特殊形状有足够的空间
        extra_space = 15 if self.shape_type == "cloud" else 5
        return QRectF(-self.width/2 - extra_space, -self.height/2 - extra_space, 
                     self.width + 2*extra_space, self.height + 2*extra_space)
    
    def shape(self):
        """返回节点的形状用于碰撞检测"""
        path = QPainterPath()
        
        if self.shape_type == "rounded_rect":
            rect = QRectF(-self.width/2, -self.height/2, self.width, self.height)
            path.addRoundedRect(rect, 10, 10)  # 圆角矩形
        elif self.shape_type == "cloud":
            # 绘制一个简单的云形状
            self._draw_cloud_path(path)
        else:
            # 默认使用矩形
            path.addRect(QRectF(-self.width/2, -self.height/2, self.width, self.height))
            
        return path
    
    def _draw_cloud_path(self, path):
        """绘制云形状的路径"""
        # 云形状由多个圆弧组成
        center_x, center_y = 0, 0
        w, h = self.width, self.height
        
        # 定义云的圆弧半径
        r1 = min(w, h) / 4
        r2 = min(w, h) / 5
        r3 = min(w, h) / 6
        
        # 定义圆弧中心点
        points = [
            (center_x - w/4, center_y - h/4, r1),  # 左上
            (center_x + w/4, center_y - h/4, r2),  # 右上
            (center_x + w/3, center_y, r2),        # 右中
            (center_x + w/4, center_y + h/4, r1),  # 右下
            (center_x - w/4, center_y + h/4, r2),  # 左下
            (center_x - w/3, center_y, r3)         # 左中
        ]
        
        # 绘制路径
        for i, (x, y, r) in enumerate(points):
            if i == 0:
                path.addEllipse(QPointF(x, y), r, r)
            else:
                path.addEllipse(QPointF(x, y), r, r)
    
    def paint(self, painter, option, widget):
        """绘制节点"""
        # 设置画笔和画刷
        pen = QPen(Qt.black)
        pen.setWidth(2)
        if self.isSelected():
            pen.setColor(Qt.red)
        
        # 设置渐变画刷来增强视觉效果
        gradient = QLinearGradient(0, -self.height/2, 0, self.height/2)
        gradient.setColorAt(0, self.color.lighter(110))
        gradient.setColorAt(1, self.color)
        brush = QBrush(gradient)
        
        painter.setPen(pen)
        painter.setBrush(brush)
        
        # 根据形状绘制
        if self.shape_type == "rounded_rect":
            rect = QRectF(-self.width/2, -self.height/2, self.width, self.height)
            painter.drawRoundedRect(rect, 10, 10)  # 圆角矩形
        elif self.shape_type == "cloud":
            # 云形状由多个圆弧组成
            path = QPainterPath()
            self._draw_cloud_path(path)
            painter.drawPath(path)
        else:
            # 默认使用矩形
            painter.drawRect(QRectF(-self.width/2, -self.height/2, self.width, self.height))
        
        # 绘制文本
        font = QFont()
        font.setPointSize(10)
        if self.node_type == "中心主题":
            font.setBold(True)
            font.setPointSize(12)
        
        painter.setFont(font)
        painter.setPen(Qt.black)
        text_rect = QRectF(-self.width/2 + 10, -self.height/2 + 5, self.width - 20, self.height - 10)
        painter.drawText(text_rect, Qt.AlignCenter | Qt.TextWordWrap, self.node_text)
    
    def itemChange(self, change, value):
        """处理节点变化，主要用于更新连接线"""
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            # 更新所有连接到此节点的连接线
            for conn in self.connections:
                conn.updatePosition()
        return super().itemChange(change, value)
    
    def contextMenuEvent(self, event):
        """右键菜单"""
        menu = QMenu()
        edit_action = menu.addAction("编辑")
        edit_action.triggered.connect(self.editNode)
        
        add_child_action = menu.addAction("添加子节点")
        add_child_action.triggered.connect(self.addChildNode)
        
        delete_action = menu.addAction("删除")
        delete_action.triggered.connect(self.deleteNode)
        
        color_action = menu.addAction("更改颜色")
        color_action.triggered.connect(self.changeColor)
        
        # 添加折叠/展开子菜单
        if self.get_child_nodes():
            menu.addSeparator()
            fold_menu = menu.addMenu("折叠/展开")
            
            # 检查当前节点状态
            is_folded = getattr(self, 'is_folded', False)
            all_children = self.getAllChildNodes()
            direct_children = self.get_child_nodes()
            
            if is_folded:
                # 如果已经折叠，显示展开选项
                expand_action = fold_menu.addAction("展开当前层级")
                expand_action.triggered.connect(lambda: self.toggleFold())
                
                if len(all_children) > len(direct_children):
                    expand_all_action = fold_menu.addAction("展开所有层级")
                    expand_all_action.triggered.connect(lambda: self.expandAllLevels())
            else:
                # 如果未折叠，显示折叠选项
                fold_action = fold_menu.addAction("折叠当前层级")
                fold_action.triggered.connect(lambda: self.toggleFold())
                
                if len(all_children) > len(direct_children):
                    fold_all_action = fold_menu.addAction("折叠所有层级")
                    fold_all_action.triggered.connect(lambda: self.foldAllLevels())
        
        menu.addSeparator()
        
        # 添加图片相关菜单
        add_image_action = menu.addAction("添加图片")
        add_image_action.triggered.connect(lambda: self.addImage())
        
        remove_image_action = menu.addAction("移除图片")
        remove_image_action.triggered.connect(lambda: self.removeImage())
        
        # 如果节点没有图片，禁用移除图片选项
        if not hasattr(self, 'image') or self.image is None:
            remove_image_action.setEnabled(False)
        
        menu.addSeparator()
        
        # 添加链接相关菜单
        add_link_action = menu.addAction("添加链接")
        add_link_action.triggered.connect(lambda: self.addLink())
        
        remove_link_action = menu.addAction("移除链接")
        remove_link_action.triggered.connect(lambda: self.removeLink())
        
        # 如果节点没有链接，禁用移除链接选项
        if not hasattr(self, 'link') or not self.link:
            remove_link_action.setEnabled(False)
        
        # 执行菜单
        menu.exec_(event.screenPos())
    
    def addChildNode(self):
        """添加子节点"""
        # 直接使用views中存储的main_window引用
        main_window = self.scene().views()[0].main_window
        
        if main_window:
            # 调用主窗口的addNode方法，并传入当前节点作为父节点
            main_window.addNode(self)
        else:
            QMessageBox.warning(None, "错误", "无法找到主窗口实例")
    
    def editNode(self):
        """编辑节点文本"""
        text, ok = QInputDialog.getText(None, "编辑节点", "节点文本:", 
                                       text=self.node_text)
        if ok and text:
            self.node_text = text
            self.update()
    
    def deleteNode(self):
        """删除节点及其连接线和子节点"""
        # 显示确认对话框
        reply = QMessageBox.question(
            None, "确认删除", 
            f"确定要删除节点 '{self.node_text}' 及其所有子节点吗？", 
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # 首先找出所有需要删除的节点（当前节点及其所有子节点）
        nodes_to_delete = self.getAllChildNodes()
        
        # 在控制台打印节点信息，便于调试
        print(f"Deleting node: {self.node_text}")
        print(f"Child nodes to delete: {[node.node_text for node in nodes_to_delete]}")
        
        # 先删除所有连接线
        scene = self.scene()
        if scene:
            # 删除所有相关连接线
            for item in list(scene.items()):
                if isinstance(item, FlowchartConnection):
                    if item.start_node == self or item.end_node == self or \
                       item.start_node in nodes_to_delete or item.end_node in nodes_to_delete:
                        scene.removeItem(item)
            
            # 删除所有子节点
            for node in nodes_to_delete:
                if node in scene.items():
                    scene.removeItem(node)
            
            # 最后删除当前节点
            scene.removeItem(self)
    
    def getAllChildNodes(self):
        """获取所有子节点（递归）"""
        child_nodes = []
        scene = self.scene()
        
        if not scene:
            return child_nodes
        
        # 找出直接子节点
        for item in scene.items():
            if isinstance(item, FlowchartConnection) and item.start_node == self:
                child_node = item.end_node
                child_nodes.append(child_node)
                
                # 递归获取子节点的子节点
                child_nodes.extend(child_node.getAllChildNodes())
        
        return child_nodes
    
    def mouseDoubleClickEvent(self, event):
        """双击编辑节点或折叠/展开"""
        # 如果按住Ctrl键，则折叠/展开节点，否则编辑节点
        if event.modifiers() & Qt.ControlModifier:
            # 使用扩展模块的折叠/展开功能
            advanced.extend_node_mouse_double_click_event(self, event, self.scene().views()[0].main_window)
        else:
            self.editNode()
    
    def changeColor(self):
        """更改节点颜色"""
        color = QColorDialog.getColor(self.color, None, "选择节点颜色")
        if color.isValid():
            self.color = color
            self.update()
            self.scene().views()[0].main_window.setModified(True)
    
    def get_child_nodes(self):
        """获取直接子节点"""
        child_nodes = []
        scene = self.scene()
        
        if not scene:
            return child_nodes
        
        for item in scene.items():
            if isinstance(item, FlowchartConnection) and item.start_node == self:
                child_node = item.end_node
                child_nodes.append(child_node)
        
        return child_nodes
    
    def toggleFold(self):
        """切换节点的折叠/展开状态"""
        main_window = self.scene().views()[0].main_window
        if hasattr(main_window, 'shortcut_manager'):
            # 通过快捷键管理器来切换折叠状态
            main_window.shortcut_manager._toggle_fold_node(self)
    
    def foldAllLevels(self):
        """折叠所有层级的子节点"""
        main_window = self.scene().views()[0].main_window
        if hasattr(main_window, 'shortcut_manager'):
            # 使用快捷键管理器的多层折叠方法
            main_window.shortcut_manager._fold_all_levels(self)
    
    def expandAllLevels(self):
        """展开所有层级的子节点"""
        # 获取所有子节点（包括子节点的子节点）
        all_descendants = self.getAllChildNodes()
        
        # 将所有子节点设置为可见，并取消折叠状态
        for child in all_descendants:
            child.setVisible(True)
            if hasattr(child, 'is_folded'):
                child.is_folded = False
        
        # 还需要将当前节点的折叠状态取消
        self.is_folded = False
        
        # 更新场景
        self.scene().update()
        
        # 标记为已修改
        self.scene().views()[0].main_window.setModified(True)
    
    def addImage(self):
        """添加图片到节点"""
        main_window = self.scene().views()[0].main_window
        file_path, _ = QFileDialog.getOpenFileName(
            main_window, 
            "选择图片", 
            "", 
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path:
            try:
                self.image = QPixmap(file_path)
                self.update()
                main_window.setModified(True)
            except Exception as e:
                QMessageBox.critical(main_window, "错误", f"无法加载图片: {str(e)}")
    
    def removeImage(self):
        """从节点移除图片"""
        if hasattr(self, 'image') and self.image is not None:
            self.image = None
            self.update()
            self.scene().views()[0].main_window.setModified(True)
    
    def addLink(self):
        """添加链接到节点"""
        main_window = self.scene().views()[0].main_window
        link, ok = QInputDialog.getText(
            main_window, 
            "添加链接", 
            "请输入URL链接:",
            text=getattr(self, 'link', '')
        )
        
        if ok and link:
            self.link = link
            self.update()
            main_window.setModified(True)
    
    def removeLink(self):
        """从节点移除链接"""
        if hasattr(self, 'link') and self.link:
            self.link = None
            self.update()
            self.scene().views()[0].main_window.setModified(True)

class FlowchartConnection(QGraphicsPathItem):
    """思维导图连接线"""
    
    def __init__(self, start_node, end_node, parent=None):
        super().__init__(parent)
        self.start_node = start_node
        self.end_node = end_node
        
        # 将此连接添加到两个节点的连接列表中
        self.start_node.connections.append(self)
        self.end_node.connections.append(self)
        
        # 生成随机颜色，但保持较浅的色调
        hue = (hash(str(start_node) + str(end_node)) % 360) / 360.0
        self.color = QColor.fromHsvF(hue, 0.5, 0.9)
        
        # 设置线条样式
        pen = QPen(self.color)
        pen.setWidth(2)
        self.setPen(pen)
        
        # 初始化连接线位置
        self.updatePosition()
        
        # 设置可选择
        self.setFlag(QGraphicsItem.ItemIsSelectable)
    
    def updatePosition(self):
        """更新连接线位置"""
        # 获取起点和终点的中心位置
        start_pos = self.start_node.scenePos()
        end_pos = self.end_node.scenePos()
        
        # 创建路径
        path = QPainterPath()
        
        # 计算起点和终点之间的距离和方向
        line = QLineF(start_pos, end_pos)
        length = line.length()
        
        # 确定控制点的偏移量，让曲线更自然
        offset_factor = min(length / 200.0, 1.0) * 50  # 根据距离调整控制点偏移
        
        # 计算控制点的位置
        # 如果是水平或垂直布局，使用不同的控制点策略
        dx = end_pos.x() - start_pos.x()
        dy = end_pos.y() - start_pos.y()
        
        # 判断是否是水平或垂直布局
        is_horizontal = abs(dx) > abs(dy)
        
        if is_horizontal:
            # 水平布局，控制点在x方向上偏移
            ctrl1 = QPointF(start_pos.x() + dx * 0.5, start_pos.y())
            ctrl2 = QPointF(end_pos.x() - dx * 0.1, end_pos.y())
        else:
            # 垂直布局，控制点在y方向上偏移
            ctrl1 = QPointF(start_pos.x(), start_pos.y() + dy * 0.5)
            ctrl2 = QPointF(end_pos.x(), end_pos.y() - dy * 0.1)
        
        # 绘制起点
        path.moveTo(start_pos)
        
        # 绘制三次贝塞尔曲线
        path.cubicTo(ctrl1, ctrl2, end_pos)
        
        # 设置路径
        self.setPath(path)
        
        # 存储终点信息用于绘制箭头
        self.end_point = end_pos
        
        # 计算箭头方向（基于终点附近的曲线切线）
        # 这里简化处理，使用控制点到终点的方向
        self.angle = math.atan2(end_pos.y() - ctrl2.y(), end_pos.x() - ctrl2.x())
    
    def paint(self, painter, option, widget):
        """绘制连接线，包括箭头"""
        # 设置画笔
        pen = self.pen()
        if self.isSelected():
            pen.setColor(Qt.red)
            pen.setWidth(3)
        painter.setPen(pen)
        
        # 绘制路径
        painter.drawPath(self.path())
        
        # 绘制箭头
        self.drawArrow(painter)
    
    def drawArrow(self, painter):
        """绘制箭头"""
        if not hasattr(self, 'end_point') or not hasattr(self, 'angle'):
            return
            
        # 箭头大小和形状
        arrow_size = 12
        arrow_angle = math.pi / 6  # 30度
        
        # 计算箭头的三个点
        tip = self.end_point
        arrow_p1 = tip - QPointF(math.cos(self.angle) * arrow_size, 
                               math.sin(self.angle) * arrow_size)
        arrow_p2 = arrow_p1 - QPointF(math.cos(self.angle + arrow_angle) * arrow_size,
                                    math.sin(self.angle + arrow_angle) * arrow_size)
        arrow_p3 = arrow_p1 - QPointF(math.cos(self.angle - arrow_angle) * arrow_size,
                                    math.sin(self.angle - arrow_angle) * arrow_size)
        
        # 创建箭头多边形
        arrow = QPolygonF([tip, arrow_p2, arrow_p3])
        
        # 设置画刷和画笔
        if self.isSelected():
            painter.setBrush(Qt.red)
            painter.setPen(QPen(Qt.red, 2))
        else:
            painter.setBrush(self.color)
            painter.setPen(QPen(self.color.darker(120), 1.5))
            
        # 绘制箭头
        painter.drawPolygon(arrow)
    
    def contextMenuEvent(self, event):
        """右键菜单"""
        menu = QMenu()
        delete_action = menu.addAction("删除")
        color_action = menu.addAction("更改颜色")
        
        action = menu.exec_(event.screenPos())
        
        if action == delete_action:
            self.deleteConnection()
        elif action == color_action:
            self.changeColor()
    
    def changeColor(self):
        """更改连接线颜色"""
        color = QColorDialog.getColor(self.color, None, "选择连接线颜色")
        if color.isValid():
            self.color = color
            pen = self.pen()
            pen.setColor(color)
            self.setPen(pen)
            self.update()
    
    def deleteConnection(self):
        """删除连接线"""
        # 从节点的连接列表中移除此连接
        if hasattr(self, 'start_node') and self in self.start_node.connections:
            self.start_node.connections.remove(self)
        if hasattr(self, 'end_node') and self in self.end_node.connections:
            self.end_node.connections.remove(self)
        
        # 从场景中移除
        scene = self.scene()
        if scene is not None:
            scene.removeItem(self)

class NodePropertiesDialog(QDialog):
    """节点属性对话框"""
    
    def __init__(self, node_type="主要分支", text="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("节点属性")
        self.setMinimumWidth(350)
        
        # 创建表单布局
        layout = QFormLayout(self)
        layout.setSpacing(15)
        
        # 节点类型选择
        self.type_combo = QComboBox()
        self.type_combo.setMinimumHeight(30)
        for node_type_name in NODE_TYPES.keys():
            self.type_combo.addItem(node_type_name)
        self.type_combo.setCurrentText(node_type)
        layout.addRow("节点类型:", self.type_combo)
        
        # 节点文本输入（使用文本区域而不是单行输入，支持多行文本）
        self.text_edit = QLineEdit(text)
        self.text_edit.setMinimumHeight(30)
        layout.addRow("节点文本:", self.text_edit)
        
        # 颜色选择按钮
        self.color_button = QPushButton("选择颜色")
        self.color_button.setMinimumHeight(30)
        self.color = NODE_TYPES[node_type]["color"]
        self.update_color_button()
        self.color_button.clicked.connect(self.choose_color)
        layout.addRow("节点颜色:", self.color_button)
        
        # 按钮
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)
        
        # 连接类型选择事件
        self.type_combo.currentTextChanged.connect(self.update_default_color)
    
    def update_default_color(self, node_type):
        """更新默认颜色"""
        self.color = NODE_TYPES[node_type]["color"]
        self.update_color_button()
    
    def choose_color(self):
        """选择颜色"""
        color = QColorDialog.getColor(self.color, self, "选择节点颜色")
        if color.isValid():
            self.color = color
            self.update_color_button()
    
    def update_color_button(self):
        """更新颜色按钮样式"""
        self.color_button.setStyleSheet(
            f"background-color: {self.color.name()}; "
            f"color: {'black' if self.color.lightness() > 128 else 'white'};"
            f"padding: 5px;"
        )
    
    def getNodeProperties(self):
        """获取节点属性"""
        return {
            "node_type": self.type_combo.currentText(),
            "text": self.text_edit.text(),
            "color": self.color
        }

class FlowchartView(QGraphicsView):
    """思维导图视图"""
    
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        
        # 连接线绘制状态
        self.line_drawing = False
        self.temp_line = None
        self.start_node = None
        
        # 设置背景颜色
        self.setBackgroundBrush(QBrush(QColor(240, 240, 240)))
        
        # 获取主窗口引用
        self.main_window = None
        parent = self.parent()
        while parent is not None:
            if isinstance(parent, FlowchartEditor):
                self.main_window = parent
                break
            parent = parent.parent()
    
    def contextMenuEvent(self, event):
        """右键菜单事件"""
        # 检查点击位置是否有节点
        item = self.itemAt(event.pos())
        
        # 如果点击在空白处
        if not item:
            # 检查场景中是否有中心主题
            has_center_node = False
            has_nodes = False
            
            for scene_item in self.scene().items():
                if isinstance(scene_item, FlowchartNode):
                    has_nodes = True
                    if scene_item.node_type == "中心主题":
                        has_center_node = True
                        break
            
            # 如果没有任何节点，则显示创建中心主题的选项
            if not has_nodes:
                menu = QMenu()
                create_center_action = menu.addAction("创建中心主题")
                
                action = menu.exec_(event.globalPos())
                
                if action == create_center_action and self.main_window:
                    # 获取鼠标点击的场景坐标
                    scene_pos = self.mapToScene(event.pos())
                    self.main_window.addCenterNodeAt(scene_pos)
                
                event.accept()
                return
            # 如果没有中心主题，则显示创建中心主题的选项
            elif not has_center_node:
                menu = QMenu()
                create_center_action = menu.addAction("创建中心主题")
                
                action = menu.exec_(event.globalPos())
                
                if action == create_center_action and self.main_window:
                    # 获取鼠标点击的场景坐标
                    scene_pos = self.mapToScene(event.pos())
                    self.main_window.addCenterNodeAt(scene_pos)
                
                event.accept()
                return
            # 如果已经有中心主题，则不显示创建节点的选项
            # 直接通过这里，不显示任何菜单
        
        # 如果点击在节点上，让节点处理右键菜单
        super().contextMenuEvent(event)
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton and event.modifiers() & Qt.ControlModifier:
            # 按住Ctrl+左键开始绘制连接线
            item = self.itemAt(event.pos())
            if isinstance(item, FlowchartNode):
                self.line_drawing = True
                self.start_node = item
                start_pos = item.scenePos()
                
                # 创建临时线
                self.temp_line = QGraphicsLineItem(
                    QLineF(start_pos, self.mapToScene(event.pos())))
                pen = QPen(Qt.black, 2, Qt.DashLine)
                self.temp_line.setPen(pen)
                self.scene().addItem(self.temp_line)
                
                event.accept()
                return
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.line_drawing and self.temp_line:
            # 更新临时线的终点
            new_line = QLineF(self.temp_line.line().p1(), 
                             self.mapToScene(event.pos()))
            self.temp_line.setLine(new_line)
            event.accept()
            return
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton and self.line_drawing:
            # 结束连接线绘制
            end_item = self.itemAt(event.pos())
            
            # 移除临时线
            self.scene().removeItem(self.temp_line)
            self.temp_line = None
            
            # 如果释放在另一个节点上，创建连接
            if isinstance(end_item, FlowchartNode) and end_item != self.start_node:
                connection = FlowchartConnection(self.start_node, end_item)
                self.scene().addItem(connection)
                
                # 标记为已修改
                if self.main_window:
                    self.main_window.setModified(True)
            
            self.line_drawing = False
            self.start_node = None
            event.accept()
            return
        
        super().mouseReleaseEvent(event)
    
    def wheelEvent(self, event):
        """鼠标滚轮事件 - 用于缩放"""
        zoom_factor = 1.1
        
        if event.angleDelta().y() > 0:
            # 放大
            self.scale(zoom_factor, zoom_factor)
        else:
            # 缩小
            self.scale(1.0 / zoom_factor, 1.0 / zoom_factor)

class WelcomeWidget(QWidget):
    """欢迎界面小部件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # 设置背景颜色
        self.setStyleSheet("background-color: #f5f5f7;")
        
        # 标题标签
        title_label = QLabel("思维导图编辑器")
        title_label.setStyleSheet("font-size: 28pt; font-weight: bold; margin-bottom: 20px; color: #333;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 副标题
        subtitle_label = QLabel("创建美观的思维导图，组织您的想法")
        subtitle_label.setStyleSheet("font-size: 14pt; color: #666; margin-bottom: 20px;")
        subtitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle_label)
        
        # 示例图片区域
        example_container = QWidget()
        example_container.setStyleSheet("background-color: white; border-radius: 10px; padding: 15px;")
        example_layout = QVBoxLayout(example_container)
        
        # 示例标题
        example_title = QLabel("示例思维导图")
        example_title.setStyleSheet("font-size: 12pt; font-weight: bold; color: #444;")
        example_title.setAlignment(Qt.AlignCenter)
        example_layout.addWidget(example_title)
        
        # 示例图片
        example_image = QLabel()
        
        # 创建一个示例思维导图图片
        pixmap = self.create_example_mindmap()
        example_image.setPixmap(pixmap)
        example_image.setAlignment(Qt.AlignCenter)
        example_image.setMinimumHeight(250)
        example_layout.addWidget(example_image)
        
        layout.addWidget(example_container)
        
        # 按钮容器
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(30)
        
        # 新建按钮
        new_button = QPushButton("新建思维导图")
        new_button.setMinimumSize(180, 60)
        new_button.setStyleSheet(
            "font-size: 14pt; font-weight: bold; "
            "background-color: #0078d7; color: white; "
            "border-radius: 5px; padding: 10px;"
        )
        new_button.clicked.connect(lambda: self.parent.newFlowchart())
        button_layout.addWidget(new_button)
        
        # 打开按钮
        open_button = QPushButton("打开思维导图")
        open_button.setMinimumSize(180, 60)
        open_button.setStyleSheet(
            "font-size: 14pt; "
            "background-color: #f0f0f0; color: #333; "
            "border-radius: 5px; border: 1px solid #ddd; padding: 10px;"
        )
        open_button.clicked.connect(lambda: self.parent.openFlowchart())
        button_layout.addWidget(open_button)
        
        layout.addWidget(button_container)
        
        # 提示信息
        tips_container = QWidget()
        tips_container.setStyleSheet("background-color: #f0f8ff; border-radius: 5px; padding: 10px;")
        tips_layout = QVBoxLayout(tips_container)
        
        tips_title = QLabel("使用提示")
        tips_title.setStyleSheet("font-weight: bold; color: #0078d7;")
        tips_layout.addWidget(tips_title)
        
        tips = [
            "• 创建思维导图后，可以右键点击节点添加子节点",
            "• 按住 Ctrl+左键 从一个节点拖动到另一个节点可创建连接",
            "• 使用鼠标滚轮可以放大或缩小视图"
        ]
        
        for tip in tips:
            tip_label = QLabel(tip)
            tip_label.setStyleSheet("color: #444; padding: 2px;")
            tips_layout.addWidget(tip_label)
        
        layout.addWidget(tips_container)
    
    def create_example_mindmap(self):
        """创建示例思维导图图片"""
        # 创建一个空白图片
        pixmap = QPixmap(600, 250)
        pixmap.fill(Qt.white)
        
        # 创建画布
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 定义颜色
        center_color = QColor(0, 176, 151)  # 中心节点颜色
        branch1_color = QColor(135, 206, 250)  # 分支1颜色
        branch2_color = QColor(255, 182, 193)  # 分支2颜色
        branch3_color = QColor(211, 211, 211)  # 分支3颜色
        
        # 定义位置
        center_pos = QPointF(300, 125)
        branch1_pos = QPointF(150, 60)
        branch2_pos = QPointF(450, 70)
        branch3_pos = QPointF(200, 190)
        branch4_pos = QPointF(400, 180)
        
        # 绘制连接线
        pen = QPen(QColor(100, 100, 100, 180))
        pen.setWidth(2)
        painter.setPen(pen)
        
        # 绘制曲线连接
        path1 = QPainterPath()
        path1.moveTo(center_pos)
        path1.cubicTo(center_pos.x() - 50, center_pos.y() - 30, 
                     branch1_pos.x() + 50, branch1_pos.y() + 30, 
                     branch1_pos.x() + 40, branch1_pos.y())
        painter.drawPath(path1)
        
        path2 = QPainterPath()
        path2.moveTo(center_pos)
        path2.cubicTo(center_pos.x() + 50, center_pos.y() - 30, 
                     branch2_pos.x() - 50, branch2_pos.y() + 30, 
                     branch2_pos.x() - 40, branch2_pos.y())
        painter.drawPath(path2)
        
        path3 = QPainterPath()
        path3.moveTo(center_pos)
        path3.cubicTo(center_pos.x() - 50, center_pos.y() + 30, 
                     branch3_pos.x() + 30, branch3_pos.y() - 30, 
                     branch3_pos.x() + 40, branch3_pos.y())
        painter.drawPath(path3)
        
        path4 = QPainterPath()
        path4.moveTo(center_pos)
        path4.cubicTo(center_pos.x() + 50, center_pos.y() + 30, 
                     branch4_pos.x() - 30, branch4_pos.y() - 30, 
                     branch4_pos.x() - 40, branch4_pos.y())
        painter.drawPath(path4)
        
        # 绘制节点
        # 中心节点
        self.draw_rounded_rect(painter, center_pos, 100, 40, center_color, "中心主题")
        
        # 分支节点
        self.draw_rounded_rect(painter, branch1_pos, 80, 30, branch1_color, "主要分支1")
        self.draw_rounded_rect(painter, branch2_pos, 80, 30, branch2_color, "主要分支2")
        self.draw_rounded_rect(painter, branch3_pos, 80, 30, branch3_color, "次要分支1")
        self.draw_rounded_rect(painter, branch4_pos, 80, 30, branch3_color, "次要分支2")
        
        painter.end()
        return pixmap
    
    def draw_rounded_rect(self, painter, center, width, height, color, text):
        """绘制圆角矩形节点"""
        # 设置渐变画刷
        gradient = QLinearGradient(center.x(), center.y() - height/2, center.x(), center.y() + height/2)
        gradient.setColorAt(0, color.lighter(110))
        gradient.setColorAt(1, color)
        
        # 绘制圆角矩形
        rect = QRectF(center.x() - width/2, center.y() - height/2, width, height)
        painter.setPen(QPen(color.darker(120)))
        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(rect, 10, 10)
        
        # 绘制文字
        painter.setPen(Qt.black)
        font = painter.font()
        font.setBold(True if "\u4e2d\u5fc3" in text else False)
        font.setPointSize(10 if "\u4e2d\u5fc3" in text else 9)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, text)

class FlowchartEditor(QMainWindow):
    """思维导图编辑器主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("思维导图编辑器")
        self.setMinimumSize(900, 700)
        
        # 创建中央部件堆栈
        self.central_stack = QStackedWidget()
        self.setCentralWidget(self.central_stack)
        
        # 创建欢迎界面
        self.welcome_widget = WelcomeWidget(self)
        self.central_stack.addWidget(self.welcome_widget)
        
        # 创建场景和视图
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(-2500, -2500, 5000, 5000)
        self.view = FlowchartView(self.scene, self)
        self.view.main_window = self  # 直接设置main_window引用
        self.central_stack.addWidget(self.view)
        
        # 默认显示欢迎界面
        self.central_stack.setCurrentIndex(0)
        
        # 当前文件路径
        self.current_file = None
        
        # 修改状态标记
        self.is_modified = False
        
        # 操作历史记录
        self.history = []
        self.history_index = -1
        self.max_history = 20  # 最大历史记录数
        
        # 设置关闭事件处理
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        
        # 导出设置
        self.export_margin = 20  # 导出时的边距
        
        # 初始化导出器
        self.exporter = export.FlowchartExporter(self)
        
        # 初始化键盘快捷键管理器
        self.shortcut_manager = advanced.KeyboardShortcutManager(self)
        
        # 创建工具栏
        self.createToolBar()
        
        # 创建状态栏
        self.statusBar().showMessage("准备就绪")
    
    def closeEvent(self, event):
        """关闭窗口事件处理"""
        if self.is_modified:
            reply = QMessageBox.question(
                self, "保存确认", 
                "当前思维导图已被修改，是否保存？",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                if self.saveFlowchart():
                    event.accept()
                else:
                    event.ignore()
            elif reply == QMessageBox.Cancel:
                event.ignore()
        
        # 如果未修改或选择不保存，直接关闭
        # event.accept() 在这里是默认的
    
    def setModified(self, modified=True):
        """设置修改状态"""
        self.is_modified = modified
        
        # 更新窗口标题显示修改状态
        title = self.windowTitle()
        if modified and not title.endswith('*'):
            self.setWindowTitle(f"{title} *")
        elif not modified and title.endswith(' *'):
            self.setWindowTitle(title[:-2])

    def auto_layout(self):
        """应用自动布局算法"""
        auto_layout = advanced.AutoLayoutAlgorithm(self)
        auto_layout.apply_layout()

    def toggle_fold_selected(self):
        """折叠/展开选中节点"""
        if hasattr(self, 'shortcut_manager'):
            self.shortcut_manager.toggle_fold_selected()

    def createToolBar(self):
        """创建工具栏"""
        toolbar = QToolBar(self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # 返回主页按钮
        home_button = QPushButton("返回主页")
        home_button.setToolTip("返回主页面")
        home_button.clicked.connect(self.showWelcomePage)
        toolbar.addWidget(home_button)
        
        toolbar.addSeparator()
        
        # 添加节点按钮
        add_node_button = QPushButton("添加节点")
        add_node_button.setToolTip("添加新节点")
        add_node_button.clicked.connect(self.addNode)
        toolbar.addWidget(add_node_button)
        
        # 添加中心主题按钮
        add_center_button = QPushButton("添加中心主题")
        add_center_button.setToolTip("添加新的中心主题")
        add_center_button.clicked.connect(lambda: self.addNode(node_type="中心主题"))
        toolbar.addWidget(add_center_button)
        
        # 删除选中项按钮
        delete_button = QPushButton("删除选中")
        delete_button.setToolTip("删除选中的节点或连接")
        delete_button.clicked.connect(self.deleteSelected)
        toolbar.addWidget(delete_button)
        
        # 线条样式按钮
        line_style_button = QPushButton("线条样式")
        line_style_button.setToolTip("设置选中连接线的样式")
        line_style_button.clicked.connect(self.setLineStyle)
        toolbar.addWidget(line_style_button)
        
        toolbar.addSeparator()
        
        # 文件操作按钮
        new_button = QPushButton("新建")
        new_button.setToolTip("创建新的思维导图")
        new_button.clicked.connect(self.newFlowchart)
        toolbar.addWidget(new_button)
        
        open_button = QPushButton("打开")
        open_button.setToolTip("打开现有思维导图")
        open_button.clicked.connect(self.openFlowchart)
        toolbar.addWidget(open_button)
        
        save_button = QPushButton("保存")
        save_button.setToolTip("保存当前思维导图")
        save_button.clicked.connect(lambda: save_functions.save_flowchart(self))
        toolbar.addWidget(save_button)
        
        # 另存为按钮
        save_as_button = QPushButton("另存为")
        save_as_button.setToolTip("将当前思维导图另存为新文件")
        save_as_button.clicked.connect(lambda: save_functions.save_flowchart_as(self))
        toolbar.addWidget(save_as_button)
        
        toolbar.addSeparator()
        
        # 导出按钮
        export_button = QPushButton("导出")
        export_button.setToolTip("导出为图片或PDF")
        export_button.clicked.connect(self.exporter.export_flowchart)
        toolbar.addWidget(export_button)
        
        # 自动布局按钮
        auto_layout_button = QPushButton("自动布局")
        auto_layout_button.setToolTip("应用自动布局算法")
        auto_layout_button.clicked.connect(self.auto_layout)
        toolbar.addWidget(auto_layout_button)
        
        # 折叠/展开按钮
        fold_button = QPushButton("折叠/展开")
        fold_button.setToolTip("折叠或展开选中节点")
        fold_button.clicked.connect(self.toggle_fold_selected)
        toolbar.addWidget(fold_button)
        
        toolbar.addSeparator()
        
        # 操作历史
        undo_button = QPushButton("撤销")
        undo_button.setToolTip("撤销上一步操作")
        undo_button.clicked.connect(self.undo)
        toolbar.addWidget(undo_button)
        
        redo_button = QPushButton("重做")
        redo_button.setToolTip("重做上一步操作")
        redo_button.clicked.connect(self.redo)
        toolbar.addWidget(redo_button)
        
        toolbar.addSeparator()
        
        # 帮助信息
        help_label = QLabel("提示: Ctrl+左键拖动可创建连接线 | 右键点击空白处创建节点")
        toolbar.addWidget(help_label)
    
    def addNode(self, parent_node=None, node_type=None, pos=None):
        """添加新节点
        
        Args:
            parent_node: 父节点，如果指定则自动创建连接
            node_type: 节点类型，如果指定则使用该类型
            pos: 节点位置，如果指定则使用该位置
        """
        # 如果当前不在编辑视图，切换到编辑视图
        if self.central_stack.currentIndex() != 1:
            # 如果有未保存的更改，先提示保存
            if self.is_modified and self.scene.items():
                reply = QMessageBox.question(
                    self, "保存确认", 
                    "当前思维导图已被修改，是否保存？",
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                    QMessageBox.Save
                )
                
                if reply == QMessageBox.Save:
                    if not self.saveFlowchart():
                        return None  # 保存失败，取消操作
                elif reply == QMessageBox.Cancel:
                    return None  # 取消操作
            
            # 创建新的思维导图
            self.newFlowchart(ask_save=False)  # 不再次提示保存
        
        # 如果是空场景，默认创建中心主题
        if not self.scene.items() and parent_node is None and node_type is None:
            default_type = "中心主题"
        elif node_type:
            default_type = node_type
        else:
            default_type = "主要分支" if parent_node and parent_node.node_type == "中心主题" else "次要分支"
        
        dialog = NodePropertiesDialog(node_type=default_type, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            props = dialog.getNodeProperties()
            
            # 计算新节点的位置
            if pos:
                # 如果指定了位置，直接使用
                node_pos = pos
            elif parent_node:
                # 如果有父节点，则基于父节点位置计算
                parent_pos = parent_node.scenePos()
                
                # 计算该父节点已有的子节点数量
                child_count = sum(1 for item in self.scene.items() 
                                 if isinstance(item, FlowchartConnection) and item.start_node == parent_node)
                
                # 根据子节点数量确定位置
                if parent_node.node_type == "中心主题":
                    # 中心节点的子节点呈环形分布
                    radius = 200
                    angle = (child_count * 40) % 360  # 每个子节点间隔40度
                    angle_rad = math.radians(angle)
                    x = parent_pos.x() + radius * math.cos(angle_rad)
                    y = parent_pos.y() + radius * math.sin(angle_rad)
                    node_pos = QPointF(x, y)
                else:
                    # 其他节点的子节点呈垂直分布
                    x_offset = 180
                    y_offset = 100 + child_count * 80
                    
                    # 根据父节点的位置确定子节点应该在左边还是右边
                    if parent_pos.x() < 0:
                        x = parent_pos.x() - x_offset
                    else:
                        x = parent_pos.x() + x_offset
                    
                    y = parent_pos.y() + (child_count % 2 * 2 - 1) * y_offset
                    node_pos = QPointF(x, y)
            else:
                # 如果没有父节点，则使用默认位置
                node_pos = QPointF(0, 0) if props["node_type"] == "中心主题" else QPointF(250, 250)
            
            # 创建新节点并添加到场景
            node = FlowchartNode(props["node_type"], props["text"], node_pos)
            
            # 如果指定了自定义颜色，则使用自定义颜色
            if "color" in props and props["color"] != NODE_TYPES[props["node_type"]]["color"]:
                node.color = props["color"]
                
            self.scene.addItem(node)
            
            # 如果有父节点，创建连接
            if parent_node:
                connection = FlowchartConnection(parent_node, node)
                self.scene.addItem(connection)
            
            # 如果是第一个节点，将视图居中
            if len(self.scene.items()) <= 2:  # 只有一个节点或一个节点+一个连接
                self.view.centerOn(node)
            
            # 标记为已修改
            self.setModified(True)
            
            # 添加到操作历史
            self.addHistory({
                "type": "add_node",
                "node_id": id(node),
                "node_type": props["node_type"],
                "node_text": props["text"],
                "node_pos": (node_pos.x(), node_pos.y()),
                "parent_node_id": id(parent_node) if parent_node else None
            })
            
            self.statusBar().showMessage(f"已添加 {props['node_type']} 节点")
            
            # 返回创建的节点，便于连续添加子节点
            return node
        
        return None
    
    def addNodeAt(self, pos):
        """在指定位置添加节点"""
        return self.addNode(pos=pos)
    
    def addCenterNodeAt(self, pos):
        """在指定位置添加中心主题节点"""
        return self.addNode(node_type="中心主题", pos=pos)
    
    def deleteSelected(self):
        """删除选中的项目"""
        selected_items = self.scene.selectedItems()
        if not selected_items:
            return
        
        # 记录删除操作历史
        history_data = {
            "type": "delete_items",
            "items": []
        }
        
        for item in selected_items:
            if isinstance(item, FlowchartNode):
                # 记录节点信息
                node_data = {
                    "item_type": "node",
                    "node_id": id(item),
                    "node_type": item.node_type,
                    "node_text": item.node_text,
                    "node_pos": (item.scenePos().x(), item.scenePos().y()),
                    "node_color": item.color.name(),
                    "connections": []
                }
                
                # 记录连接信息
                for conn in item.connections:
                    if conn in self.scene.items():  # 确保连接还存在
                        conn_data = {
                            "start_node_id": id(conn.start_node),
                            "end_node_id": id(conn.end_node),
                            "color": conn.color.name()
                        }
                        node_data["connections"].append(conn_data)
                
                history_data["items"].append(node_data)
                item.deleteNode()
            elif isinstance(item, FlowchartConnection):
                # 记录连接信息
                conn_data = {
                    "item_type": "connection",
                    "start_node_id": id(item.start_node),
                    "end_node_id": id(item.end_node),
                    "color": item.color.name()
                }
                history_data["items"].append(conn_data)
                item.deleteConnection()
        
        # 添加到历史记录
        self.addHistory(history_data)
        
        # 标记为已修改
        self.setModified(True)
        
        self.statusBar().showMessage("已删除选中项")
    
    def setLineStyle(self):
        """设置选中连接线的样式"""
        # 获取选中的连接线
        selected_connections = [item for item in self.scene.selectedItems() 
                               if isinstance(item, FlowchartConnection)]
        
        if not selected_connections:
            QMessageBox.information(self, "提示", "请先选择要设置样式的连接线")
            return
        
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("设置连接线样式")
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout(dialog)
        
        # 颜色选择
        color_button = QPushButton("选择颜色")
        color = selected_connections[0].color  # 使用第一个选中连接线的颜色
        
        # 更新颜色按钮样式
        def update_color_button():
            color_button.setStyleSheet(
                f"background-color: {color.name()}; "
                f"color: {'black' if color.lightness() > 128 else 'white'};"
                f"padding: 5px;"
            )
        
        update_color_button()
        
        # 选择颜色
        def choose_color():
            nonlocal color
            new_color = QColorDialog.getColor(color, dialog, "选择连接线颜色")
            if new_color.isValid():
                color = new_color
                update_color_button()
        
        color_button.clicked.connect(choose_color)
        layout.addWidget(color_button)
        
        # 线宽选择
        width_layout = QHBoxLayout()
        width_label = QLabel("线条宽度:")
        width_slider = QSlider(Qt.Horizontal)
        width_slider.setMinimum(1)
        width_slider.setMaximum(10)
        width_slider.setValue(int(selected_connections[0].pen().width()))
        width_slider.setTickPosition(QSlider.TicksBelow)
        width_slider.setTickInterval(1)
        width_value = QLabel(str(width_slider.value()))
        
        def update_width_value(value):
            width_value.setText(str(value))
        
        width_slider.valueChanged.connect(update_width_value)
        
        width_layout.addWidget(width_label)
        width_layout.addWidget(width_slider)
        width_layout.addWidget(width_value)
        layout.addLayout(width_layout)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # 显示对话框
        if dialog.exec_() == QDialog.Accepted:
            # 记录历史
            history_data = {
                "type": "change_line_style",
                "connections": []
            }
            
            # 应用样式到所有选中的连接线
            for conn in selected_connections:
                # 记录原始样式
                history_data["connections"].append({
                    "connection_id": id(conn),
                    "old_color": conn.color.name(),
                    "old_width": conn.pen().width(),
                    "new_color": color.name(),
                    "new_width": width_slider.value()
                })
                
                # 设置新样式
                conn.color = color
                pen = conn.pen()
                pen.setColor(color)
                pen.setWidth(width_slider.value())
                conn.setPen(pen)
                conn.update()
            
            # 添加到历史记录
            self.addHistory(history_data)
            
            # 标记为已修改
            self.setModified(True)
            
            self.statusBar().showMessage("已更新连接线样式")
    
    def addHistory(self, data):
        """添加操作历史"""
        # 如果当前不在最新状态，删除之后的历史
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        
        # 添加新的历史记录
        self.history.append(data)
        
        # 如果历史记录超过最大限制，删除最早的记录
        if len(self.history) > self.max_history:
            self.history.pop(0)
        
        # 更新历史索引
        self.history_index = len(self.history) - 1
    
    def undo(self):
        """撤销上一步操作"""
        if self.history_index < 0:
            self.statusBar().showMessage("没有可撤销的操作")
            return
        
        # 获取当前历史记录
        data = self.history[self.history_index]
        
        # 根据操作类型执行撤销
        if data["type"] == "add_node":
            # 撤销添加节点操作，删除该节点
            for item in self.scene.items():
                if isinstance(item, FlowchartNode) and id(item) == data["node_id"]:
                    item.deleteNode()
                    break
        elif data["type"] == "delete_items":
            # 撤销删除操作，恢复删除的项目
            # 先恢复节点
            nodes = {}
            for item_data in data["items"]:
                if item_data["item_type"] == "node":
                    # 创建节点
                    pos = QPointF(item_data["node_pos"][0], item_data["node_pos"][1])
                    node = FlowchartNode(item_data["node_type"], item_data["node_text"], pos)
                    node.color = QColor(item_data["node_color"])
                    self.scene.addItem(node)
                    nodes[item_data["node_id"]] = node
            
            # 再恢复连接
            for item_data in data["items"]:
                if item_data["item_type"] == "node":
                    # 恢复该节点的连接
                    for conn_data in item_data["connections"]:
                        # 检查起点和终点是否存在
                        start_node = nodes.get(conn_data["start_node_id"])
                        end_node = nodes.get(conn_data["end_node_id"])
                        
                        if start_node and end_node and start_node != end_node:
                            conn = FlowchartConnection(start_node, end_node)
                            conn.color = QColor(conn_data["color"])
                            pen = conn.pen()
                            pen.setColor(conn.color)
                            conn.setPen(pen)
                            self.scene.addItem(conn)
                elif item_data["item_type"] == "connection":
                    # 当前场景中的节点
                    scene_nodes = {id(node): node for node in self.scene.items() 
                                   if isinstance(node, FlowchartNode)}
                    
                    # 检查起点和终点是否存在
                    start_node = scene_nodes.get(item_data["start_node_id"])
                    end_node = scene_nodes.get(item_data["end_node_id"])
                    
                    if start_node and end_node and start_node != end_node:
                        conn = FlowchartConnection(start_node, end_node)
                        conn.color = QColor(item_data["color"])
                        pen = conn.pen()
                        pen.setColor(conn.color)
                        conn.setPen(pen)
                        self.scene.addItem(conn)
        elif data["type"] == "change_line_style":
            # 撤销样式更改，恢复原始样式
            for conn_data in data["connections"]:
                # 在场景中查找连接
                for item in self.scene.items():
                    if isinstance(item, FlowchartConnection) and id(item) == conn_data["connection_id"]:
                        # 恢复原始样式
                        item.color = QColor(conn_data["old_color"])
                        pen = item.pen()
                        pen.setColor(item.color)
                        pen.setWidth(conn_data["old_width"])
                        item.setPen(pen)
                        item.update()
                        break
        
        # 更新历史索引
        self.history_index -= 1
        
        # 标记为已修改
        self.setModified(True)
        
        self.statusBar().showMessage("已撤销上一步操作")
    
    def redo(self):
        """重做上一步操作"""
        if self.history_index >= len(self.history) - 1:
            self.statusBar().showMessage("没有可重做的操作")
            return
        
        # 更新历史索引
        self.history_index += 1
        
        # 获取当前历史记录
        data = self.history[self.history_index]
        
        # 根据操作类型执行重做
        if data["type"] == "add_node":
            # 重做添加节点操作
            pos = QPointF(data["node_pos"][0], data["node_pos"][1])
            node = FlowchartNode(data["node_type"], data["node_text"], pos)
            self.scene.addItem(node)
            
            # 如果有父节点，创建连接
            if data["parent_node_id"]:
                for item in self.scene.items():
                    if isinstance(item, FlowchartNode) and id(item) == data["parent_node_id"]:
                        conn = FlowchartConnection(item, node)
                        self.scene.addItem(conn)
                        break
        elif data["type"] == "delete_items":
            # 重做删除操作，删除项目
            for item_data in data["items"]:
                if item_data["item_type"] == "node":
                    # 删除节点
                    for item in self.scene.items():
                        if isinstance(item, FlowchartNode) and id(item) == item_data["node_id"]:
                            item.deleteNode()
                            break
                elif item_data["item_type"] == "connection":
                    # 删除连接
                    for item in self.scene.items():
                        if isinstance(item, FlowchartConnection) and \
                           id(item.start_node) == item_data["start_node_id"] and \
                           id(item.end_node) == item_data["end_node_id"]:
                            item.deleteConnection()
                            break
        elif data["type"] == "change_line_style":
            # 重做样式更改
            for conn_data in data["connections"]:
                # 在场景中查找连接
                for item in self.scene.items():
                    if isinstance(item, FlowchartConnection) and id(item) == conn_data["connection_id"]:
                        # 应用新样式
                        item.color = QColor(conn_data["new_color"])
                        pen = item.pen()
                        pen.setColor(item.color)
                        pen.setWidth(conn_data["new_width"])
                        item.setPen(pen)
                        item.update()
                        break
        
        # 标记为已修改
        self.setModified(True)
        
        self.statusBar().showMessage("已重做操作")
    
    def showWelcomePage(self):
        """返回欢迎页面"""
        # 如果有未保存的更改，先提示保存
        if self.is_modified and self.scene.items():
            reply = QMessageBox.question(
                self, "保存确认", 
                "当前思维导图已被修改，是否保存？",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                if not self.saveFlowchart():
                    return  # 保存失败，取消操作
            elif reply == QMessageBox.Cancel:
                return  # 取消操作
        
        # 切换到欢迎页面
        self.central_stack.setCurrentIndex(0)
        self.statusBar().showMessage("返回主页")
    
    def newFlowchart(self, ask_save=True):
        """新建思维导图
        
        Args:
            ask_save: 是否在有未保存更改时提示保存
        """
        # 如果有未保存的更改，先提示保存
        if ask_save and self.is_modified and self.scene.items():
            reply = QMessageBox.question(
                self, "保存确认", 
                "当前思维导图已被修改，是否保存？",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                if not self.saveFlowchart():
                    return False  # 保存失败，取消操作
            elif reply == QMessageBox.Cancel:
                return False  # 取消操作
        
        # 清空场景
        self.scene.clear()
        self.current_file = None
        
        # 重置历史记录
        self.history = []
        self.history_index = -1
        
        # 重置修改状态
        self.setModified(False)
        
        # 切换到编辑视图
        self.central_stack.setCurrentIndex(1)
        
        self.statusBar().showMessage("已创建新思维导图")
        return True
    
    def openFlowchart(self):
        """打开思维导图文件"""
        # 如果有未保存的更改，先提示保存
        if self.is_modified and self.scene.items():
            reply = QMessageBox.question(
                self, "保存确认", 
                "当前思维导图已被修改，是否保存？",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                if not self.saveFlowchart():
                    return  # 保存失败，取消操作
            elif reply == QMessageBox.Cancel:
                return  # 取消操作
        
        # 选择文件
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开思维导图", "", "思维导图文件 (*.mindmap);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            # 清空当前场景
            self.scene.clear()
            
            # 加载文件
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 设置当前文件路径
            self.current_file = file_path
            
            # 首先创建节点
            nodes = {}
            for node_data in data["nodes"]:
                pos = QPointF(node_data["pos_x"], node_data["pos_y"])
                node = FlowchartNode(node_data["type"], node_data["text"], pos)
                if "color" in node_data:
                    node.color = QColor(node_data["color"])
                self.scene.addItem(node)
                nodes[node_data["id"]] = node
            
            # 然后创建连接
            for conn_data in data["connections"]:
                if conn_data["start_id"] in nodes and conn_data["end_id"] in nodes:
                    start_node = nodes[conn_data["start_id"]]
                    end_node = nodes[conn_data["end_id"]]
                    conn = FlowchartConnection(start_node, end_node)
                    if "color" in conn_data:
                        conn.color = QColor(conn_data["color"])
                        pen = conn.pen()
                        pen.setColor(conn.color)
                        if "width" in conn_data:
                            pen.setWidth(conn_data["width"])
                        conn.setPen(pen)
                    self.scene.addItem(conn)
            
            # 重置历史记录
            self.history = []
            self.history_index = -1
            
            # 重置修改状态
            self.setModified(False)
            
            # 切换到编辑视图
            self.central_stack.setCurrentIndex(1)
            
            # 调整视图以显示所有内容
            self.view.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)
            
            self.statusBar().showMessage(f"已打开思维导图: {os.path.basename(file_path)}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开文件时发生错误: {str(e)}")
            return
    
    def showWelcomePage(self):
        """返回欢迎页面"""
        # 如果有未保存的更改，先提示保存
        if self.is_modified and self.scene.items():
            reply = QMessageBox.question(
                self, "保存确认", 
                "当前思维导图已被修改，是否保存？",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                if not self.saveFlowchart():
                    return  # 保存失败，取消操作
            elif reply == QMessageBox.Cancel:
                return  # 取消操作
        
        # 切换到欢迎页面
        self.central_stack.setCurrentIndex(0)
        self.statusBar().showMessage("返回主页")
    
    def redo(self):
        """重做上一步操作"""
        if self.history_index >= len(self.history) - 1:
            self.statusBar().showMessage("没有可重做的操作")
            return
        
        # 更新历史索引
        self.history_index += 1
        
        # 获取当前历史记录
        data = self.history[self.history_index]
        
        # 根据操作类型执行重做
        if data["type"] == "add_node":
            # 重做添加节点操作
            pos = QPointF(data["node_pos"][0], data["node_pos"][1])
            node = FlowchartNode(data["node_type"], data["node_text"], pos)
            self.scene.addItem(node)
            
            # 如果有父节点，创建连接
            if data["parent_node_id"]:
                for item in self.scene.items():
                    if isinstance(item, FlowchartNode) and id(item) == data["parent_node_id"]:
                        conn = FlowchartConnection(item, node)
                        self.scene.addItem(conn)
                        break
        elif data["type"] == "delete_items":
            # 重做删除操作，删除项目
            for item_data in data["items"]:
                if item_data["item_type"] == "node":
                    # 删除节点
                    for item in self.scene.items():
                        if isinstance(item, FlowchartNode) and id(item) == item_data["node_id"]:
                            item.deleteNode()
                            break
                elif item_data["item_type"] == "connection":
                    # 删除连接
                    for item in self.scene.items():
                        if isinstance(item, FlowchartConnection) and \
                           id(item.start_node) == item_data["start_node_id"] and \
                           id(item.end_node) == item_data["end_node_id"]:
                            item.deleteConnection()
                            break
        elif data["type"] == "change_line_style":
            # 重做样式更改
            for conn_data in data["connections"]:
                # 在场景中查找连接
                for item in self.scene.items():
                    if isinstance(item, FlowchartConnection) and id(item) == conn_data["connection_id"]:
                        # 应用新样式
                        item.color = QColor(conn_data["new_color"])
                        pen = item.pen()
                        pen.setColor(item.color)
                        pen.setWidth(conn_data["new_width"])
                        item.setPen(pen)
                        item.update()
                        break
        
        # 标记为已修改
        self.setModified(True)
        
        self.statusBar().showMessage("已重做操作")

def openFlowchart(self):
    """打开思维导图文件"""
    # 如果有未保存的更改，先提示保存
    if self.is_modified and self.scene.items():
        reply = QMessageBox.question(
            self, "保存确认", 
            "当前思维导图已被修改，是否保存？",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save
        )
        
        if reply == QMessageBox.Save:
            if not self.saveFlowchart():
                return False  # 保存失败，取消操作
        elif reply == QMessageBox.Cancel:
            return False  # 取消操作
    
    file_path, _ = QFileDialog.getOpenFileName(
        self, "打开思维导图", "", "思维导图文件 (*.flow);;所有文件 (*)")
    
    if file_path:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 清空当前场景
            self.scene.clear()
            
            # 创建节点
            nodes = {}
            for node_data in data["nodes"]:
                node = FlowchartNode(
                    node_data["type"],
                    node_data["text"],
                    QPointF(node_data["x"], node_data["y"])
                )
                if "color" in node_data:
                    node.color = QColor(node_data["color"])
                self.scene.addItem(node)
                nodes[node_data["id"]] = node
            
            # 创建连接
            for conn_data in data["connections"]:
                if conn_data["start"] in nodes and conn_data["end"] in nodes:
                    connection = FlowchartConnection(
                        nodes[conn_data["start"]],
                        nodes[conn_data["end"]]
                    )
                    # 如果有颜色和线宽信息，应用它们
                    if "color" in conn_data:
                        connection.color = QColor(conn_data["color"])
                        pen = connection.pen()
                        pen.setColor(connection.color)
                        connection.setPen(pen)
                    if "width" in conn_data:
                        pen = connection.pen()
                        pen.setWidth(conn_data["width"])
                        connection.setPen(pen)
                    self.scene.addItem(connection)
            
            self.current_file = file_path
            
            # 重置历史记录
            self.history = []
            self.history_index = -1
            
            # 重置修改状态
            self.setModified(False)
            
            # 切换到编辑视图
            self.central_stack.setCurrentIndex(1)
            
            self.statusBar().showMessage(f"已打开 {file_path}")
            return True
        
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开文件: {str(e)}")
            return False
    
    return False

    def saveFlowchart(self):
        """保存思维导图"""
        if not self.current_file:
            return self.saveFlowchartAs()
        
        try:
            # 收集节点和连接数据
            data = {"nodes": [], "connections": []}
            
            # 节点ID映射
            node_to_id = {}
            node_id = 0
            
            # 收集节点数据
            for item in self.scene.items():
                if isinstance(item, FlowchartNode):
                    node_id += 1
                    node_to_id[item] = str(node_id)
                    
                    node_data = {
                        "id": str(node_id),
                        "type": item.node_type,
                        "text": item.node_text,
                        "x": item.scenePos().x(),
                        "y": item.scenePos().y(),
                        "color": item.color.name()
                    }
                    data["nodes"].append(node_data)
            
            # 收集连接数据
            for item in self.scene.items():
                if isinstance(item, FlowchartConnection):
                    if item.start_node in node_to_id and item.end_node in node_to_id:
                        conn_data = {
                            "start": node_to_id[item.start_node],
                            "end": node_to_id[item.end_node],
                            "color": item.color.name(),
                            "width": item.pen().width()
                        }
                        data["connections"].append(conn_data)
            
            # 保存为JSON文件
            with open(self.current_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # 重置修改状态
            self.setModified(False)
            
            self.statusBar().showMessage(f"已保存到 {self.current_file}")
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
            return False

    def saveFlowchartAs(self):
        """思维导图另存为"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "思维导图另存为", "", "思维导图文件 (*.flow);;所有文件 (*)")
        
        if not file_path:
            return False
        
        # 确保文件扩展名
        if not file_path.endswith('.flow'):
            file_path += '.flow'
        
        self.current_file = file_path
        return self.saveFlowchart()  # 调用保存方法

    def auto_layout(self):
        """应用自动布局算法"""
        auto_layout = advanced.AutoLayoutAlgorithm(self)
        auto_layout.apply_layout()
    
    def toggle_fold_selected(self):
        """折叠/展开选中节点"""
        self.shortcut_manager.toggle_fold_selected()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FlowchartEditor()
    window.show()
    sys.exit(app.exec_())
