#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#-------------------------------------------------------------
Name    : project.py
Time    : 2026/3/20 
Author  : xixi
File    : app/models
#-------------------------------------------------------------
"""
from .. import db
from datetime import datetime

class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    progress = db.Column(db.Integer, default=0)  # Progress percentage (0-100)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    requirements = db.relationship('Requirement', backref='project', lazy=True)
    testcases = db.relationship('TestCase', backref='project', lazy=True)