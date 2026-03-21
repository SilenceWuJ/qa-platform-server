#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#-------------------------------------------------------------
Name    : mark.py
Time    : 2026/3/20 
Author  : xixi
File    : app/routes
#-------------------------------------------------------------
"""
from flask import Blueprint, request, jsonify
from .. import db
from ..models import Mark

mark_bp = Blueprint('mark', __name__)

@mark_bp.route('/', methods=['GET'],strict_slashes=False)
def list_marks():
    marks = Mark.query.all()
    return jsonify([{'id': m.id, 'name': m.name} for m in marks])

@mark_bp.route('/', methods=['POST'],strict_slashes=False)
def create_mark():
    data = request.json
    if not data or 'name' not in data:
        return jsonify({'error': 'Missing name'}), 400
    if Mark.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'Mark already exists'}), 409
    mark = Mark(name=data['name'])
    db.session.add(mark)
    db.session.commit()
    return jsonify({'id': mark.id}), 201

@mark_bp.route('/<int:mark_id>', methods=['PUT'],strict_slashes=False)
def update_mark(mark_id):
    mark = Mark.query.get_or_404(mark_id)
    data = request.json
    if 'name' in data:
        if Mark.query.filter(Mark.name == data['name'], Mark.id != mark_id).first():
            return jsonify({'error': 'Mark name already exists'}), 409
        mark.name = data['name']
    db.session.commit()
    return jsonify({'id': mark.id})