#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import datetime
import platform
import subprocess
from pathlib import Path
import shutil
from PIL import Image, ExifTags
import io

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFileDialog, QTreeView, QListWidget,
                             QListWidgetItem, QSplitter, QMenu, QAction, QMessageBox,
                             QFileSystemModel, QAbstractItemView, QScrollArea, QGroupBox,
                             QFormLayout, QLineEdit, QComboBox, QInputDialog)
from PyQt5.QtCore import Qt, QDir, QSize, QModelIndex, QRect, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon, QImageReader, QImage, QPalette, QColor


class ImageLoader(QThread):
    """图片加载线程，用于异步加载图片缩略图"""
    image_loaded = pyqtSignal(int, QPixmap)  # 图片加载完成信号，参数为索引和图片
    
    def __init__(self, file_paths, thumbnail_size):
        super().__init__()
        self.file_paths = file_paths
        self.thumbnail_size = thumbnail_size
        self.running = True
    
    def run(self):
        for i, file_path in enumerate(self.file_paths):
            if not self.running:
                break
                
            try:
                # 使用PIL加载图片并创建缩略图
                img = Image.open(file_path)
                img.thumbnail(self.thumbnail_size)
                
                # 转换为QPixmap
                img_data = io.BytesIO()
                img_format = img.format if img.format else 'PNG'
                img.save(img_data, format=img_format)
                pixmap = QPixmap()
                pixmap.loadFromData(img_data.getvalue())
                
                # 发送信号
                self.image_loaded.emit(i, pixmap)
            except Exception as e:
                print(f"加载图片 {file_path} 失败: {e}")
            
            # 给UI线程一些时间处理
            time.sleep(0.01)
    
    def stop(self):
        self.running = False


class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('图片管理工具')
        self.setMinimumSize(1000, 600)
        
        # 设置中心部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建主布局
        self.main_layout = QHBoxLayout(self.central_widget)
        
        # 创建分割器
        self.splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.splitter)
        
        # 创建左侧文件夹面板
        self.create_folder_panel()
        
        # 创建中间图片列表面板
        self.create_image_list_panel()
        
        # 创建右侧图片详情面板
        self.create_image_details_panel()
        
        # 设置分割器比例
        self.splitter.setSizes([200, 500, 300])
        
        # 初始化变量
        self.current_folder = None
        self.current_images = []
        self.image_loader = None
        
        # 状态栏
        self.statusBar().showMessage('准备就绪')
        
        # 设置默认目录为用户图片文件夹
        default_dir = os.path.join(str(Path.home()), 'Pictures')
        if os.path.exists(default_dir):
            self.folder_model.setRootPath(default_dir)
            self.folder_view.setRootIndex(self.folder_model.index(default_dir))
    
    def create_folder_panel(self):
        # 创建左侧文件夹面板
        folder_panel = QWidget()
        folder_layout = QVBoxLayout(folder_panel)
        
        # 文件夹标题
        folder_label = QLabel('文件夹')
        folder_label.setStyleSheet('font-weight: bold; font-size: 14px;')
        folder_layout.addWidget(folder_label)
        
        # 文件夹树
        self.folder_model = QFileSystemModel()
        self.folder_model.setFilter(QDir.Dirs | QDir.NoDotAndDotDot)
        self.folder_model.setRootPath('')
        
        self.folder_view = QTreeView()
        self.folder_view.setModel(self.folder_model)
        self.folder_view.setHeaderHidden(True)
        self.folder_view.setAnimated(True)
        self.folder_view.setIndentation(20)
        # 只显示名称列
        for i in range(1, self.folder_model.columnCount()):
            self.folder_view.hideColumn(i)
        
        self.folder_view.clicked.connect(self.on_folder_clicked)
        folder_layout.addWidget(self.folder_view)
        
        # 添加按钮
        buttons_layout = QHBoxLayout()
        
        self.browse_button = QPushButton('浏览...')
        self.browse_button.clicked.connect(self.browse_folder)
        buttons_layout.addWidget(self.browse_button)
        
        folder_layout.addLayout(buttons_layout)
        
        # 添加到分割器
        self.splitter.addWidget(folder_panel)
    
    def create_image_list_panel(self):
        # 创建中间图片列表面板
        image_panel = QWidget()
        image_layout = QVBoxLayout(image_panel)
        
        # 图片列表标题
        self.image_list_label = QLabel('图片列表')
        self.image_list_label.setStyleSheet('font-weight: bold; font-size: 14px;')
        image_layout.addWidget(self.image_list_label)
        
        # 图片列表
        self.image_list = QListWidget()
        self.image_list.setViewMode(QListWidget.IconMode)
        self.image_list.setIconSize(QSize(150, 150))
        self.image_list.setResizeMode(QListWidget.Adjust)
        self.image_list.setWrapping(True)
        self.image_list.setSpacing(10)
        self.image_list.setMovement(QListWidget.Static)
        self.image_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.image_list.itemClicked.connect(self.on_image_clicked)
        self.image_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.image_list.customContextMenuRequested.connect(self.show_image_context_menu)
        image_layout.addWidget(self.image_list)
        
        # 添加到分割器
        self.splitter.addWidget(image_panel)
    
    def create_image_details_panel(self):
        # 创建右侧图片详情面板
        details_panel = QWidget()
        details_layout = QVBoxLayout(details_panel)
        
        # 详情标题
        details_label = QLabel('图片详情')
        details_label.setStyleSheet('font-weight: bold; font-size: 14px;')
        details_layout.addWidget(details_label)
        
        # 图片预览
        preview_group = QGroupBox('预览')
        preview_layout = QVBoxLayout(preview_group)
        
        self.image_preview = QLabel()
        self.image_preview.setAlignment(Qt.AlignCenter)
        self.image_preview.setMinimumHeight(200)
        self.image_preview.setStyleSheet('background-color: #f0f0f0; border: 1px solid #ddd;')
        preview_layout.addWidget(self.image_preview)
        
        details_layout.addWidget(preview_group)
        
        # 图片信息
        info_group = QGroupBox('信息')
        info_layout = QFormLayout(info_group)
        
        self.file_name_label = QLabel('')
        self.file_size_label = QLabel('')
        self.image_dimensions_label = QLabel('')
        self.image_format_label = QLabel('')
        self.creation_date_label = QLabel('')
        self.modification_date_label = QLabel('')
        
        info_layout.addRow('文件名:', self.file_name_label)
        info_layout.addRow('文件大小:', self.file_size_label)
        info_layout.addRow('尺寸:', self.image_dimensions_label)
        info_layout.addRow('格式:', self.image_format_label)
        info_layout.addRow('创建日期:', self.creation_date_label)
        info_layout.addRow('修改日期:', self.modification_date_label)
        
        details_layout.addWidget(info_group)
        
        # 操作按钮
        actions_group = QGroupBox('操作')
        actions_layout = QVBoxLayout(actions_group)
        
        self.open_button = QPushButton('打开图片')
        self.open_button.clicked.connect(self.open_current_image)
        actions_layout.addWidget(self.open_button)
        
        self.rename_button = QPushButton('重命名')
        self.rename_button.clicked.connect(self.rename_current_image)
        actions_layout.addWidget(self.rename_button)
        
        self.delete_button = QPushButton('删除')
        self.delete_button.clicked.connect(self.delete_current_image)
        actions_layout.addWidget(self.delete_button)
        
        details_layout.addWidget(actions_group)
        
        # 添加弹性空间
        details_layout.addStretch()
        
        # 初始禁用按钮
        self.open_button.setEnabled(False)
        self.rename_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        
        # 添加到分割器
        self.splitter.addWidget(details_panel)
    
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, '选择图片文件夹', str(Path.home()))
        if folder:
            self.folder_view.setRootIndex(self.folder_model.index(folder))
            self.load_images_from_folder(folder)
    
    def on_folder_clicked(self, index):
        folder_path = self.folder_model.filePath(index)
        self.load_images_from_folder(folder_path)
    
    def load_images_from_folder(self, folder_path):
        self.current_folder = folder_path
        self.image_list_label.setText(f'图片列表 - {os.path.basename(folder_path)}')
        
        # 清空图片列表
        self.image_list.clear()
        self.current_images = []
        
        # 停止之前的加载线程
        if self.image_loader and self.image_loader.isRunning():
            self.image_loader.stop()
            self.image_loader.wait()
        
        # 获取文件夹中的所有图片
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        image_files = []
        
        try:
            for file in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file)
                if os.path.isfile(file_path) and os.path.splitext(file)[1].lower() in image_extensions:
                    image_files.append(file_path)
                    
                    # 添加到列表，先用占位图
                    item = QListWidgetItem(file)
                    item.setIcon(QIcon())
                    item.setSizeHint(QSize(170, 190))  # 设置项目大小
                    item.setData(Qt.UserRole, file_path)  # 存储文件路径
                    self.image_list.addItem(item)
                    self.current_images.append(file_path)
            
            # 更新状态栏
            self.statusBar().showMessage(f'找到 {len(image_files)} 张图片')
            
            # 异步加载图片
            if image_files:
                self.image_loader = ImageLoader(image_files, (150, 150))
                self.image_loader.image_loaded.connect(self.on_image_loaded)
                self.image_loader.start()
            
        except Exception as e:
            QMessageBox.warning(self, '错误', f'加载文件夹失败: {e}')
    
    def on_image_loaded(self, index, pixmap):
        if index < self.image_list.count():
            item = self.image_list.item(index)
            item.setIcon(QIcon(pixmap))
    
    def on_image_clicked(self, item):
        file_path = item.data(Qt.UserRole)
        self.show_image_details(file_path)
        
        # 启用按钮
        self.open_button.setEnabled(True)
        self.rename_button.setEnabled(True)
        self.delete_button.setEnabled(True)
    
    def show_image_details(self, file_path):
        try:
            # 基本文件信息
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            # 格式化文件大小
            if file_size < 1024:
                size_str = f"{file_size} B"
            elif file_size < 1024 * 1024:
                size_str = f"{file_size / 1024:.2f} KB"
            else:
                size_str = f"{file_size / (1024 * 1024):.2f} MB"
            
            # 获取创建和修改时间
            if platform.system() == 'Windows':
                created_time = os.path.getctime(file_path)
            else:
                try:
                    stat = os.stat(file_path)
                    created_time = stat.st_birthtime  # macOS
                except AttributeError:
                    created_time = stat.st_mtime  # Linux可能没有创建时间
            
            modified_time = os.path.getmtime(file_path)
            
            # 格式化时间
            created_time_str = datetime.datetime.fromtimestamp(created_time).strftime('%Y-%m-%d %H:%M:%S')
            modified_time_str = datetime.datetime.fromtimestamp(modified_time).strftime('%Y-%m-%d %H:%M:%S')
            
            # 获取图片信息
            img = Image.open(file_path)
            width, height = img.size
            img_format = img.format
            
            # 更新标签
            self.file_name_label.setText(file_name)
            self.file_size_label.setText(size_str)
            self.image_dimensions_label.setText(f"{width} x {height}")
            self.image_format_label.setText(img_format)
            self.creation_date_label.setText(created_time_str)
            self.modification_date_label.setText(modified_time_str)
            
            # 显示预览图
            preview_size = QSize(300, 200)
            img.thumbnail((preview_size.width(), preview_size.height()))
            
            # 转换为QPixmap
            img_data = io.BytesIO()
            img.save(img_data, format=img_format)
            pixmap = QPixmap()
            pixmap.loadFromData(img_data.getvalue())
            
            self.image_preview.setPixmap(pixmap)
            
        except Exception as e:
            QMessageBox.warning(self, '错误', f'加载图片详情失败: {e}')
    
    def show_image_context_menu(self, position):
        item = self.image_list.itemAt(position)
        if not item:
            return
        
        context_menu = QMenu(self)
        
        open_action = QAction('打开', self)
        open_action.triggered.connect(self.open_current_image)
        
        rename_action = QAction('重命名', self)
        rename_action.triggered.connect(self.rename_current_image)
        
        delete_action = QAction('删除', self)
        delete_action.triggered.connect(self.delete_current_image)
        
        context_menu.addAction(open_action)
        context_menu.addAction(rename_action)
        context_menu.addSeparator()
        context_menu.addAction(delete_action)
        
        context_menu.exec_(self.image_list.mapToGlobal(position))
    
    def open_current_image(self):
        item = self.image_list.currentItem()
        if not item:
            return
        
        file_path = item.data(Qt.UserRole)
        
        try:
            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(['open', file_path])
            else:  # Linux
                subprocess.call(['xdg-open', file_path])
        except Exception as e:
            QMessageBox.warning(self, '错误', f'无法打开图片: {e}')
    
    def rename_current_image(self):
        item = self.image_list.currentItem()
        if not item:
            return
        
        file_path = item.data(Qt.UserRole)
        old_name = os.path.basename(file_path)
        file_dir = os.path.dirname(file_path)
        
        new_name, ok = QInputDialog.getText(self, '重命名图片', '输入新文件名:', text=old_name)
        
        if ok and new_name and new_name != old_name:
            new_path = os.path.join(file_dir, new_name)
            
            # 检查文件是否已存在
            if os.path.exists(new_path):
                QMessageBox.warning(self, '错误', f'文件 "{new_name}" 已存在')
                return
            
            try:
                # 重命名文件
                os.rename(file_path, new_path)
                
                # 更新列表项
                item.setText(new_name)
                item.setData(Qt.UserRole, new_path)
                
                # 更新当前图片列表
                index = self.current_images.index(file_path)
                self.current_images[index] = new_path
                
                # 更新详情
                self.show_image_details(new_path)
                
                self.statusBar().showMessage(f'已将 "{old_name}" 重命名为 "{new_name}"')
            except Exception as e:
                QMessageBox.warning(self, '错误', f'重命名失败: {e}')
    
    def delete_current_image(self):
        item = self.image_list.currentItem()
        if not item:
            return
        
        file_path = item.data(Qt.UserRole)
        file_name = os.path.basename(file_path)
        
        reply = QMessageBox.question(self, '确认删除', 
                                   f'确定要删除图片 "{file_name}" 吗?', 
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                # 删除文件
                os.remove(file_path)
                
                # 从列表中移除
                row = self.image_list.row(item)
                self.image_list.takeItem(row)
                
                # 从当前图片列表中移除
                self.current_images.remove(file_path)
                
                # 清空详情
                self.clear_image_details()
                
                # 禁用按钮
                self.open_button.setEnabled(False)
                self.rename_button.setEnabled(False)
                self.delete_button.setEnabled(False)
                
                self.statusBar().showMessage(f'已删除 "{file_name}"')
            except Exception as e:
                QMessageBox.warning(self, '错误', f'删除失败: {e}')
    
    def clear_image_details(self):
        self.file_name_label.setText('')
        self.file_size_label.setText('')
        self.image_dimensions_label.setText('')
        self.image_format_label.setText('')
        self.creation_date_label.setText('')
        self.modification_date_label.setText('')
        self.image_preview.clear()
    
    def closeEvent(self, event):
        # 停止加载线程
        if self.image_loader and self.image_loader.isRunning():
            self.image_loader.stop()
            self.image_loader.wait()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageViewer()
    window.show()
    sys.exit(app.exec_())