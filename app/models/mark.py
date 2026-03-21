#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#-------------------------------------------------------------
Name    : mark.py
Time    : 2026/3/20 
Author  : xixi
File    : app/models
#-------------------------------------------------------------
"""
from .. import db

class Mark(db.Model):
    __tablename__ = 'marks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)