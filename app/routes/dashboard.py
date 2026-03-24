#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#-------------------------------------------------------------
Name    : dashboard.py
Time    : 2026/3/24
Author  : xixi
File    : app/routes
Description: 看板API路由
#-------------------------------------------------------------
"""
from flask import Blueprint, jsonify, request
from app import db
from sqlalchemy import text, func
from datetime import datetime, timedelta
import json

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/stats', methods=['GET'])
def get_dashboard_stats():
    """获取看板统计信息"""
    try:
        # 1. 项目统计
        project_stats = db.session.execute(
            text("SELECT COUNT(*) as total, SUM(progress) as total_progress FROM projects")
        ).fetchone()
        
        # 2. 测试用例统计
        testcase_stats = db.session.execute(
            text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN is_deleted = 1 THEN 1 END) as deleted,
                COUNT(CASE WHEN is_deleted = 0 OR is_deleted IS NULL THEN 1 END) as active
            FROM testcases
            """)
        ).fetchone()
        
        # 3. 测试执行统计
        execution_stats = db.session.execute(
            text("""
            SELECT 
                COUNT(*) as total_runs,
                SUM(total_tests) as total_tests,
                SUM(passed) as total_passed,
                SUM(failed) as total_failed,
                SUM(skipped) as total_skipped,
                AVG(duration) as avg_duration
            FROM mcp_test_runs
            WHERE total_tests > 0
            """)
        ).fetchone()
        
        # 4. 测试报告统计
        report_stats = db.session.execute(
            text("SELECT status, COUNT(*) as count FROM test_reports GROUP BY status")
        ).fetchall()
        
        # 5. 最近活动
        recent_activities = db.session.execute(
            text("""
            SELECT 
                'test_run' COLLATE utf8mb4_unicode_ci as type,
                project_name COLLATE utf8mb4_unicode_ci,
                test_path COLLATE utf8mb4_unicode_ci,
                created_at,
                CONCAT(passed, '/', total_tests, ' 通过') COLLATE utf8mb4_unicode_ci as description
            FROM mcp_test_runs
            UNION ALL
            SELECT 
                'testcase' COLLATE utf8mb4_unicode_ci as type,
                p.name COLLATE utf8mb4_unicode_ci as project_name,
                tc.name COLLATE utf8mb4_unicode_ci as test_path,
                tc.created_at,
                '新测试用例' COLLATE utf8mb4_unicode_ci as description
            FROM testcases tc
            JOIN projects p ON tc.project_id = p.id
            ORDER BY created_at DESC
            LIMIT 10
            """)
        ).fetchall()
        
        # 6. 项目进度排名
        project_progress = db.session.execute(
            text("""
            SELECT name, progress, created_at
            FROM projects
            ORDER BY progress DESC
            LIMIT 5
            """)
        ).fetchall()
        
        # 7. 测试成功率趋势（最近7天）
        success_trend = db.session.execute(
            text("""
            SELECT 
                DATE(created_at) as date,
                AVG(passed * 100.0 / NULLIF(total_tests, 0)) as success_rate
            FROM mcp_test_runs
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY DATE(created_at)
            ORDER BY date
            """)
        ).fetchall()
        
        stats = {
            'projects': {
                'total': project_stats[0] or 0,
                'total_progress': project_stats[1] or 0,
                'avg_progress': round(float(project_stats[1] or 0) / float(project_stats[0] or 1), 2) if project_stats[0] and project_stats[0] > 0 else 0
            },
            'testcases': {
                'total': testcase_stats[0] or 0,
                'active': testcase_stats[2] or 0,
                'deleted': testcase_stats[1] or 0
            },
            'executions': {
                'total_runs': execution_stats[0] or 0,
                'total_tests': execution_stats[1] or 0,
                'total_passed': execution_stats[2] or 0,
                'total_failed': execution_stats[3] or 0,
                'total_skipped': execution_stats[4] or 0,
                'avg_duration': round(execution_stats[5] or 0, 2),
                'success_rate': round((float(execution_stats[2] or 0) * 100.0 / float(execution_stats[1] or 1)), 2) if execution_stats[1] and execution_stats[1] > 0 else 0
            },
            'reports': {
                item[0]: item[1] for item in report_stats
            },
            'recent_activities': [
                {
                    'type': item[0],
                    'project_name': item[1],
                    'test_path': item[2],
                    'created_at': item[3].isoformat() if item[3] else None,
                    'description': item[4]
                }
                for item in recent_activities
            ],
            'project_progress': [
                {
                    'name': item[0],
                    'progress': item[1],
                    'created_at': item[2].isoformat() if item[2] else None
                }
                for item in project_progress
            ],
            'success_trend': [
                {
                    'date': item[0].isoformat() if item[0] else None,
                    'success_rate': round(float(item[1] or 0), 2)
                }
                for item in success_trend
            ]
        }
        
        return jsonify({
            'code': 200,
            'message': '成功',
            'data': stats
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取统计信息失败: {str(e)}',
            'data': None
        }), 500

@dashboard_bp.route('/summary', methods=['GET'])
def get_dashboard_summary():
    """获取看板摘要信息"""
    try:
        # 获取各表数据量
        tables = ['projects', 'testcases', 'mcp_test_runs', 'test_reports', 'reports', 'files']
        table_stats = {}
        
        for table in tables:
            try:
                result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                table_stats[table] = result.scalar() or 0
            except:
                table_stats[table] = 0
        
        # 获取测试报告状态统计
        report_status = db.session.execute(
            text("SELECT status, COUNT(*) FROM test_reports GROUP BY status")
        ).fetchall()
        
        # 获取最近一次测试执行
        latest_run = db.session.execute(
            text("""
            SELECT project_name, test_path, passed, failed, total_tests, created_at 
            FROM mcp_test_runs 
            ORDER BY created_at DESC 
            LIMIT 1
            """)
        ).fetchone()
        
        summary = {
            'table_stats': table_stats,
            'report_status': {item[0]: item[1] for item in report_status},
            'latest_run': {
                'project_name': latest_run[0] if latest_run else None,
                'test_path': latest_run[1] if latest_run else None,
                'passed': latest_run[2] if latest_run else None,
                'failed': latest_run[3] if latest_run else None,
                'total_tests': latest_run[4] if latest_run else None,
                'created_at': latest_run[5].isoformat() if latest_run and latest_run[5] else None
            } if latest_run else None,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'code': 200,
            'message': '成功',
            'data': summary
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取摘要信息失败: {str(e)}',
            'data': None
        }), 500

@dashboard_bp.route('/test-runs', methods=['GET'])
def get_test_runs():
    """获取测试执行记录"""
    try:
        limit = request.args.get('limit', default=10, type=int)
        
        test_runs = db.session.execute(
            text("""
            SELECT 
                id, project_name, test_path, total_tests, passed, failed, 
                skipped, duration, status, created_at
            FROM mcp_test_runs 
            ORDER BY created_at DESC 
            LIMIT :limit
            """),
            {'limit': limit}
        ).fetchall()
        
        runs = []
        for row in test_runs:
            success_rate = (float(row[4]) / float(row[3]) * 100) if row[3] and row[3] > 0 else 0
            runs.append({
                'id': row[0],
                'project_name': row[1],
                'test_path': row[2],
                'total_tests': row[3],
                'passed': row[4],
                'failed': row[5],
                'skipped': row[6],
                'duration': row[7],
                'status': row[8],
                'success_rate': round(success_rate, 2),
                'created_at': row[9].isoformat() if row[9] else None
            })
        
        return jsonify({
            'code': 200,
            'message': '成功',
            'data': runs,
            'count': len(runs)
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取测试执行记录失败: {str(e)}',
            'data': None
        }), 500

@dashboard_bp.route('/test-reports', methods=['GET'])
def get_test_reports():
    """获取测试报告"""
    try:
        limit = request.args.get('limit', default=10, type=int)
        testcase_id = request.args.get('testcase_id', type=int)
        
        query = """
        SELECT 
            tr.id, tr.testcase_id, tc.name as testcase_name,
            tr.status, tr.result, tr.started_at, tr.finished_at,
            tr.log
        FROM test_reports tr
        LEFT JOIN testcases tc ON tr.testcase_id = tc.id
        """
        
        params = {'limit': limit}
        if testcase_id:
            query += " WHERE tr.testcase_id = :testcase_id"
            params['testcase_id'] = testcase_id
        
        query += " ORDER BY tr.started_at DESC LIMIT :limit"
        
        test_reports = db.session.execute(text(query), params).fetchall()
        
        reports = []
        for row in test_reports:
            duration = None
            if row[5] and row[6]:
                duration = (row[6] - row[5]).total_seconds()
            
            reports.append({
                'id': row[0],
                'testcase_id': row[1],
                'testcase_name': row[2],
                'status': row[3],
                'result': row[4],
                'started_at': row[5].isoformat() if row[5] else None,
                'finished_at': row[6].isoformat() if row[6] else None,
                'duration': round(duration, 2) if duration else None,
                'log': row[7]
            })
        
        return jsonify({
            'code': 200,
            'message': '成功',
            'data': reports,
            'count': len(reports)
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取测试报告失败: {str(e)}',
            'data': None
        }), 500

@dashboard_bp.route('/report-files', methods=['GET'])
def get_report_files():
    """获取报告文件"""
    try:
        limit = request.args.get('limit', default=10, type=int)
        
        files = db.session.execute(
            text("""
            SELECT 
                id, filename, original_filename, file_path, 
                file_size, mime_type, uploaded_at, uploader_id
            FROM files 
            ORDER BY uploaded_at DESC 
            LIMIT :limit
            """),
            {'limit': limit}
        ).fetchall()
        
        file_list = []
        for row in files:
            size_kb = float(row[4] or 0) / 1024
            file_list.append({
                'id': row[0],
                'filename': row[1],
                'original_filename': row[2],
                'file_path': row[3],
                'file_size': row[4],
                'file_size_kb': round(size_kb, 2),
                'mime_type': row[5],
                'uploaded_at': row[6].isoformat() if row[6] else None,
                'uploader_id': row[7]
            })
        
        return jsonify({
            'code': 200,
            'message': '成功',
            'data': file_list,
            'count': len(file_list)
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取报告文件失败: {str(e)}',
            'data': None
        }), 500

@dashboard_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        # 测试数据库连接
        db.session.execute(text("SELECT 1"))
        
        return jsonify({
            'code': 200,
            'message': '服务正常',
            'data': {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'service': 'QA测试平台看板API'
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'服务异常: {str(e)}',
            'data': {
                'status': 'unhealthy',
                'timestamp': datetime.now().isoformat()
            }
        }), 500