#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#-------------------------------------------------------------
Name    : requirement.py
Time    : 2026/3/20 
Author  : xixi
File    : app/models
#-------------------------------------------------------------
"""
from .. import db
from datetime import datetime

class Requirement(db.Model):
    __tablename__ = 'requirements'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    creator = db.Column(db.String(100), nullable=True)
    tester = db.Column(db.String(100), nullable=True)
    developer = db.Column(db.String(100), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)   # 废除标志
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    testcases = db.relationship('TestCase', backref='requirement', lazy=True)
    files = db.relationship('File', secondary='requirement_files', back_populates='requirements')