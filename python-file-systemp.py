#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import datetime
import platform
import subprocess
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
                             QVBoxLayout, QHBoxLayout, QWidget, QLabel, QLineEdit,
                             QPushButton, QFileDialog, QMenu, QAction, QHeaderView,
                             QComboBox, QCheckBox, QMessageBox, QProgressBar, QSizePolicy,
                             QGroupBox, QFormLayout, QSpinBox, QInputDialog, QDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer
from PyQt5.QtGui import QIcon, QCursor


class FileSearchThread(QThread):
    """文件搜索线程"""
    # 定义信号
    file_found = pyqtSignal(str, str, str, int, str, str, str)  # 文件路径, 文件名, 后缀, 大小, 创建时间, 修改时间, 文件类型
    search_completed = pyqtSignal(int)  # 搜索完成信号，参数为找到的文件数量
    search_progress = pyqtSignal(int, int)  # 搜索进度信号，参数为当前进度和总进度
    
    def __init__(self, search_path, search_term, file_extensions, min_size, max_size, search_subdirs):
        super().__init__()
        self.search_path = search_path
        self.search_term = search_term.lower()  # 转为小写以便不区分大小写搜索
        self.file_extensions = file_extensions
        self.min_size = min_size
        self.max_size = max_size
        self.search_subdirs = search_subdirs
        self.running = True
        self.file_count = 0
        self.dirs_to_scan = 0
        self.dirs_scanned = 0
    
    def run(self):
        # 计算需要扫描的目录数量
        if self.search_subdirs:
            for _, dirs, _ in os.walk(self.search_path):
                self.dirs_to_scan += 1
                if self.dirs_to_scan > 1000:  # 限制目录计数，避免过长时间
                    break
        else:
            self.dirs_to_scan = 1
        
        # 开始搜索
        self.search_files(self.search_path)
        self.search_completed.emit(self.file_count)
    
    def search_files(self, directory):
        try:
            # 获取目录中的所有文件和子目录
            items = os.listdir(directory)
            
            # 更新进度
            self.dirs_scanned += 1
            self.search_progress.emit(self.dirs_scanned, self.dirs_to_scan)
            
            for item in items:
                if not self.running:  # 检查是否应该停止
                    return
                
                full_path = os.path.join(directory, item)
                
                # 如果是文件
                if os.path.isfile(full_path):
                    # 检查文件名是否匹配搜索词
                    if self.search_term and self.search_term not in item.lower():
                        continue
                    
                    # 检查文件扩展名
                    _, ext = os.path.splitext(item)
                    ext = ext.lower()[1:]  # 移除点号并转为小写
                    
                    if self.file_extensions and ext not in self.file_extensions:
                        continue
                    
                    # 获取文件大小
                    try:
                        file_size = os.path.getsize(full_path)
                        
                        # 检查文件大小范围
                        if (self.min_size > 0 and file_size < self.min_size * 1024) or \
                           (self.max_size > 0 and file_size > self.max_size * 1024):
                            continue
                        
                        # 获取文件创建和修改时间
                        if platform.system() == 'Windows':
                            created_time = os.path.getctime(full_path)
                        else:
                            try:
                                stat = os.stat(full_path)
                                created_time = stat.st_birthtime  # macOS
                            except AttributeError:
                                created_time = stat.st_mtime  # Linux可能没有创建时间
                        
                        modified_time = os.path.getmtime(full_path)
                        
                        # 格式化时间
                        created_time_str = datetime.datetime.fromtimestamp(created_time).strftime('%Y-%m-%d %H:%M:%S')
                        modified_time_str = datetime.datetime.fromtimestamp(modified_time).strftime('%Y-%m-%d %H:%M:%S')
                        
                        # 确定文件类型
                        file_type = "未知"
                        if ext:
                            file_type = f"{ext.upper()} 文件"
                        else:
                            file_type = "无扩展名文件"
                        
                        # 发出文件找到信号
                        self.file_found.emit(
                            full_path,
                            item,
                            ext,
                            file_size,
                            created_time_str,
                            modified_time_str,
                            file_type
                        )
                        
                        self.file_count += 1
                    except Exception as e:
                        print(f"处理文件 {full_path} 时出错: {e}")
                
                # 如果是目录且需要搜索子目录
                elif os.path.isdir(full_path) and self.search_subdirs:
                    try:
                        self.search_files(full_path)
                    except PermissionError:
                        print(f"无权限访问目录: {full_path}")
                    except Exception as e:
                        print(f"搜索目录 {full_path} 时出错: {e}")
        
        except PermissionError:
            print(f"无权限访问目录: {directory}")
        except Exception as e:
            print(f"搜索目录 {directory} 时出错: {e}")
    
    def stop(self):
        self.running = False


class FileSearcher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('文件搜索器')
        self.setMinimumSize(900, 600)
        
        # 创建主窗口部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # 初始化历史记录
        self.search_history = []
        self.delete_history = []
        
        # 创建搜索控件
        self.create_search_controls()
        
        # 创建表格
        self.create_table()
        
        # 创建状态栏
        self.statusBar().showMessage('准备就绪')
        
        # 搜索线程
        self.search_thread = None
        
        # 初始化计时器
        self.search_timer = QTimer()
        self.search_timer.timeout.connect(self.update_search_time)
        self.search_start_time = 0
        
        # 加载历史记录
        self.load_history_from_file()
        
        # 显示初始目录
        self.path_edit.setText(str(Path.home()))
    
    def create_search_controls(self):
        # 搜索区域组
        search_group = QGroupBox("搜索设置")
        search_layout = QVBoxLayout()
        
        # 路径选择区域
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("搜索路径:"))
        
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("输入或选择要搜索的路径")
        path_layout.addWidget(self.path_edit)
        
        self.browse_button = QPushButton("浏览...")
        self.browse_button.clicked.connect(self.browse_directory)
        path_layout.addWidget(self.browse_button)
        
        search_layout.addLayout(path_layout)
        
        # 搜索条件区域
        criteria_layout = QHBoxLayout()
        
        # 搜索词
        criteria_layout.addWidget(QLabel("搜索词:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入文件名关键词（留空搜索所有文件）")
        criteria_layout.addWidget(self.search_edit)
        
        # 文件类型
        criteria_layout.addWidget(QLabel("文件类型:"))
        self.file_type_combo = QComboBox()
        self.file_type_combo.addItem("所有文件")
        self.file_type_combo.addItem("文档 (txt, doc, docx, pdf, rtf)")
        self.file_type_combo.addItem("图片 (jpg, jpeg, png, gif, bmp)")
        self.file_type_combo.addItem("音频 (mp3, wav, flac, ogg)")
        self.file_type_combo.addItem("视频 (mp4, avi, mkv, mov)")
        self.file_type_combo.addItem("压缩文件 (zip, rar, 7z, tar, gz)")
        self.file_type_combo.addItem("自定义...")
        criteria_layout.addWidget(self.file_type_combo)
        
        # 搜索历史下拉菜单
        criteria_layout.addWidget(QLabel("历史:"))
        self.history_combo = QComboBox()
        self.history_combo.setMinimumWidth(150)
        self.history_combo.addItem("搜索历史")
        self.history_combo.currentIndexChanged.connect(self.load_search_history)
        criteria_layout.addWidget(self.history_combo)
        
        search_layout.addLayout(criteria_layout)
        
        # 高级选项
        advanced_layout = QHBoxLayout()
        
        # 文件大小范围
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("大小范围:"))
        
        self.min_size_spin = QSpinBox()
        self.min_size_spin.setRange(0, 1000000)
        self.min_size_spin.setSuffix(" KB")
        self.min_size_spin.setSpecialValueText("最小")
        size_layout.addWidget(self.min_size_spin)
        
        size_layout.addWidget(QLabel("到"))
        
        self.max_size_spin = QSpinBox()
        self.max_size_spin.setRange(0, 1000000)
        self.max_size_spin.setSuffix(" KB")
        self.max_size_spin.setSpecialValueText("最大")
        size_layout.addWidget(self.max_size_spin)
        
        advanced_layout.addLayout(size_layout)
        
        # 子目录选项
        self.subdirs_check = QCheckBox("包含子目录")
        self.subdirs_check.setChecked(True)
        advanced_layout.addWidget(self.subdirs_check)
        
        # 添加搜索按钮
        self.search_button = QPushButton("开始搜索")
        self.search_button.clicked.connect(self.start_search)
        advanced_layout.addWidget(self.search_button)
        
        # 添加停止按钮
        self.stop_button = QPushButton("停止")
        self.stop_button.clicked.connect(self.stop_search)
        self.stop_button.setEnabled(False)
        advanced_layout.addWidget(self.stop_button)
        
        search_layout.addLayout(advanced_layout)
        
        # 进度条
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("搜索进度:"))
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%v/%m 目录 (%p%)")
        progress_layout.addWidget(self.progress_bar)
        
        self.time_label = QLabel("时间: 00:00")
        progress_layout.addWidget(self.time_label)
        
        search_layout.addLayout(progress_layout)
        
        # 设置搜索组布局
        search_group.setLayout(search_layout)
        self.main_layout.addWidget(search_group)
    
    def create_table(self):
        # 创建表格组
        table_group = QGroupBox("搜索结果")
        table_layout = QVBoxLayout()
        
        # 创建结果计数标签和操作按钮区域
        results_button_layout = QHBoxLayout()
        
        self.results_label = QLabel("找到 0 个文件")
        results_button_layout.addWidget(self.results_label)
        
        results_button_layout.addStretch()
        
        # 添加删除选中文件按钮
        self.delete_button = QPushButton("删除选中文件")
        self.delete_button.clicked.connect(self.delete_selected_files)
        self.delete_button.setEnabled(False)  # 初始时禁用
        results_button_layout.addWidget(self.delete_button)
        
        # 添加查看删除记录按钮
        self.view_delete_history_button = QPushButton("查看删除记录")
        self.view_delete_history_button.clicked.connect(self.show_delete_history)
        results_button_layout.addWidget(self.view_delete_history_button)
        
        table_layout.addLayout(results_button_layout)
        
        # 创建表格
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["文件名", "路径", "类型", "大小", "创建时间", "修改时间", "完整路径"])
        
        # 设置表格列宽
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)  # 文件名列自适应
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # 路径列自适应
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 类型列自适应内容
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 大小列自适应内容
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 创建时间列自适应内容
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)  # 修改时间列自适应内容
        
        # 隐藏完整路径列（用于内部存储）
        self.table.hideColumn(6)
        
        # 设置表格上下文菜单
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # 双击打开文件
        self.table.cellDoubleClicked.connect(self.open_file)
        
        # 连接选中变化信号
        self.table.itemSelectionChanged.connect(self.update_delete_button_state)
        
        table_layout.addWidget(self.table)
        
        # 设置表格组布局
        table_group.setLayout(table_layout)
        self.main_layout.addWidget(table_group)
    
    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "选择搜索目录", self.path_edit.text())
        if directory:
            self.path_edit.setText(directory)
    
    def start_search(self):
        # 获取搜索路径
        search_path = self.path_edit.text()
        if not search_path or not os.path.isdir(search_path):
            QMessageBox.warning(self, "路径错误", "请选择一个有效的搜索目录")
            return
        
        # 获取搜索词
        search_term = self.search_edit.text()
        
        # 获取文件类型
        file_extensions = []
        file_type_index = self.file_type_combo.currentIndex()
        file_type_text = self.file_type_combo.currentText()
        
        if file_type_index == 1:  # 文档
            file_extensions = ["txt", "doc", "docx", "pdf", "rtf"]
        elif file_type_index == 2:  # 图片
            file_extensions = ["jpg", "jpeg", "png", "gif", "bmp"]
        elif file_type_index == 3:  # 音频
            file_extensions = ["mp3", "wav", "flac", "ogg"]
        elif file_type_index == 4:  # 视频
            file_extensions = ["mp4", "avi", "mkv", "mov"]
        elif file_type_index == 5:  # 压缩文件
            file_extensions = ["zip", "rar", "7z", "tar", "gz"]
        elif file_type_index == 6:  # 自定义
            custom_extensions, ok = QInputDialog.getText(self, "自定义文件类型", 
                                                    "输入文件扩展名（用逗号分隔，不含点号）:")
            if ok and custom_extensions:
                file_extensions = [ext.strip().lower() for ext in custom_extensions.split(',')]
            else:
                return
        
        # 获取文件大小范围
        min_size = self.min_size_spin.value()
        max_size = self.max_size_spin.value()
        
        # 获取是否搜索子目录
        search_subdirs = self.subdirs_check.isChecked()
        
        # 清空表格
        self.table.setRowCount(0)
        self.results_label.setText("找到 0 个文件")
        
        # 更新UI状态
        self.search_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.statusBar().showMessage('正在搜索...')
        
        # 重置进度条
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(100)  # 临时设置
        
        # 开始计时
        self.search_start_time = time.time()
        self.search_timer.start(1000)  # 每秒更新一次
        
        # 记录搜索历史
        search_record = {
            "path": search_path,
            "term": search_term,
            "file_type": file_type_text,
            "time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.add_to_search_history(search_record)
        
        # 创建并启动搜索线程
        self.search_thread = FileSearchThread(
            search_path, search_term, file_extensions, min_size, max_size, search_subdirs)
        self.search_thread.file_found.connect(self.add_file_to_table)
        self.search_thread.search_completed.connect(self.search_finished)
        self.search_thread.search_progress.connect(self.update_progress)
        self.search_thread.start()
    
    def stop_search(self):
        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.stop()
            self.search_thread.wait()  # 等待线程结束
            self.search_finished(self.table.rowCount())
    
    def add_file_to_table(self, full_path, file_name, ext, file_size, created_time, modified_time, file_type):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # 设置文件名
        self.table.setItem(row, 0, QTableWidgetItem(file_name))
        
        # 设置文件路径（显示相对路径）
        dir_path = os.path.dirname(full_path)
        self.table.setItem(row, 1, QTableWidgetItem(dir_path))
        
        # 设置文件类型
        self.table.setItem(row, 2, QTableWidgetItem(file_type))
        
        # 设置文件大小（格式化）
        size_str = self.format_size(file_size)
        self.table.setItem(row, 3, QTableWidgetItem(size_str))
        
        # 设置创建时间
        self.table.setItem(row, 4, QTableWidgetItem(created_time))
        
        # 设置修改时间
        self.table.setItem(row, 5, QTableWidgetItem(modified_time))
        
        # 存储完整路径（隐藏列）
        self.table.setItem(row, 6, QTableWidgetItem(full_path))
        
        # 更新结果计数
        self.results_label.setText(f"找到 {row + 1} 个文件")
    
    def search_finished(self, count):
        # 停止计时器
        self.search_timer.stop()
        
        # 更新UI状态
        self.search_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
        # 更新状态栏
        elapsed_time = time.time() - self.search_start_time
        self.statusBar().showMessage(f'搜索完成，找到 {count} 个文件，用时 {self.format_time(elapsed_time)}')
        
        # 更新进度条
        self.progress_bar.setValue(self.progress_bar.maximum())
    
    def update_progress(self, current, total):
        if total > 0:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
    
    def update_search_time(self):
        elapsed_time = time.time() - self.search_start_time
        self.time_label.setText(f"时间: {self.format_time(elapsed_time)}")
    
    def show_context_menu(self, position):
        # 获取当前选中的行
        row = self.table.rowAt(position.y())
        if row < 0:
            return
        
        # 创建上下文菜单
        context_menu = QMenu(self)
        
        # 添加菜单项
        open_file_action = QAction("打开文件", self)
        open_folder_action = QAction("打开所在文件夹", self)
        copy_path_action = QAction("复制文件路径", self)
        delete_file_action = QAction("删除文件", self)
        
        # 连接信号
        open_file_action.triggered.connect(lambda: self.open_file(row, 0))
        open_folder_action.triggered.connect(lambda: self.open_folder(row))
        copy_path_action.triggered.connect(lambda: self.copy_path(row))
        delete_file_action.triggered.connect(lambda: self.delete_file(row))
        
        # 添加到菜单
        context_menu.addAction(open_file_action)
        context_menu.addAction(open_folder_action)
        context_menu.addAction(copy_path_action)
        context_menu.addSeparator()
        context_menu.addAction(delete_file_action)
        
        # 显示菜单
        context_menu.exec_(QCursor.pos())
    
    def update_delete_button_state(self):
        # 更新删除按钮状态
        selected_items = self.table.selectedItems()
        self.delete_button.setEnabled(len(selected_items) > 0)
    
    def delete_file(self, row):
        # 获取文件路径
        file_path = self.table.item(row, 6).text()
        file_name = self.table.item(row, 0).text()
        
        # 确认删除
        reply = QMessageBox.question(self, "确认删除", 
                                   f"确定要删除文件 '{file_name}' 吗?", 
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                # 尝试删除文件
                os.remove(file_path)
                
                # 记录删除操作
                delete_record = {
                    "file_name": file_name,
                    "file_path": file_path,
                    "time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.delete_history.append(delete_record)
                self.save_history_to_file()  # 保存历史记录
                
                # 从表格中移除
                self.table.removeRow(row)
                
                # 更新结果计数
                count = self.table.rowCount()
                self.results_label.setText(f"找到 {count} 个文件")
                
                # 显示成功消息
                self.statusBar().showMessage(f'文件 "{file_name}" 已成功删除', 3000)
            except Exception as e:
                QMessageBox.critical(self, "删除失败", f"无法删除文件: {e}")
    
    def delete_selected_files(self):
        # 获取选中的行
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            return
        
        # 确认删除
        file_count = len(selected_rows)
        reply = QMessageBox.question(self, "确认删除", 
                                   f"确定要删除选中的 {file_count} 个文件吗?", 
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # 从大到小排序行号，以避免删除时索引变化
            rows = sorted(list(selected_rows), reverse=True)
            deleted_count = 0
            failed_files = []
            
            for row in rows:
                try:
                    # 获取文件路径
                    file_path = self.table.item(row, 6).text()
                    file_name = self.table.item(row, 0).text()
                    
                    # 删除文件
                    os.remove(file_path)
                    
                    # 记录删除操作
                    delete_record = {
                        "file_name": file_name,
                        "file_path": file_path,
                        "time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    self.delete_history.append(delete_record)
                    
                    # 从表格中移除
                    self.table.removeRow(row)
                    deleted_count += 1
                except Exception as e:
                    failed_files.append((self.table.item(row, 0).text(), str(e)))
            
            # 更新结果计数
            count = self.table.rowCount()
            self.results_label.setText(f"找到 {count} 个文件")
            
            # 显示结果消息
            if deleted_count == file_count:
                self.statusBar().showMessage(f'成功删除 {deleted_count} 个文件', 3000)
            elif deleted_count > 0:
                QMessageBox.warning(self, "部分删除成功", 
                                 f"成功删除 {deleted_count} 个文件\n"
                                 f"失败: {len(failed_files)} 个文件")
            else:
                error_details = "\n".join([f"{name}: {error}" for name, error in failed_files[:5]])
                if len(failed_files) > 5:
                    error_details += f"\n... 及其他 {len(failed_files) - 5} 个文件"
                    
                QMessageBox.critical(self, "删除失败", 
                                  f"无法删除文件:\n{error_details}")
            
            # 保存历史记录
            self.save_history_to_file()
    
    def open_file(self, row, column):
        # 获取文件路径
        file_path = self.table.item(row, 6).text()
        
        # 根据操作系统打开文件
        try:
            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(['open', file_path])
            else:  # Linux
                subprocess.call(['xdg-open', file_path])
        except Exception as e:
            QMessageBox.warning(self, "打开文件失败", f"无法打开文件: {e}")
    
    def open_folder(self, row):
        # 获取文件路径
        file_path = self.table.item(row, 6).text()
        folder_path = os.path.dirname(file_path)
        
        # 根据操作系统打开文件夹
        try:
            if platform.system() == 'Windows':
                os.startfile(folder_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(['open', folder_path])
            else:  # Linux
                subprocess.call(['xdg-open', folder_path])
        except Exception as e:
            QMessageBox.warning(self, "打开文件夹失败", f"无法打开文件夹: {e}")
    
    def copy_path(self, row):
        # 获取文件路径
        file_path = self.table.item(row, 6).text()
        
        # 复制到剪贴板
        clipboard = QApplication.clipboard()
        clipboard.setText(file_path)
        
        self.statusBar().showMessage('文件路径已复制到剪贴板', 3000)
    
    def closeEvent(self, event):
        # 保存历史记录
        self.save_history_to_file()
        event.accept()
    
    def format_size(self, size_bytes):
        # 格式化文件大小
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
    
    def format_time(self, seconds):
        # 格式化时间
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def add_to_search_history(self, record):
        # 避免重复记录
        for i, hist in enumerate(self.search_history):
            if hist["path"] == record["path"] and hist["term"] == record["term"]:
                self.search_history.pop(i)
                break
        
        # 添加到历史记录
        self.search_history.insert(0, record)
        
        # 限制历史记录数量
        if len(self.search_history) > 20:
            self.search_history = self.search_history[:20]
        
        # 更新下拉菜单
        self.update_history_combo()
        
        # 保存历史记录
        self.save_history_to_file()
    
    def update_history_combo(self):
        self.history_combo.clear()
        self.history_combo.addItem("搜索历史")
        
        for record in self.search_history:
            display_text = f"{record['time']} - {record['term'] or '所有文件'} in {os.path.basename(record['path'])}"
            self.history_combo.addItem(display_text, record)
    
    def load_search_history(self, index):
        if index <= 0:
            return
        
        # 获取选中的历史记录
        record = self.history_combo.itemData(index)
        
        # 填充搜索条件
        self.path_edit.setText(record["path"])
        self.search_edit.setText(record["term"])
        
        # 设置文件类型
        for i in range(self.file_type_combo.count()):
            if self.file_type_combo.itemText(i) == record["file_type"]:
                self.file_type_combo.setCurrentIndex(i)
                break
        
        # 重置下拉菜单
        self.history_combo.setCurrentIndex(0)
    
    def load_history_from_file(self):
        try:
            history_file = os.path.join(os.path.expanduser("~"), ".file_searcher_history.json")
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.search_history = data.get("search_history", [])
                    self.delete_history = data.get("delete_history", [])
                    self.update_history_combo()
        except Exception as e:
            print(f"加载历史记录失败: {e}")
    
    def save_history_to_file(self):
        try:
            history_file = os.path.join(os.path.expanduser("~"), ".file_searcher_history.json")
            with open(history_file, 'w', encoding='utf-8') as f:
                data = {
                    "search_history": self.search_history,
                    "delete_history": self.delete_history
                }
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史记录失败: {e}")
    
    def show_delete_history(self):
        # 创建删除历史对话框
        dialog = DeleteHistoryDialog(self.delete_history, self)
        dialog.exec_()


class DeleteHistoryDialog(QDialog):
    def __init__(self, history, parent=None):
        super().__init__(parent)
        self.setWindowTitle("删除记录")
        self.setMinimumSize(700, 400)
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 创建表格
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["文件名", "文件路径", "删除时间"])
        
        # 设置表格列宽
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        # 填充表格
        for record in history:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(record["file_name"]))
            self.table.setItem(row, 1, QTableWidgetItem(record["file_path"]))
            self.table.setItem(row, 2, QTableWidgetItem(record["time"]))
        
        layout.addWidget(self.table)
        
        # 添加按钮
        button_layout = QHBoxLayout()
        
        clear_button = QPushButton("清空记录")
        clear_button.clicked.connect(self.clear_history)
        
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        
        button_layout.addWidget(clear_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
    
    def clear_history(self):
        reply = QMessageBox.question(self, "确认清空", 
                                   "确定要清空所有删除记录吗?", 
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.parent().delete_history = []
            self.table.setRowCount(0)
            self.parent().save_history_to_file()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileSearcher()
    window.show()
    sys.exit(app.exec_())
