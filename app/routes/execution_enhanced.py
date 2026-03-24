#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#-------------------------------------------------------------
Name    : execution_enhanced.py
Time    : 2026/3/24
Author  : xixi
File    : app/routes
Description: 增强的执行记录API - 支持WebSocket实时更新和JSON格式测试步骤
#-------------------------------------------------------------
"""
import json
import time
import random
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_socketio import emit, join_room
from .. import db, socketio
from ..models import TestCase, ExecutionResult, Report, Project
from ..websocket_handler import (
    send_execution_progress, 
    send_test_case_result,
    send_execution_completed,
    broadcast_test_run_update
)

execution_enhanced_bp = Blueprint('execution_enhanced', __name__)

# REST API: 获取执行记录列表
@execution_enhanced_bp.route('/', methods=['GET'], strict_slashes=False)
def list_executions():
    """获取执行记录列表"""
    testcase_id = request.args.get('testcase_id')
    project_id = request.args.get('project_id')
    limit = request.args.get('limit', default=50, type=int)
    status = request.args.get('status')
    
    query = ExecutionResult.query
    
    if testcase_id:
        query = query.filter_by(testcase_id=testcase_id)
    
    if project_id:
        # 通过测试用例关联项目
        query = query.join(TestCase).filter(TestCase.project_id == project_id)
    
    if status:
        query = query.filter_by(status=status)
    
    executions = query.order_by(ExecutionResult.started_at.desc()).limit(limit).all()
    
    result = []
    for e in executions:
        testcase = TestCase.query.get(e.testcase_id) if e.testcase_id else None
        
        # 解析测试步骤（如果是JSON格式）
        test_steps = []
        if testcase and testcase.steps:
            try:
                test_steps = json.loads(testcase.steps)
            except:
                test_steps = []
        
        result.append({
            'id': e.id,
            'testcase_id': e.testcase_id,
            'testcase_name': testcase.name if testcase else '未知用例',
            'project_id': testcase.project_id if testcase else None,
            'project_name': testcase.project.name if testcase and testcase.project else None,
            'status': e.status,
            'result': e.result,
            'progress': e.progress or 0,
            'total_tests': e.total_tests or 0,
            'passed': e.passed or 0,
            'failed': e.failed or 0,
            'skipped': e.skipped or 0,
            'started_at': e.started_at.isoformat() if e.started_at else None,
            'finished_at': e.finished_at.isoformat() if e.finished_at else None,
            'duration': (e.finished_at - e.started_at).total_seconds() if e.started_at and e.finished_at else None,
            'log': e.log,
            'test_steps': test_steps,  # 包含测试步骤信息
            'created_at': e.created_at.isoformat() if e.created_at else None
        })
    
    return jsonify({
        'code': 200,
        'message': '成功',
        'data': result,
        'count': len(result),
        'timestamp': datetime.now().isoformat()
    })

# REST API: 获取单个执行记录详情
@execution_enhanced_bp.route('/<int:exec_id>', methods=['GET'], strict_slashes=False)
def get_execution_detail(exec_id):
    """获取执行记录详情"""
    execution = ExecutionResult.query.get_or_404(exec_id)
    testcase = TestCase.query.get(execution.testcase_id) if execution.testcase_id else None
    
    # 解析测试步骤
    test_steps = []
    if testcase and testcase.steps:
        try:
            test_steps = json.loads(testcase.steps)
        except:
            test_steps = []
    
    # 获取关联的报告
    reports = Report.query.filter_by(execution_id=exec_id).all()
    
    return jsonify({
        'code': 200,
        'message': '成功',
        'data': {
            'execution': {
                'id': execution.id,
                'testcase_id': execution.testcase_id,
                'testcase_name': testcase.name if testcase else '未知用例',
                'status': execution.status,
                'result': execution.result,
                'progress': execution.progress or 0,
                'total_tests': execution.total_tests or 0,
                'passed': execution.passed or 0,
                'failed': execution.failed or 0,
                'skipped': execution.skipped or 0,
                'started_at': execution.started_at.isoformat() if execution.started_at else None,
                'finished_at': execution.finished_at.isoformat() if execution.finished_at else None,
                'duration': (execution.finished_at - execution.started_at).total_seconds() if execution.started_at and execution.finished_at else None,
                'log': execution.log,
                'created_at': execution.created_at.isoformat() if execution.created_at else None
            },
            'testcase': {
                'id': testcase.id if testcase else None,
                'name': testcase.name if testcase else None,
                'description': testcase.description if testcase else None,
                'steps': test_steps,  # JSON格式的测试步骤
                'expected_result': testcase.expected_result if testcase else None,
                'project_id': testcase.project_id if testcase else None,
                'project_name': testcase.project.name if testcase and testcase.project else None
            },
            'reports': [{
                'id': r.id,
                'content': r.content,
                'html_content': r.html_content[:500] + '...' if r.html_content and len(r.html_content) > 500 else r.html_content,
                'created_at': r.created_at.isoformat() if r.created_at else None
            } for r in reports]
        },
        'timestamp': datetime.now().isoformat()
    })

# REST API: 创建新的执行记录
@execution_enhanced_bp.route('/', methods=['POST'], strict_slashes=False)
def create_execution():
    """创建新的执行记录"""
    data = request.json
    testcase_id = data.get('testcase_id')
    
    if not testcase_id:
        return jsonify({
            'code': 400,
            'message': '需要testcase_id参数',
            'data': None
        }), 400
    
    testcase = TestCase.query.get(testcase_id)
    if not testcase or testcase.is_deleted:
        return jsonify({
            'code': 404,
            'message': '测试用例不存在或已被删除',
            'data': None
        }), 404
    
    # 创建执行记录
    execution = ExecutionResult(
        testcase_id=testcase_id,
        status='pending',
        progress=0,
        total_tests=0,
        passed=0,
        failed=0,
        skipped=0,
        started_at=datetime.now()
    )
    
    db.session.add(execution)
    db.session.commit()
    
    # 广播新执行记录创建
    broadcast_test_run_update({
        'type': 'execution_created',
        'execution_id': execution.id,
        'testcase_id': testcase_id,
        'testcase_name': testcase.name,
        'project_id': testcase.project_id,
        'status': 'pending',
        'started_at': execution.started_at.isoformat() if execution.started_at else None,
        'timestamp': datetime.now().isoformat()
    })
    
    # 启动后台执行任务
    from .execution_tasks import start_test_execution
    socketio.start_background_task(start_test_execution, execution.id, testcase_id)
    
    return jsonify({
        'code': 201,
        'message': '执行记录创建成功，开始执行',
        'data': {
            'execution_id': execution.id,
            'testcase_id': testcase_id,
            'testcase_name': testcase.name,
            'status': 'pending',
            'websocket_room': f'execution_{execution.id}',
            'started_at': execution.started_at.isoformat() if execution.started_at else None
        },
        'timestamp': datetime.now().isoformat()
    }), 201

# REST API: 批量执行测试用例
@execution_enhanced_bp.route('/batch', methods=['POST'], strict_slashes=False)
def create_batch_execution():
    """批量执行测试用例"""
    data = request.json
    testcase_ids = data.get('testcase_ids', [])
    project_id = data.get('project_id')
    
    if not testcase_ids and not project_id:
        return jsonify({
            'code': 400,
            'message': '需要testcase_ids或project_id参数',
            'data': None
        }), 400
    
    # 获取测试用例列表
    if project_id:
        # 执行整个项目的测试用例
        testcases = TestCase.query.filter_by(
            project_id=project_id,
            is_deleted=False
        ).all()
        testcase_ids = [tc.id for tc in testcases]
    
    if not testcase_ids:
        return jsonify({
            'code': 400,
            'message': '没有找到可执行的测试用例',
            'data': None
        }), 400
    
    # 创建批量执行记录
    batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    executions = []
    
    for tc_id in testcase_ids:
        testcase = TestCase.query.get(tc_id)
        if testcase and not testcase.is_deleted:
            execution = ExecutionResult(
                testcase_id=tc_id,
                status='pending',
                progress=0,
                total_tests=0,
                passed=0,
                failed=0,
                skipped=0,
                batch_id=batch_id,
                started_at=datetime.now()
            )
            db.session.add(execution)
            executions.append({
                'execution_id': execution.id,
                'testcase_id': tc_id,
                'testcase_name': testcase.name
            })
    
    db.session.commit()
    
    # 启动批量执行任务
    from .execution_tasks import start_batch_execution
    socketio.start_background_task(start_batch_execution, batch_id, testcase_ids)
    
    return jsonify({
        'code': 201,
        'message': f'批量执行创建成功，共{len(executions)}个测试用例',
        'data': {
            'batch_id': batch_id,
            'executions': executions,
            'total_count': len(executions),
            'websocket_room': f'batch_{batch_id}',
            'timestamp': datetime.now().isoformat()
        }
    }), 201

# REST API: 获取执行统计
@execution_enhanced_bp.route('/stats', methods=['GET'], strict_slashes=False)
def get_execution_stats():
    """获取执行统计信息"""
    project_id = request.args.get('project_id')
    days = request.args.get('days', default=30, type=int)
    
    # 计算时间范围
    from datetime import timedelta
    start_date = datetime.now() - timedelta(days=days)
    
    query = ExecutionResult.query.filter(ExecutionResult.started_at >= start_date)
    
    if project_id:
        query = query.join(TestCase).filter(TestCase.project_id == project_id)
    
    executions = query.all()
    
    # 统计信息
    total = len(executions)
    passed = sum(1 for e in executions if e.status == 'passed')
    failed = sum(1 for e in executions if e.status == 'failed')
    running = sum(1 for e in executions if e.status == 'running')
    pending = sum(1 for e in executions if e.status == 'pending')
    
    # 成功率
    success_rate = (passed / total * 100) if total > 0 else 0
    
    # 每日统计
    daily_stats = {}
    for e in executions:
        date_str = e.started_at.date().isoformat() if e.started_at else 'unknown'
        if date_str not in daily_stats:
            daily_stats[date_str] = {'total': 0, 'passed': 0, 'failed': 0}
        
        daily_stats[date_str]['total'] += 1
        if e.status == 'passed':
            daily_stats[date_str]['passed'] += 1
        elif e.status == 'failed':
            daily_stats[date_str]['failed'] += 1
    
    # 转换为列表
    daily_list = [
        {
            'date': date,
            'total': stats['total'],
            'passed': stats['passed'],
            'failed': stats['failed'],
            'success_rate': (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
        }
        for date, stats in sorted(daily_stats.items())
    ]
    
    return jsonify({
        'code': 200,
        'message': '成功',
        'data': {
            'total': total,
            'passed': passed,
            'failed': failed,
            'running': running,
            'pending': pending,
            'success_rate': round(success_rate, 2),
            'time_range': {
                'days': days,
                'start_date': start_date.isoformat(),
                'end_date': datetime.now().isoformat()
            },
            'daily_stats': daily_list,
            'timestamp': datetime.now().isoformat()
        }
    })

# WebSocket事件处理
@socketio.on('subscribe_execution')
def handle_subscribe_execution(data):
    """订阅执行记录更新"""
    execution_id = data.get('execution_id')
    client_id = request.sid
    
    if not execution_id:
        emit('error', {'message': '需要execution_id参数'})
        return
    
    room_name = f'execution_{execution_id}'
    join_room(room_name)
    
    # 发送当前状态
    execution = ExecutionResult.query.get(execution_id)
    if execution:
        emit('execution_status', {
            'execution_id': execution.id,
            'status': execution.status,
            'progress': execution.progress or 0,
            'total_tests': execution.total_tests or 0,
            'passed': execution.passed or 0,
            'failed': execution.failed or 0,
            'skipped': execution.skipped or 0,
            'started_at': execution.started_at.isoformat() if execution.started_at else None,
            'finished_at': execution.finished_at.isoformat() if execution.finished_at else None,
            'timestamp': datetime.now().isoformat()
        }, room=client_id)
    
    emit('subscribed', {
        'execution_id': execution_id,
        'room': room_name,
        'message': '已订阅执行记录更新',
        'timestamp': datetime.now().isoformat()
    }, room=client_id)

@socketio.on('unsubscribe_execution')
def handle_unsubscribe_execution(data):
    """取消订阅执行记录更新"""
    execution_id = data.get('execution_id')
    
    if execution_id:
        room_name = f'execution_{execution_id}'
        leave_room(room_name)
        
        emit('unsubscribed', {
            'execution_id': execution_id,
            'room': room_name,
            'message': '已取消订阅执行记录更新'
        })

@socketio.on('request_realtime_updates')
def handle_request_realtime_updates():
    """请求实时更新"""
    join_room('realtime_updates')
    
    emit('realtime_subscribed', {
        'message': '已订阅实时更新',
        'channels': ['test_runs', 'execution_progress', 'system_status'],
        'timestamp': datetime.now().isoformat()
    })