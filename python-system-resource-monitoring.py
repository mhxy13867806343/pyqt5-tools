import sys
import platform
import psutil
import subprocess
import re
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                            QLabel, QProgressBar, QHBoxLayout, QGroupBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QPalette


class SystemMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('系统资源监控')
        self.setMinimumSize(600, 500)  # 增加窗口大小以适应更多内容
        
        # 设置主窗口部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        

        
        # 添加系统信息
        self.setup_system_info()
        

        
        # 添加CPU使用率
        self.setup_cpu_usage()
        
        # 添加内存使用情况
        self.setup_memory_usage()
        
        # 添加磁盘使用情况
        self.setup_disk_usage()
        
        # 更新定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(2000)  # 每2秒更新一次
        

        
        self.update_stats()  # 初始更新
    
    def closeEvent(self, event):
        """关闭窗口时的处理"""
        event.accept()
        
    def setup_system_info(self):
        """设置系统信息显示"""
        group = QGroupBox("系统信息")
        layout = QVBoxLayout()
        
        # 操作系统信息
        os_name = platform.system()
        os_version = platform.version()
        os_arch = platform.machine()
        
        # 判断系统类型
        if os_name == "Darwin":
            os_display = "macOS"
        elif os_name == "Windows":
            os_display = "Windows"
        else:
            os_display = os_name
            
        self.os_label = QLabel(f"操作系统: {os_display} {platform.mac_ver()[0] if os_name == 'Darwin' else platform.win32_ver()[0] if os_name == 'Windows' else ''}")
        self.arch_label = QLabel(f"系统架构: {os_arch}")
        self.python_label = QLabel(f"Python版本: {platform.python_version()}")
        
        layout.addWidget(self.os_label)
        layout.addWidget(self.arch_label)
        layout.addWidget(self.python_label)
        
        group.setLayout(layout)
        self.layout.addWidget(group)
        

        

    

    
    def set_progress_bar_style(self, progress_bar, color):
        """设置进度条样式"""
        # 创建调色板
        palette = QPalette()
        # 设置进度条颜色
        palette.setColor(QPalette.Highlight, QColor(color))
        # 应用调色板
        progress_bar.setPalette(palette)
        # 设置样式表
        progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #bbb;
                border-radius: 4px;
                text-align: center;
                height: 20px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """)
    
    def setup_cpu_usage(self):
        """设置CPU使用率显示"""
        group = QGroupBox("CPU 使用率")
        layout = QVBoxLayout()
        
        self.cpu_percent = QProgressBar()
        self.cpu_percent.setMaximum(100)
        self.cpu_percent.setFormat("%p%")
        self.cpu_percent.setAlignment(Qt.AlignCenter)
        # 设置进度条颜色
        self.set_progress_bar_style(self.cpu_percent, "#e74c3c")  # 红色
        
        self.cpu_count_label = QLabel()
        
        layout.addWidget(QLabel(f"逻辑CPU核心数: {psutil.cpu_count()}, 物理CPU核心数: {psutil.cpu_count(logical=False) or '未知'}"))
        layout.addWidget(QLabel("CPU 使用率:"))
        layout.addWidget(self.cpu_percent)
        
        group.setLayout(layout)
        self.layout.addWidget(group)
        
    def setup_memory_usage(self):
        """设置内存使用情况显示"""
        group = QGroupBox("内存使用情况")
        layout = QVBoxLayout()
        
        self.memory_percent = QProgressBar()
        self.memory_percent.setMaximum(100)
        self.memory_percent.setAlignment(Qt.AlignCenter)
        self.memory_percent.setFormat("%p%")
        # 设置进度条颜色
        self.set_progress_bar_style(self.memory_percent, "#2ecc71")  # 绿色
        
        self.memory_label = QLabel()
        
        layout.addWidget(QLabel("内存使用:"))
        layout.addWidget(self.memory_percent)
        layout.addWidget(self.memory_label)
        
        group.setLayout(layout)
        self.layout.addWidget(group)
        
    def setup_disk_usage(self):
        """设置磁盘使用情况显示"""
        group = QGroupBox("磁盘使用情况")
        self.disk_layout = QVBoxLayout()
        
        # 获取所有磁盘分区
        self.disk_bars = {}
        
        # 检测操作系统类型
        os_name = platform.system()
        
        # 获取所有磁盘分区
        partitions = psutil.disk_partitions(all=False)
        
        # 如果是Windows系统，显示更友好的盘符号
        if os_name == "Windows":
            import string
            import os
            
            # 获取Windows上的磁盘
            drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
            for drive in drives:
                try:
                    usage = psutil.disk_usage(drive)
                    # 创建磁盘显示组
                    disk_name = f"磁盘 {drive} (本地磁盘)"
                    self._add_disk_display(disk_name, drive, usage)
                except Exception as e:
                    print(f"Error getting disk usage for {drive}: {e}")
        else:  # macOS或Linux
            for part in partitions:
                if 'cdrom' in part.opts or part.fstype == '':
                    continue
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    
                    # 优化macOS磁盘显示
                    if os_name == "Darwin":
                        # 尝试获取更友好的名称
                        if part.mountpoint == "/":
                            disk_name = "磁盘 Macintosh HD (系统盘)"
                        elif "/Volumes/" in part.mountpoint:
                            volume_name = part.mountpoint.split("/")[-1]
                            disk_name = f"磁盘 {volume_name}"
                        else:
                            disk_name = f"磁盘 {part.device} ({part.mountpoint})"
                    else:  # Linux或其他系统
                        disk_name = f"磁盘 {part.device} ({part.mountpoint})"
                    
                    self._add_disk_display(disk_name, part.mountpoint, usage)
                except Exception as e:
                    print(f"Error getting disk usage for {part.mountpoint}: {e}")
        
        group.setLayout(self.disk_layout)
        self.layout.addWidget(group)
    
    def _add_disk_display(self, disk_name, mount_point, usage):
        """添加磁盘显示组件"""
        disk_group = QGroupBox(disk_name)
        disk_layout = QHBoxLayout()  # 使用水平布局更美观
        
        # 左侧信息区
        info_layout = QVBoxLayout()
        
        # 添加容量信息
        capacity_label = QLabel(f"总容量: {self.format_bytes(usage.total)}")
        free_label = QLabel(f"可用空间: {self.format_bytes(usage.free)}")
        used_label = QLabel(f"已用空间: {self.format_bytes(usage.used)}")
        percent_label = QLabel(f"使用率: {usage.percent}%")
        
        info_layout.addWidget(capacity_label)
        info_layout.addWidget(free_label)
        info_layout.addWidget(used_label)
        info_layout.addWidget(percent_label)
        
        # 右侧进度条
        progress_layout = QVBoxLayout()
        
        disk_bar = QProgressBar()
        disk_bar.setMaximum(100)
        disk_bar.setAlignment(Qt.AlignCenter)
        disk_bar.setFixedHeight(20)  # 设置固定高度
        disk_bar.setMinimumWidth(150)  # 设置最小宽度
        disk_bar.setFormat("%p%")
        # 设置进度条颜色 - 每个磁盘使用不同颜色
        self.set_progress_bar_style(disk_bar, "#9b59b6")  # 紫色
        
        # 添加一些空白使进度条垂直居中
        progress_layout.addStretch()
        progress_layout.addWidget(disk_bar)
        progress_layout.addStretch()
        
        # 将信息区和进度条添加到水平布局
        disk_layout.addLayout(info_layout)
        disk_layout.addLayout(progress_layout)
        
        disk_group.setLayout(disk_layout)
        self.disk_layout.addWidget(disk_group)
        
        # 存储引用以便更新
        self.disk_bars[mount_point] = (disk_bar, percent_label, capacity_label, free_label, used_label)
        
    def update_stats(self):
        """更新统计信息"""
        # 更新CPU使用率
        cpu_percent = psutil.cpu_percent(interval=0.1)  # 缩短间隔以加快更新
        self.cpu_percent.setValue(int(cpu_percent))
        
        # 更新内存使用情况
        memory = psutil.virtual_memory()
        self.memory_percent.setValue(int(memory.percent))
        self.memory_label.setText(
            f"已用: {self.format_bytes(memory.used)} / "
            f"总共: {self.format_bytes(memory.total)} "
            f"({memory.percent}%)"
        )
        
        # 更新磁盘使用情况
        self._update_disk_usage()
    
    def _update_disk_usage(self):
        """更新磁盘使用情况"""
        # 检测操作系统类型
        os_name = platform.system()
        
        if os_name == "Windows":
            import string
            import os
            # 获取Windows上的磁盘
            drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
            for drive in drives:
                if drive in self.disk_bars:
                    try:
                        usage = psutil.disk_usage(drive)
                        self._update_disk_display(drive, usage)
                    except Exception as e:
                        print(f"Error updating disk {drive}: {e}")
        else:
            # macOS或Linux
            for part in psutil.disk_partitions():
                if part.mountpoint in self.disk_bars:
                    try:
                        usage = psutil.disk_usage(part.mountpoint)
                        self._update_disk_display(part.mountpoint, usage)
                    except Exception as e:
                        print(f"Error updating disk {part.mountpoint}: {e}")
    
    def _update_disk_display(self, mount_point, usage):
        """更新磁盘显示信息"""
        if mount_point in self.disk_bars:
            disk_bar, percent_label, capacity_label, free_label, used_label = self.disk_bars[mount_point]
            disk_bar.setValue(int(usage.percent))
            percent_label.setText(f"使用率: {usage.percent}%")
            free_label.setText(f"可用空间: {self.format_bytes(usage.free)}")
            used_label.setText(f"已用空间: {self.format_bytes(usage.used)}")
            # 总容量一般不会变化，但为了完整性也更新
            capacity_label.setText(f"总容量: {self.format_bytes(usage.total)}")
    
    @staticmethod
    def format_bytes(bytes_num):
        """格式化字节大小为易读格式"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_num < 1024.0:
                return f"{bytes_num:.1f} {unit}"
            bytes_num /= 1024.0
        return f"{bytes_num:.1f} PB"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SystemMonitor()
    window.show()
    sys.exit(app.exec_())