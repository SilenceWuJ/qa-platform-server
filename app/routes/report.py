#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#-------------------------------------------------------------
Name    : report.py
Time    : 2026/3/20 
Author  : xixi
File    : app/routes
#-------------------------------------------------------------
"""
from flask import render_template
from .. import db
from flask import Blueprint, request, jsonify
from ..models import Report

report_bp = Blueprint('report', __name__)

@report_bp.route('/', methods=['GET'],strict_slashes=False)
def list_reports():
    execution_id = request.args.get('execution_id')
    query = Report.query
    if execution_id:
        query = query.filter_by(execution_id=execution_id)
    reports = query.order_by(Report.created_at.desc()).all()
    return jsonify([{
        'id': r.id,
        'execution_id': r.execution_id,
        'html_content': r.html_content if r.html_content else '',
        'content': r.content,
        'created_at': r.created_at.isoformat()
    } for r in reports])

@report_bp.route('/<int:report_id>', methods=['GET'],strict_slashes=False)
def get_report(report_id):
    report = Report.query.get_or_404(report_id)
    return jsonify({
        'id': report.id,
        'execution_id': report.execution_id,
        'html_content': report.html_content if report.html_content else '',
        'content': report.content,
        'created_at': report.created_at.isoformat()
    })

from flask import send_file, render_template_string
from io import BytesIO

def generate_html_report(testcase, execution):
    """生成HTML报告内容"""
    return render_template('report_template.html',
                           testcase=testcase,
                           execution=execution,
                           log=execution.log)

@report_bp.route('/<int:report_id>/export', methods=['GET'],strict_slashes=False)
def export_report_html(report_id):
    report = Report.query.get_or_404(report_id)
    if report.html_content:
        return report.html_content, 200, {
            'Content-Type': 'text/html',
            'Content-Disposition': f'attachment; filename=report_{report_id}.html'
        }
    else:
        # 降级方案：从 content 生成简单 HTML
        html = f"<html><body><h1>测试报告</h1><pre>{report.content}</pre></body></html>"
        return html, 200, {
            'Content-Type': 'text/html',
            'Content-Disposition': f'attachment; filename=report_{report_id}.html'
        }