#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#-------------------------------------------------------------
Name    : execution_result.py
Time    : 2026/3/20 
Author  : xixi
File    : app/models
#-------------------------------------------------------------
"""
from .. import db
from datetime import datetime

class ExecutionResult(db.Model):
    __tablename__ = 'execution_results'
    id = db.Column(db.Integer, primary_key=True)
    testcase_id = db.Column(db.Integer, db.ForeignKey('testcases.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')   # pending, running, passed, failed
    result = db.Column(db.Text, default='')                # 详细结果，可以是 JSON 字符串
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime, nullable=True)
    log = db.Column(db.Text, default='')

    # 关系
    report = db.relationship('Report', backref='execution', uselist=False)