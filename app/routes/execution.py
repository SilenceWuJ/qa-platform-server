#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#-------------------------------------------------------------
Name    : execution.py
Time    : 2026/3/20 
Author  : xixi
File    : app/routes
#-------------------------------------------------------------
"""
import time
import random
from datetime import datetime
import subprocess
import tempfile
import os
import json
from flask import current_app, Blueprint, request, jsonify, render_template
from flask_socketio import emit, join_room
from .. import db, socketio
from ..models import TestCase, ExecutionResult, Report

execution_bp = Blueprint('execution', __name__)

# REST 查看执行结果
@execution_bp.route('/', methods=['GET'],strict_slashes=False)
def list_executions():
    testcase_id = request.args.get('testcase_id')
    query = ExecutionResult.query
    if testcase_id:
        query = query.filter_by(testcase_id=testcase_id)
    executions = query.order_by(ExecutionResult.started_at.desc()).all()
    return jsonify([{
        'id': e.id,
        'testcase_id': e.testcase_id,
        'status': e.status,
        'result': e.result,
        'started_at': e.started_at.isoformat(),
        'finished_at': e.finished_at.isoformat() if e.finished_at else None,
        'log': e.log
    } for e in executions])

@execution_bp.route('/<int:exec_id>', methods=['GET'],strict_slashes=False)
def get_execution(exec_id):
    execution = ExecutionResult.query.get_or_404(exec_id)
    return jsonify({
        'id': execution.id,
        'testcase_id': execution.testcase_id,
        'status': execution.status,
        'result': execution.result,
        'started_at': execution.started_at.isoformat(),
        'finished_at': execution.finished_at.isoformat() if execution.finished_at else None,
        'log': execution.log
    })

# WebSocket 事件
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('join_room')
def handle_join_room(data):
    room = data.get('room')
    if room:
        join_room(room)
        print(f'Client joined room {room}')



@socketio.on('start_execution')
def handle_start_execution(data):
    testcase_id = data.get('testcase_id')
    room = data.get('room', f'exec_{testcase_id}')
    if not testcase_id:
        emit('error', {'message': 'testcase_id required'}, room=room)
        return
    app = current_app._get_current_object()
    socketio.start_background_task(run_testcase, testcase_id, room, app)

def run_testcase(testcase_id, room, app):
    with app.app_context():
        testcase = TestCase.query.get(testcase_id)
        if not testcase or testcase.is_deleted:
            socketio.emit('execution_error', {'message': 'Test case not found'}, room=room)
            return

        execution = ExecutionResult(
            testcase_id=testcase_id,
            status='running',
            started_at=datetime.utcnow()
        )
        db.session.add(execution)
        db.session.commit()

        socketio.emit('execution_started', {
            'execution_id': execution.id,
            'testcase_name': testcase.name
        }, room=room)

        try:
            if testcase.test_script:
                # 写入临时文件
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(testcase.test_script)
                    temp_file = f.name

                # 运行 pytest
                result = subprocess.run(
                    ['pytest', temp_file, '-v', '--json-report', '--json-report-file=report.json'],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    status = 'passed'
                    result_text = '测试通过'
                else:
                    status = 'failed'
                    result_text = result.stderr if result.stderr else result.stdout
                log = result.stdout + result.stderr

                # 可选：解析 json 报告
                if os.path.exists('report.json'):
                    with open('report.json') as rf:
                        report_data = json.load(rf)
                    # 可提取更详细的信息
                    os.remove('report.json')
                os.unlink(temp_file)
            else:
                status = 'failed'
                result_text = 'No test script provided'
                log = 'No test script available.'

            execution.status = status
            execution.result = result_text
            execution.log = log

        except Exception as e:
            execution.status = 'failed'
            execution.result = f'执行异常: {str(e)}'
            execution.log = str(e)

        execution.finished_at = datetime.utcnow()
        db.session.commit()

        testcase.latest_result_id = execution.id
        db.session.commit()

        # 生成报告（此处可调用 HTML 报告生成）
        from app.routes.report import generate_html_report
        html_content = generate_html_report(testcase, execution)

        report = Report(
            execution_id=execution.id,
            content=f"# 测试报告\n\n用例：{testcase.name}\n结果：{execution.status}\n日志：\n{execution.log}",
            html_content=html_content
        )
        db.session.add(report)
        db.session.commit()

        socketio.emit('execution_finished', {
            'execution_id': execution.id,
            'status': execution.status,
            'report_id': report.id
        }, room=room)