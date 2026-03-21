#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#-------------------------------------------------------------
Name    : test_type.py
Time    : 2026/3/20 
Author  : xixi
File    : app/models
#-------------------------------------------------------------
"""
from .. import db

class TestType(db.Model):
    __tablename__ = 'test_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)