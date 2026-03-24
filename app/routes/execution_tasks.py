#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#-------------------------------------------------------------
Name    : execution_tasks.py
Time    : 2026/3/24
Author  : xixi
File    : app/routes
Description: 执行任务模块 - 处理测试执行逻辑
#-------------------------------------------------------------
"""
import json
import time
import random
from datetime import datetime
from .. import db, socketio
from ..models import TestCase, ExecutionResult, Report
from ..websocket_handler import (
    send_execution_progress,
    send_test_case_result,
    send_execution_completed,
    broadcast_test_run_update
)

def start_test_execution(execution_id, testcase_id):
    """启动单个测试执行任务"""
    with socketio.app.app_context():
        try:
            execution = ExecutionResult.query.get(execution_id)
            testcase = TestCase.query.get(testcase_id)
            
            if not execution or not testcase:
                return
            
            # 更新状态为运行中
            execution.status = 'running'
            execution.started_at = datetime.now()
            db.session.commit()
            
            # 发送开始通知
            send_execution_progress(execution_id, {
                'status': 'running',
                'progress': 0,
                'message': '测试执行开始',
                'timestamp': datetime.now().isoformat()
            })
            
            broadcast_test_run_update({
                'type': 'execution_started',
                'execution_id': execution_id,
                'testcase_id': testcase_id,
                'testcase_name': testcase.name,
                'status': 'running',
                'started_at': execution.started_at.isoformat(),
                'timestamp': datetime.now().isoformat()
            })
            
            # 解析测试步骤
            test_steps = []
            if testcase.steps:
                try:
                    test_steps = json.loads(testcase.steps)
                except:
                    test_steps = []
            
            # 模拟测试执行过程
            total_steps = len(test_steps) if test_steps else random.randint(3, 8)
            execution.total_tests = total_steps
            db.session.commit()
            
            passed_count = 0
            failed_count = 0
            skipped_count = 0
            
            for step_num in range(1, total_steps + 1):
                # 模拟执行延迟
                time.sleep(random.uniform(0.5, 2.0))
                
                # 更新进度
                progress = int((step_num / total_steps) * 100)
                execution.progress = progress
                db.session.commit()
                
                # 模拟测试结果
                if random.random() < 0.8:  # 80%通过率
                    result_status = 'passed'
                    passed_count += 1
                    result_message = f'步骤 {step_num} 执行通过'
                elif random.random() < 0.9:  # 10%失败率
                    result_status = 'failed'
                    failed_count += 1
                    result_message = f'步骤 {step_num} 执行失败: 预期结果不匹配'
                else:  # 10%跳过率
                    result_status = 'skipped'
                    skipped_count += 1
                    result_message = f'步骤 {step_num} 被跳过: 前置条件不满足'
                
                # 更新执行统计
                execution.passed = passed_count
                execution.failed = failed_count
                execution.skipped = skipped_count
                db.session.commit()
                
                # 发送步骤结果
                if test_steps and step_num <= len(test_steps):
                    step_info = test_steps[step_num - 1]
                    step_description = step_info.get('description', f'步骤 {step_num}')
                else:
                    step_description = f'测试步骤 {step_num}'
                
                send_test_case_result(execution_id, {
                    'step': step_num,
                    'description': step_description,
                    'status': result_status,
                    'message': result_message,
                    'timestamp': datetime.now().isoformat()
                })
                
                send_execution_progress(execution_id, {
                    'status': 'running',
                    'progress': progress,
                    'current_step': step_num,
                    'total_steps': total_steps,
                    'passed': passed_count,
                    'failed': failed_count,
                    'skipped': skipped_count,
                    'message': f'正在执行步骤 {step_num}/{total_steps}',
                    'timestamp': datetime.now().isoformat()
                })
            
            # 执行完成
            execution.status = 'passed' if failed_count == 0 else 'failed'
            execution.result = f'执行完成: 通过{passed_count}个，失败{failed_count}个，跳过{skipped_count}个'
            execution.finished_at = datetime.now()
            db.session.commit()
            
            # 生成报告
            generate_execution_report(execution, testcase, test_steps)
            
            # 发送完成通知
            send_execution_completed(execution_id, {
                'status': execution.status,
                'result': execution.result,
                'total_steps': total_steps,
                'passed': passed_count,
                'failed': failed_count,
                'skipped': skipped_count,
                'success_rate': (passed_count / total_steps * 100) if total_steps > 0 else 0,
                'started_at': execution.started_at.isoformat(),
                'finished_at': execution.finished_at.isoformat(),
                'duration': (execution.finished_at - execution.started_at).total_seconds(),
                'timestamp': datetime.now().isoformat()
            })
            
            broadcast_test_run_update({
                'type': 'execution_completed',
                'execution_id': execution_id,
                'testcase_id': testcase_id,
                'testcase_name': testcase.name,
                'status': execution.status,
                'result': execution.result,
                'passed': passed_count,
                'failed': failed_count,
                'total_steps': total_steps,
                'started_at': execution.started_at.isoformat(),
                'finished_at': execution.finished_at.isoformat(),
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            # 处理执行错误
            execution = ExecutionResult.query.get(execution_id)
            if execution:
                execution.status = 'failed'
                execution.result = f'执行异常: {str(e)}'
                execution.finished_at = datetime.now()
                db.session.commit()
                
                send_execution_completed(execution_id, {
                    'status': 'failed',
                    'result': f'执行异常: {str(e)}',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })

def start_batch_execution(batch_id, testcase_ids):
    """启动批量测试执行任务"""
    with socketio.app.app_context():
        try:
            total_cases = len(testcase_ids)
            completed_cases = 0
            passed_cases = 0
            failed_cases = 0
            
            # 发送批量开始通知
            socketio.emit('batch_started', {
                'batch_id': batch_id,
                'total_cases': total_cases,
                'message': f'批量执行开始，共{total_cases}个测试用例',
                'timestamp': datetime.now().isoformat()
            }, room=f'batch_{batch_id}')
            
            for i, testcase_id in enumerate(testcase_ids, 1):
                testcase = TestCase.query.get(testcase_id)
                if not testcase:
                    continue
                
                # 创建执行记录
                execution = ExecutionResult(
                    testcase_id=testcase_id,
                    status='running',
                    progress=0,
                    total_tests=0,
                    passed=0,
                    failed=0,
                    skipped=0,
                    batch_id=batch_id,
                    started_at=datetime.now()
                )
                db.session.add(execution)
                db.session.commit()
                
                # 发送单个用例开始通知
                socketio.emit('batch_case_started', {
                    'batch_id': batch_id,
                    'execution_id': execution.id,
                    'testcase_id': testcase_id,
                    'testcase_name': testcase.name,
                    'case_number': i,
                    'total_cases': total_cases,
                    'timestamp': datetime.now().isoformat()
                }, room=f'batch_{batch_id}')
                
                # 执行单个测试用例
                start_test_execution(execution.id, testcase_id)
                
                # 等待执行完成（在实际应用中应该使用更复杂的同步机制）
                time.sleep(1)
                
                # 获取执行结果
                execution = ExecutionResult.query.get(execution.id)
                if execution:
                    if execution.status == 'passed':
                        passed_cases += 1
                    else:
                        failed_cases += 1
                
                completed_cases += 1
                
                # 发送进度更新
                socketio.emit('batch_progress', {
                    'batch_id': batch_id,
                    'completed_cases': completed_cases,
                    'total_cases': total_cases,
                    'passed_cases': passed_cases,
                    'failed_cases': failed_cases,
                    'progress': int((completed_cases / total_cases) * 100),
                    'current_case': testcase.name,
                    'timestamp': datetime.now().isoformat()
                }, room=f'batch_{batch_id}')
            
            # 批量执行完成
            socketio.emit('batch_completed', {
                'batch_id': batch_id,
                'total_cases': total_cases,
                'completed_cases': completed_cases,
                'passed_cases': passed_cases,
                'failed_cases': failed_cases,
                'success_rate': (passed_cases / total_cases * 100) if total_cases > 0 else 0,
                'message': f'批量执行完成，通过{passed_cases}个，失败{failed_cases}个',
                'timestamp': datetime.now().isoformat()
            }, room=f'batch_{batch_id}')
            
        except Exception as e:
            socketio.emit('batch_error', {
                'batch_id': batch_id,
                'error': str(e),
                'message': '批量执行发生错误',
                'timestamp': datetime.now().isoformat()
            }, room=f'batch_{batch_id}')

def generate_execution_report(execution, testcase, test_steps):
    """生成执行报告"""
    try:
        # 解析测试步骤结果
        steps_html = ""
        if test_steps:
            for i, step in enumerate(test_steps):
                step_num = step.get('step', i + 1)
                description = step.get('description', '')
                expected = step.get('expected', '')
                
                # 模拟实际结果（在实际应用中应该从执行日志中提取）
                actual = f"步骤 {step_num} 执行完成"
                status = 'passed' if random.random() < 0.8 else 'failed'
                
                status_class = 'success' if status == 'passed' else 'danger'
                
                steps_html += f"""
                <div class="test-step {status_class}">
                    <div class="step-header">
                        <span class="step-number">步骤 {step_num}</span>
                        <span class="step-status badge bg-{status_class}">{status}</span>
                    </div>
                    <div class="step-description">{description}</div>
                    <div class="step-details">
                        <div class="step-expected">
                            <strong>预期结果:</strong> {expected}
                        </div>
                        <div class="step-actual">
                            <strong>实际结果:</strong> {actual}
                        </div>
                    </div>
                </div>
                """
        
        # 生成HTML报告
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>测试执行报告 - {testcase.name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .report-container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ border-bottom: 2px solid #4CAF50; padding-bottom: 20px; margin-bottom: 30px; }}
                .header h1 {{ color: #333; margin: 0; }}
                .summary {{ background: #f9f9f9; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
                .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }}
                .summary-item {{ text-align: center; padding: 15px; background: white; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
                .summary-value {{ font-size: 24px; font-weight: bold; color: #333; }}
                .summary-label {{ color: #666; margin-top: 5px; }}
                .test-step {{ border: 1px solid #ddd; border-radius: 6px; padding: 15px; margin-bottom: 15px; }}
                .test-step.success {{ border-left: 4px solid #4CAF50; }}
                .test-step.danger {{ border-left: 4px solid #f44336; }}
                .step-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
                .step-number {{ font-weight: bold; color: #333; }}
                .step-status {{ padding: 3px 8px; border-radius: 4px; font-size: 12px; }}
                .step-description {{ color: #555; margin-bottom: 10px; }}
                .step-details {{ background: #f9f9f9; padding: 10px; border-radius: 4px; }}
                .step-expected, .step-actual {{ margin-bottom: 5px; }}
                .execution-log {{ background: #f5f5f5; padding: 15px; border-radius: 6px; margin-top: 30px; }}
                .log-content {{ font-family: monospace; white-space: pre-wrap; font-size: 12px; }}
                .timestamp {{ color: #999; font-size: 12px; text-align: right; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="report-container">
                <div class="header">
                    <h1>📋 测试执行报告</h1>
                    <p><strong>测试用例:</strong> {testcase.name}</p>
                    <p><strong>执行ID:</strong> {execution.id}</p>
                </div>
                
                <div class="summary">
                    <h2>📊 执行摘要</h2>
                    <div class="summary-grid">
                        <div class="summary-item">
                            <div class="summary-value" style="color: {'#4CAF50' if execution.status == 'passed' else '#f44336'}">
                                {execution.status.upper()}
                            </div>
                            <div class="summary-label">执行状态</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-value">{execution.total_tests or 0}</div>
                            <div class="summary-label">总步骤数</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-value" style="color: #4CAF50">{execution.passed or 0}</div>
                            <div class="summary-label">通过</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-value" style="color: #f44336">{execution.failed or 0}</div>
                            <div class="summary-label">失败</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-value" style="color: #FF9800">{execution.skipped or 0}</div>
                            <div class="summary-label">跳过</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-value">
                                {(execution.passed / execution.total_tests * 100) if execution.total_tests and execution.total_tests > 0 else 0:.1f}%
                            </div>
                            <div class="summary-label">成功率</div>
                        </div>
                    </div>
                </div>
                
                <h2>🧪 测试步骤详情</h2>
                {steps_html if steps_html else '<p>暂无测试步骤详情</p>'}
                
                <div class="execution-log">
                    <h3>📝 执行日志</h3>
                    <div class="log-content">{execution.log or '暂无详细日志'}</div>
                </div>
                
                <div class="timestamp">
                    报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </div>
            </div>
        </body>
        </html>
        """
        
        # 保存报告
        report = Report(
            execution_id=execution.id,
            content=execution.result or '执行报告',
            html_content=html_content
        )
        db.session.add(report)
        db.session.commit()
        
    except Exception as e:
        print(f"生成报告失败: {e}")
        # 创建简单报告
        report = Report(
            execution_id=execution.id,
            content=execution.result or '执行报告',
            html_content=f"<h1>测试执行报告</h1><p>{execution.result}</p>"
        )
        db.session.add(report)
        db.session.commit()