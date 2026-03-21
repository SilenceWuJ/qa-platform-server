#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#-------------------------------------------------------------
Name    : project.py
Time    : 2026/3/20
Author  : xixi
File    : app/routes
#-------------------------------------------------------------
"""
from flask import Blueprint, request, jsonify
from .. import db
from ..models import Project

project_bp = Blueprint('project', __name__)

@project_bp.route('/', methods=['GET'],strict_slashes=False)
def list_projects():
    projects = Project.query.all()

    return jsonify([{
        'id': p.id,
        'name': p.name,
        'start_date': p.start_date.isoformat() if p.start_date else None,
        'end_date': p.end_date.isoformat() if p.end_date else None,
        'progress': p.progress,
        'created_at': p.created_at.isoformat()
    } for p in projects])

@project_bp.route('/', methods=['POST'],strict_slashes=False)
def create_project():
    data = request.json
    if not data or 'name' not in data:
        return jsonify({'error': 'Missing name'}), 400
    if Project.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'Project name already exists'}), 409

    from datetime import datetime
    start_date = None
    end_date = None
    if data.get('start_date'):
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
    if data.get('end_date'):
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()

    project = Project(
        name=data['name'],
        start_date=start_date,
        end_date=end_date,
        progress=data.get('progress', 0)
    )
    db.session.add(project)
    db.session.commit()
    return jsonify({
        'id': project.id,
        'name': project.name,
        'start_date': project.start_date.isoformat() if project.start_date else None,
        'end_date': project.end_date.isoformat() if project.end_date else None,
        'progress': project.progress
    }), 201

@project_bp.route('/<int:project_id>', methods=['PUT'],strict_slashes=False)
def update_project(project_id):
    project = Project.query.get_or_404(project_id)
    data = request.json

    from datetime import datetime
    if 'name' in data:
        # 检查重名
        if Project.query.filter(Project.name == data['name'], Project.id != project_id).first():
            return jsonify({'error': 'Project name already exists'}), 409
        project.name = data['name']

    if 'start_date' in data:
        if data['start_date']:
            project.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        else:
            project.start_date = None

    if 'end_date' in data:
        if data['end_date']:
            project.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        else:
            project.end_date = None

    if 'progress' in data:
        progress = int(data['progress'])
        if progress < 0:
            progress = 0
        elif progress > 100:
            progress = 100
        project.progress = progress

    db.session.commit()
    return jsonify({
        'id': project.id,
        'name': project.name,
        'start_date': project.start_date.isoformat() if project.start_date else None,
        'end_date': project.end_date.isoformat() if project.end_date else None,
        'progress': project.progress
    })