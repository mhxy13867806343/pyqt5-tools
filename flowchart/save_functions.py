#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtGui import QColor

def save_flowchart(editor):
    """保存思维导图"""
    if not editor.current_file:
        return save_flowchart_as(editor)
    
    try:
        # 收集节点和连接数据
        data = {"nodes": [], "connections": []}
        
        # 节点ID映射
        node_to_id = {}
        node_id = 0
        
        # 收集节点数据
        for item in editor.scene.items():
            if hasattr(item, 'node_type'):  # 检查是否是FlowchartNode
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
        for item in editor.scene.items():
            if hasattr(item, 'start_node') and hasattr(item, 'end_node'):  # 检查是否是FlowchartConnection
                if item.start_node in node_to_id and item.end_node in node_to_id:
                    conn_data = {
                        "start": node_to_id[item.start_node],
                        "end": node_to_id[item.end_node],
                        "color": item.color.name(),
                        "width": item.pen().width()
                    }
                    data["connections"].append(conn_data)
        
        # 保存为JSON文件
        with open(editor.current_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # 重置修改状态
        editor.setModified(False)
        
        editor.statusBar().showMessage(f"已保存到 {editor.current_file}")
        return True
        
    except Exception as e:
        QMessageBox.critical(editor, "错误", f"保存失败: {str(e)}")
        return False

def save_flowchart_as(editor):
    """思维导图另存为"""
    file_path, _ = QFileDialog.getSaveFileName(
        editor, "思维导图另存为", "", "思维导图文件 (*.flow);;所有文件 (*)")
    
    if not file_path:
        return False
    
    # 确保文件扩展名
    if not file_path.endswith('.flow'):
        file_path += '.flow'
    
    editor.current_file = file_path
    return save_flowchart(editor)  # 调用保存方法
