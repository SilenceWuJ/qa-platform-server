#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#-------------------------------------------------------------
Name    : websocket_handler.py
Time    : 2026/3/24
Author  : xixi
File    : app
Description: WebSocket处理器 - 实时执行记录推送
#-------------------------------------------------------------
"""
import json
from datetime import datetime
from flask import request
from flask_socketio import emit, join_room, leave_room
from . import socketio

# 存储连接的客户端
connected_clients = {}

@socketio.on('connect')
def handle_connect():
    """客户端连接事件"""
    client_id = request.sid
    connected_clients[client_id] = {
        'connected_at': datetime.now(),
        'rooms': []
    }
    print(f"客户端连接: {client_id}")
    emit('connection_established', {
        'message': '连接成功',
        'client_id': client_id,
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开连接事件"""
    client_id = request.sid
    if client_id in connected_clients:
        del connected_clients[client_id]
    print(f"客户端断开: {client_id}")

@socketio.on('join_execution_room')
def handle_join_execution_room(data):
    """加入执行记录房间"""
    client_id = request.sid
    execution_id = data.get('execution_id')
    
    if not execution_id:
        emit('error', {'message': '需要execution_id参数'})
        return
    
    room_name = f'execution_{execution_id}'
    join_room(room_name)
    
    if client_id in connected_clients:
        connected_clients[client_id]['rooms'].append(room_name)
    
    emit('room_joined', {
        'room': room_name,
        'execution_id': execution_id,
        'timestamp': datetime.now().isoformat()
    })
    print(f"客户端 {client_id} 加入房间 {room_name}")

@socketio.on('leave_execution_room')
def handle_leave_execution_room(data):
    """离开执行记录房间"""
    client_id = request.sid
    execution_id = data.get('execution_id')
    
    if execution_id:
        room_name = f'execution_{execution_id}'
        leave_room(room_name)
        
        if client_id in connected_clients and room_name in connected_clients[client_id]['rooms']:
            connected_clients[client_id]['rooms'].remove(room_name)
        
        emit('room_left', {
            'room': room_name,
            'execution_id': execution_id
        })

@socketio.on('subscribe_test_runs')
def handle_subscribe_test_runs():
    """订阅测试执行更新"""
    client_id = request.sid
    join_room('test_runs_updates')
    
    if client_id in connected_clients:
        connected_clients[client_id]['rooms'].append('test_runs_updates')
    
    emit('subscribed', {
        'channel': 'test_runs_updates',
        'message': '已订阅测试执行更新',
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('unsubscribe_test_runs')
def handle_unsubscribe_test_runs():
    """取消订阅测试执行更新"""
    client_id = request.sid
    leave_room('test_runs_updates')
    
    if client_id in connected_clients and 'test_runs_updates' in connected_clients[client_id]['rooms']:
        connected_clients[client_id]['rooms'].remove('test_runs_updates')
    
    emit('unsubscribed', {
        'channel': 'test_runs_updates',
        'message': '已取消订阅测试执行更新'
    })

@socketio.on('request_execution_status')
def handle_request_execution_status(data):
    """请求执行状态"""
    from .models.execution_result import ExecutionResult
    from . import db
    
    execution_id = data.get('execution_id')
    
    if not execution_id:
        emit('error', {'message': '需要execution_id参数'})
        return
    
    try:
        execution = ExecutionResult.query.get(execution_id)
        if execution:
            emit('execution_status', {
                'execution_id': execution.id,
                'status': execution.status,
                'progress': execution.progress,
                'total_tests': execution.total_tests,
                'passed': execution.passed,
                'failed': execution.failed,
                'started_at': execution.started_at.isoformat() if execution.started_at else None,
                'finished_at': execution.finished_at.isoformat() if execution.finished_at else None,
                'timestamp': datetime.now().isoformat()
            })
        else:
            emit('error', {'message': f'执行记录 {execution_id} 不存在'})
    except Exception as e:
        emit('error', {'message': f'获取执行状态失败: {str(e)}'})

# 工具函数：发送实时更新
def broadcast_test_run_update(test_run_data):
    """广播测试执行更新"""
    socketio.emit('test_run_updated', test_run_data, room='test_runs_updates')
    print(f"广播测试执行更新: {test_run_data.get('id')}")

def send_execution_progress(execution_id, progress_data):
    """发送执行进度更新"""
    room_name = f'execution_{execution_id}'
    socketio.emit('execution_progress', progress_data, room=room_name)

def send_test_case_result(execution_id, testcase_result):
    """发送测试用例结果"""
    room_name = f'execution_{execution_id}'
    socketio.emit('testcase_result', testcase_result, room=room_name)

def send_execution_completed(execution_id, summary_data):
    """发送执行完成通知"""
    room_name = f'execution_{execution_id}'
    socketio.emit('execution_completed', summary_data, room=room_name)
    
    # 同时广播到测试执行更新房间
    socketio.emit('test_run_completed', {
        'execution_id': execution_id,
        **summary_data
    }, room='test_runs_updates')

# 系统状态广播
def broadcast_system_status():
    """广播系统状态"""
    status_data = {
        'timestamp': datetime.now().isoformat(),
        'connected_clients': len(connected_clients),
        'active_rooms': len(set([room for client in connected_clients.values() for room in client['rooms']])),
        'system_status': 'healthy'
    }
    socketio.emit('system_status', status_data)

# 初始化WebSocket事件
def init_websocket_events():
    """初始化WebSocket事件处理器"""
    print("WebSocket事件处理器已初始化")
    
    # 定期广播系统状态（每30秒）
    @socketio.on('request_system_status')
    def handle_request_system_status():
        broadcast_system_status()