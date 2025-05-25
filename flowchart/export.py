#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
                            QComboBox, QSpinBox, QPushButton, QColorDialog, QFileDialog, 
                            QMessageBox, QDialogButtonBox)
from PyQt5.QtCore import Qt, QRectF, QMarginsF
from PyQt5.QtGui import QColor, QImage, QPainter, QPdfWriter, QPageSize

class FlowchartExporter:
    """流程图导出器，负责将流程图导出为图片或PDF"""
    
    def __init__(self, main_window):
        """初始化导出器"""
        self.main_window = main_window
        self.export_margin = 20  # 导出时的边距
    
    def export_flowchart(self):
        """导出流程图为图片或PDF"""
        # 检查是否有内容可导出
        if not self.main_window.scene.items():
            QMessageBox.warning(self.main_window, "警告", "当前没有内容可导出")
            return
        
        # 创建导出选项对话框
        dialog = ExportDialog(self.main_window)
        if dialog.exec_() != QDialog.Accepted:
            return
        
        # 获取导出选项
        export_format = dialog.format_combo.currentText()
        resolution = dialog.resolution_spin.value()
        bg_color = dialog.bg_color
        
        # 获取场景边界
        scene_rect = self.main_window.scene.itemsBoundingRect()
        
        # 添加边距
        scene_rect = scene_rect.marginsAdded(QMarginsF(
            self.export_margin, self.export_margin, 
            self.export_margin, self.export_margin
        ))
        
        # 根据选择的格式导出
        if export_format == "PDF":
            self._export_to_pdf(scene_rect)
        else:  # PNG 或 JPG
            self._export_to_image(scene_rect, export_format.lower(), resolution, bg_color)
    
    def _export_to_image(self, scene_rect, image_format, resolution, bg_color):
        """导出为图片格式"""
        # 计算导出图像的尺寸
        width = int(scene_rect.width() * resolution / 72)
        height = int(scene_rect.height() * resolution / 72)
        
        # 创建图像
        image = QImage(width, height, QImage.Format_ARGB32)
        image.fill(bg_color)
        
        # 创建画家
        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # 设置缩放
        painter.scale(resolution / 72, resolution / 72)
        
        # 绘制场景
        self.main_window.scene.render(painter, QRectF(), scene_rect)
        painter.end()
        
        # 保存图像
        file_filter = f"{image_format.upper()} 图像 (*.{image_format})"
        file_path, _ = QFileDialog.getSaveFileName(
            self.main_window, "导出为图片", "", file_filter
        )
        
        if file_path:
            if not file_path.lower().endswith(f".{image_format}"):
                file_path += f".{image_format}"
            
            if image.save(file_path):
                QMessageBox.information(self.main_window, "成功", f"流程图已成功导出为 {file_path}")
            else:
                QMessageBox.critical(self.main_window, "错误", f"无法保存图像到 {file_path}")
    
    def _export_to_pdf(self, scene_rect):
        """导出为PDF格式"""
        # 保存PDF
        file_path, _ = QFileDialog.getSaveFileName(
            self.main_window, "导出为PDF", "", "PDF 文件 (*.pdf)"
        )
        
        if file_path:
            if not file_path.lower().endswith(".pdf"):
                file_path += ".pdf"
            
            # 创建PDF写入器
            writer = QPdfWriter(file_path)
            writer.setPageSize(QPageSize(scene_rect.size(), QPageSize.Point))
            writer.setResolution(300)  # 设置DPI
            
            # 创建画家
            painter = QPainter(writer)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.TextAntialiasing)
            
            # 绘制场景
            self.main_window.scene.render(painter, QRectF(), scene_rect)
            painter.end()
            
            QMessageBox.information(self.main_window, "成功", f"流程图已成功导出为 {file_path}")


class ExportDialog(QDialog):
    """导出选项对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导出选项")
        self.setMinimumWidth(300)
        
        # 初始化背景颜色
        self.bg_color = QColor(Qt.white)
        
        # 创建布局
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # 格式选择
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPG", "PDF"])
        form_layout.addRow("导出格式:", self.format_combo)
        
        # 分辨率选择（仅对图片格式有效）
        self.resolution_spin = QSpinBox()
        self.resolution_spin.setRange(72, 600)
        self.resolution_spin.setValue(300)
        self.resolution_spin.setSuffix(" DPI")
        form_layout.addRow("分辨率:", self.resolution_spin)
        
        # 背景颜色选择
        self.color_button = QPushButton("选择颜色")
        self.color_button.clicked.connect(self._choose_color)
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(20, 20)
        self._update_color_preview()
        
        color_layout = QHBoxLayout()
        color_layout.addWidget(self.color_button)
        color_layout.addWidget(self.color_preview)
        form_layout.addRow("背景颜色:", color_layout)
        
        # 添加表单布局
        layout.addLayout(form_layout)
        
        # 添加按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # 连接信号
        self.format_combo.currentTextChanged.connect(self._update_ui)
        
        # 初始化UI状态
        self._update_ui()
    
    def _update_ui(self):
        """根据当前选择更新UI状态"""
        is_image = self.format_combo.currentText() != "PDF"
        self.resolution_spin.setEnabled(is_image)
        self.color_button.setEnabled(is_image)
        self.color_preview.setEnabled(is_image)
    
    def _choose_color(self):
        """选择背景颜色"""
        color = QColorDialog.getColor(self.bg_color, self, "选择背景颜色")
        if color.isValid():
            self.bg_color = color
            self._update_color_preview()
    
    def _update_color_preview(self):
        """更新颜色预览"""
        style = f"background-color: {self.bg_color.name()}; border: 1px solid black;"
        self.color_preview.setStyleSheet(style)
