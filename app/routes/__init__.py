#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#-------------------------------------------------------------
Name    : __init__.py.py
Time    : 2026/3/20
Author  : xixi
File    : app/routes
#-------------------------------------------------------------
"""
from .project import project_bp
from .requirement import requirement_bp
from .testcase import testcase_bp
from .execution import execution_bp
from .report import report_bp
from .mark import mark_bp
from .file import file_bp

__all__ = [
    'project_bp',
    'requirement_bp',
    'testcase_bp',
    'execution_bp',
    'report_bp',
    'mark_bp',
    'file_bp'
]