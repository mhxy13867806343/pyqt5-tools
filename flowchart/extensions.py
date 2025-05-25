#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QAction, QFileDialog, QInputDialog, QMessageBox)
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPen, QBrush, QColor, QPainterPath, QPolygonF, QFont, QPixmap

# 扩展节点类型
EXTENDED_NODE_TYPES = {
    "菱形": {"shape": "diamond", "color": QColor(255, 218, 185)},  # 桃色
    "六边形": {"shape": "hexagon", "color": QColor(173, 216, 230)},  # 淡蓝色
    "平行四边形": {"shape": "parallelogram", "color": QColor(152, 251, 152)},  # 淡绿色
    "文档": {"shape": "document", "color": QColor(255, 250, 205)},  # 淡黄色
    "椭圆": {"shape": "ellipse", "color": QColor(221, 160, 221)},  # 梅红色
}

def extend_node_shape(node):
    """扩展节点形状，用于碰撞检测"""
    path = QPainterPath()
    
    if node.shape_type == "rounded_rect":
        rect = QRectF(-node.width/2, -node.height/2, node.width, node.height)
        path.addRoundedRect(rect, 10, 10)  # 圆角矩形
    elif node.shape_type == "cloud":
        # 使用节点自己的云形状绘制方法
        node._draw_cloud_path(path)
    elif node.shape_type == "diamond":
        # 菱形
        points = [
            QPointF(0, -node.height/2),
            QPointF(node.width/2, 0),
            QPointF(0, node.height/2),
            QPointF(-node.width/2, 0)
        ]
        polygon = QPolygonF(points)
        path.addPolygon(polygon)
    elif node.shape_type == "hexagon":
        # 六边形
        w = node.width/2
        h = node.height/2
        points = [
            QPointF(-w/2, -h),
            QPointF(w/2, -h),
            QPointF(w, 0),
            QPointF(w/2, h),
            QPointF(-w/2, h),
            QPointF(-w, 0)
        ]
        polygon = QPolygonF(points)
        path.addPolygon(polygon)
    elif node.shape_type == "parallelogram":
        # 平行四边形
        offset = node.width/4
        points = [
            QPointF(-node.width/2 + offset, -node.height/2),
            QPointF(node.width/2 + offset, -node.height/2),
            QPointF(node.width/2 - offset, node.height/2),
            QPointF(-node.width/2 - offset, node.height/2)
        ]
        polygon = QPolygonF(points)
        path.addPolygon(polygon)
    elif node.shape_type == "document":
        # 文档形状（带卷曲底部的矩形）
        path.moveTo(-node.width/2, -node.height/2)
        path.lineTo(node.width/2, -node.height/2)
        path.lineTo(node.width/2, node.height/2 - 10)
        path.cubicTo(
            node.width/3, node.height/2 - 5,
            node.width/6, node.height/2 + 5,
            -node.width/2, node.height/2
        )
        path.closeSubpath()
    elif node.shape_type == "ellipse":
        # 椭圆
        path.addEllipse(QRectF(-node.width/2, -node.height/2, node.width, node.height))
    else:
        # 默认使用矩形
        path.addRect(QRectF(-node.width/2, -node.height/2, node.width, node.height))
        
    return path

def extend_node_paint(node, painter, option, widget):
    """扩展节点绘制方法"""
    # 设置画笔和画刷
    pen = QPen(Qt.black)
    pen.setWidth(2)
    if node.isSelected():
        pen.setColor(Qt.red)
    
    # 使用节点的渐变作为画刷
    brush = QBrush(node.gradient)
    
    painter.setPen(pen)
    painter.setBrush(brush)
    
    # 根据形状绘制
    if node.shape_type == "rounded_rect":
        rect = QRectF(-node.width/2, -node.height/2, node.width, node.height)
        painter.drawRoundedRect(rect, 10, 10)  # 圆角矩形
    elif node.shape_type == "cloud":
        # 云形状由多个圆弧组成
        path = QPainterPath()
        node._draw_cloud_path(path)
        painter.drawPath(path)
    elif node.shape_type == "diamond":
        # 菱形
        points = [
            QPointF(0, -node.height/2),
            QPointF(node.width/2, 0),
            QPointF(0, node.height/2),
            QPointF(-node.width/2, 0)
        ]
        polygon = QPolygonF(points)
        painter.drawPolygon(polygon)
    elif node.shape_type == "hexagon":
        # 六边形
        w = node.width/2
        h = node.height/2
        points = [
            QPointF(-w/2, -h),
            QPointF(w/2, -h),
            QPointF(w, 0),
            QPointF(w/2, h),
            QPointF(-w/2, h),
            QPointF(-w, 0)
        ]
        polygon = QPolygonF(points)
        painter.drawPolygon(polygon)
    elif node.shape_type == "parallelogram":
        # 平行四边形
        offset = node.width/4
        points = [
            QPointF(-node.width/2 + offset, -node.height/2),
            QPointF(node.width/2 + offset, -node.height/2),
            QPointF(node.width/2 - offset, node.height/2),
            QPointF(-node.width/2 - offset, node.height/2)
        ]
        polygon = QPolygonF(points)
        painter.drawPolygon(polygon)
    elif node.shape_type == "document":
        # 文档形状（带卷曲底部的矩形）
        path = QPainterPath()
        path.moveTo(-node.width/2, -node.height/2)
        path.lineTo(node.width/2, -node.height/2)
        path.lineTo(node.width/2, node.height/2 - 10)
        path.cubicTo(
            node.width/3, node.height/2 - 5,
            node.width/6, node.height/2 + 5,
            -node.width/2, node.height/2
        )
        path.closeSubpath()
        painter.drawPath(path)
    elif node.shape_type == "ellipse":
        # 椭圆
        painter.drawEllipse(QRectF(-node.width/2, -node.height/2, node.width, node.height))
    else:
        # 默认使用矩形
        painter.drawRect(QRectF(-node.width/2, -node.height/2, node.width, node.height))
    
    # 检查节点是否有图片
    if hasattr(node, 'image') and node.image is not None:
        # 绘制图片在节点顶部
        pixmap = node.image.scaled(
            int(node.width * 0.8), 
            int(node.height * 0.4),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        painter.drawPixmap(
            QPointF(-pixmap.width()/2, -node.height/2 + 5),
            pixmap
        )
        
        # 调整文本区域
        text_rect = QRectF(
            -node.width/2 + 10, 
            -node.height/2 + pixmap.height() + 10, 
            node.width - 20, 
            node.height - pixmap.height() - 15
        )
    else:
        # 使用默认文本区域
        text_rect = QRectF(-node.width/2 + 10, -node.height/2 + 5, node.width - 20, node.height - 10)
    
    # 绘制文本
    font = QFont()
    font.setPointSize(10)
    if node.node_type == "中心主题":
        font.setBold(True)
        font.setPointSize(12)
    
    painter.setFont(font)
    painter.setPen(Qt.black)
    painter.drawText(text_rect, Qt.AlignCenter | Qt.TextWordWrap, node.node_text)
    
    # 检查节点是否有链接
    if hasattr(node, 'link') and node.link:
        # 绘制链接图标
        painter.setPen(Qt.blue)
        link_rect = QRectF(
            node.width/2 - 20, 
            node.height/2 - 20, 
            15, 
            15
        )
        painter.drawText(link_rect, Qt.AlignCenter, "🔗")

def extend_node_context_menu(node, event, main_window):
    """扩展节点右键菜单，添加图片和链接选项"""
    # 添加图片和链接选项
    add_image_action = node.menu.addAction("添加图片")
    remove_image_action = node.menu.addAction("移除图片")
    node.menu.addSeparator()
    add_link_action = node.menu.addAction("添加链接")
    remove_link_action = node.menu.addAction("移除链接")
    
    # 如果节点没有图片，禁用移除图片选项
    if not hasattr(node, 'image') or node.image is None:
        remove_image_action.setEnabled(False)
    
    # 如果节点没有链接，禁用移除链接选项
    if not hasattr(node, 'link') or not node.link:
        remove_link_action.setEnabled(False)
    
    # 连接扩展选项的信号
    add_image_action.triggered.connect(lambda: _add_image_to_node(node, main_window))
    remove_image_action.triggered.connect(lambda: _remove_image_from_node(node))
    add_link_action.triggered.connect(lambda: _add_link_to_node(node, main_window))
    remove_link_action.triggered.connect(lambda: _remove_link_from_node(node))
    
    # 返回None，让原始的菜单处理逻辑继续执行
    # 不调用menu.exec_，由节点的contextMenuEvent方法调用
    return None

def _add_image_to_node(node, main_window):
    """添加图片到节点"""
    file_path, _ = QFileDialog.getOpenFileName(
        main_window, 
        "选择图片", 
        "", 
        "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
    )
    
    if file_path:
        try:
            node.image = QPixmap(file_path)
            node.update()
        except Exception as e:
            QMessageBox.critical(main_window, "错误", f"无法加载图片: {str(e)}")

def _remove_image_from_node(node):
    """从节点移除图片"""
    if hasattr(node, 'image'):
        node.image = None
        node.update()

def _add_link_to_node(node, main_window):
    """添加链接到节点"""
    link, ok = QInputDialog.getText(
        main_window, 
        "添加链接", 
        "请输入URL链接:",
        text=getattr(node, 'link', '')
    )
    
    if ok and link:
        node.link = link
        node.update()

def _remove_link_from_node(node):
    """从节点移除链接"""
    if hasattr(node, 'link'):
        node.link = None
        node.update()
