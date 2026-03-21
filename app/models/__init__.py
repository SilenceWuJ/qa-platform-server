#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#-------------------------------------------------------------
Name    : __init__.py.py
Time    : 2026/3/20
Author  : xixi
File    : app/models
#-------------------------------------------------------------
"""
from .. import db
from .project import Project
from .requirement import Requirement
from .testcase import TestCase
from .test_phase import TestPhase
from .test_type import TestType
from .mark import Mark
from .execution_result import ExecutionResult
from .report import Report
from .file import File

# Association tables
testcase_files = db.Table('testcase_files',
    db.Column('testcase_id', db.Integer, db.ForeignKey('testcases.id'), primary_key=True),
    db.Column('file_id', db.Integer, db.ForeignKey('files.id'), primary_key=True)
)

requirement_files = db.Table('requirement_files',
    db.Column('requirement_id', db.Integer, db.ForeignKey('requirements.id'), primary_key=True),
    db.Column('file_id', db.Integer, db.ForeignKey('files.id'), primary_key=True)
)

__all__ = [
    'Project', 'Requirement', 'TestCase', 'TestPhase', 'TestType', 'Mark',
    'ExecutionResult', 'Report', 'File', 'testcase_files', 'requirement_files'
]
