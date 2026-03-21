#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#-------------------------------------------------------------
Name    : testcase.py
Time    : 2026/3/20 
Author  : xixi
File    : app/routes
#-------------------------------------------------------------
"""
from flask import Blueprint, request, jsonify
from .. import db
from ..models import TestCase, Project, Requirement, TestPhase, TestType, Mark

testcase_bp = Blueprint('testcase', __name__)

@testcase_bp.route('/', methods=['GET'],strict_slashes=False)
def list_testcases():
    project_id = request.args.get('project_id')
    requirement_id = request.args.get('requirement_id')
    query = TestCase.query.filter_by(is_deleted=False)
    if project_id:
        query = query.filter_by(project_id=project_id)
    if requirement_id:
        query = query.filter_by(requirement_id=requirement_id)
    testcases = query.all()
    return jsonify([{
        'id': tc.id,
        'name': tc.name,
        'description': tc.description,
        'steps': tc.steps,
        'expected_result': tc.expected_result,
        'project_id': tc.project_id,
        'requirement_id': tc.requirement_id,
        'test_phase_id': tc.test_phase_id,
        'test_type_id': tc.test_type_id,
        'mark_id': tc.mark_id,
        'latest_result_status': tc.latest_result.status if tc.latest_result else None,
        'created_at': tc.created_at.isoformat(),
        'updated_at': tc.updated_at.isoformat(),
        'files': [{'id': f.id, 'filename': f.filename, 'file_size': f.file_size} for f in tc.files]
    } for tc in testcases])

@testcase_bp.route('/', methods=['POST'],strict_slashes=False)
def create_testcase():
    data = request.json
    project_id = data.get('project_id')
    if not project_id:
        return jsonify({'error': 'project_id is required'}), 400
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    # 处理可选字段，提供默认值
    name = data.get('name') or '未命名用例'
    description = data.get('description', '')
    steps = data.get('steps', '')
    expected_result = data.get('expected_result', '')
    requirement_id = data.get('requirement_id')
    test_phase_id = data.get('test_phase_id')
    test_type_id = data.get('test_type_id') or 1  # 默认 1 代表 UI
    mark_id = data.get('mark_id')
    file_ids = data.get('file_ids', [])

    # 验证外键存在
    if requirement_id and not Requirement.query.get(requirement_id):
        return jsonify({'error': 'Requirement not found'}), 404
    if test_phase_id and not TestPhase.query.get(test_phase_id):
        return jsonify({'error': 'Test phase not found'}), 404
    if test_type_id and not TestType.query.get(test_type_id):
        return jsonify({'error': 'Test type not found'}), 404
    if mark_id and not Mark.query.get(mark_id):
        return jsonify({'error': 'Mark not found'}), 404

    tc = TestCase(
        name=name,
        description=description,
        steps=steps,
        expected_result=expected_result,
        project_id=project_id,
        requirement_id=requirement_id,
        test_phase_id=test_phase_id,
        test_type_id=test_type_id,
        mark_id=mark_id
    )
    db.session.add(tc)
    db.session.commit()

    # 关联文件
    from ..models import File
    for file_id in file_ids:
        file_obj = File.query.get(file_id)
        if file_obj:
            tc.files.append(file_obj)
    db.session.commit()

    return jsonify({'id': tc.id}), 201

@testcase_bp.route('/<int:tc_id>', methods=['PUT'],strict_slashes=False)
def update_testcase(tc_id):
    tc = TestCase.query.get_or_404(tc_id)
    if tc.is_deleted:
        return jsonify({'error': 'Test case is deleted'}), 400
    data = request.json
    allowed = ['name', 'description', 'steps', 'expected_result', 'requirement_id', 'test_phase_id', 'test_type_id', 'mark_id']
    for field in allowed:
        if field in data:
            setattr(tc, field, data[field])
    db.session.commit()
    return jsonify({'id': tc.id})

@testcase_bp.route('/<int:tc_id>', methods=['DELETE'],strict_slashes=False)
def delete_testcase(tc_id):
    tc = TestCase.query.get_or_404(tc_id)
    tc.is_deleted = True
    db.session.commit()
    return '', 204

@testcase_bp.route('/test-phases', methods=['GET'],strict_slashes=False)
def get_test_phases():
    from ..models import TestPhase
    phases = TestPhase.query.all()
    return jsonify([{'id': p.id, 'name': p.name} for p in phases])

@testcase_bp.route('/test-types', methods=['GET'],strict_slashes=False)
def get_test_types():
    from ..models import TestType
    types = TestType.query.all()
    return jsonify([{'id': t.id, 'name': t.name} for t in types])