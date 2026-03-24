#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#-------------------------------------------------------------
Name    : testcase.py
Time    : 2026/3/20 
Author  : xixi
File    : app/models
#-------------------------------------------------------------
"""
from .. import db
from datetime import datetime

test_script = db.Column(db.Text, default='')  # pytest测试脚本内容

class TestCase(db.Model):
    __tablename__ = 'testcases'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    steps = db.Column(db.Text, default='')
    expected_result = db.Column(db.Text, default='')
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    requirement_id = db.Column(db.Integer, db.ForeignKey('requirements.id'), nullable=True)
    test_phase_id = db.Column(db.Integer, db.ForeignKey('test_phases.id'), nullable=True)
    test_type_id = db.Column(db.Integer, db.ForeignKey('test_types.id'), nullable=False)
    mark_id = db.Column(db.Integer, db.ForeignKey('marks.id'), nullable=True)
    latest_result_id = db.Column(db.Integer, db.ForeignKey('test_reports.id'), nullable=True)  # 最新执行结果（冗余）
    is_deleted = db.Column(db.Boolean, default=False)   # 废除标志
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    test_script = db.Column(db.Text, default='')  # pytest测试脚本内容

    # 关系
    latest_result = db.relationship('ExecutionResult', foreign_keys=[latest_result_id], backref='latest_testcase')
    executions = db.relationship('ExecutionResult', backref='testcase', lazy=True, foreign_keys='ExecutionResult.testcase_id')
    files = db.relationship('File', secondary='testcase_files', back_populates='testcases')