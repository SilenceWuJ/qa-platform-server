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
import json
from flask import Blueprint, request, jsonify
from .. import db
from ..models import TestCase, Project, Requirement, TestPhase, TestType, Mark

testcase_bp = Blueprint('testcase', __name__)

@testcase_bp.route('/', methods=['GET'],strict_slashes=False)
def list_testcases():
    try:
        project_id = request.args.get('project_id')
        requirement_id = request.args.get('requirement_id')
        from sqlalchemy import or_
        query = TestCase.query.filter(or_(TestCase.is_deleted == False, TestCase.is_deleted == None))
        if project_id:
            query = query.filter_by(project_id=project_id)
        if requirement_id:
            query = query.filter_by(requirement_id=requirement_id)
        testcases = query.all()
        
        result = []
        for tc in testcases:
            # 解析JSON格式的测试步骤
            steps_data = []
            try:
                if tc.steps:
                    steps_data = json.loads(tc.steps)
            except:
                # 如果解析失败，保持原始格式
                steps_data = tc.steps
            
            result.append({
                'id': tc.id,
                'name': tc.name,
                'description': tc.description,
                'steps': steps_data,  # 返回解析后的JSON数据
                'steps_raw': tc.steps,  # 保留原始JSON字符串
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
            })
        
        return jsonify(result)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"list_testcases 错误: {e}")
        print(f"错误详情: {error_details}")
        return jsonify({'error': str(e), 'details': error_details}), 500

@testcase_bp.route('/<int:tc_id>', methods=['GET'],strict_slashes=False)
def get_testcase(tc_id):
    try:
        tc = TestCase.query.get(tc_id)
        if not tc or tc.is_deleted:
            return jsonify({'error': 'Test case not found'}), 404
        
        # 解析JSON格式的测试步骤
        steps_data = []
        try:
            if tc.steps:
                steps_data = json.loads(tc.steps)
        except:
            # 如果解析失败，保持原始格式
            steps_data = tc.steps
        
        result = {
            'id': tc.id,
            'name': tc.name,
            'description': tc.description,
            'steps': steps_data,  # 返回解析后的JSON数据
            'steps_raw': tc.steps,  # 保留原始JSON字符串
            'expected_result': tc.expected_result,
            'project_id': tc.project_id,
            'requirement_id': tc.requirement_id,
            'test_phase_id': tc.test_phase_id,
            'test_type_id': tc.test_type_id,
            'mark_id': tc.mark_id,
            'test_script': tc.test_script,
            'latest_result_status': tc.latest_result.status if tc.latest_result else None,
            'created_at': tc.created_at.isoformat(),
            'updated_at': tc.updated_at.isoformat(),
            'files': [{'id': f.id, 'filename': f.filename, 'file_size': f.file_size} for f in tc.files]
        }
        
        return jsonify(result)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"get_testcase 错误: {e}")
        print(f"错误详情: {error_details}")
        return jsonify({'error': str(e), 'details': error_details}), 500

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
    steps = data.get('steps', [])
    expected_result = data.get('expected_result', '')
    requirement_id = data.get('requirement_id')
    test_phase_id = data.get('test_phase_id')
    test_type_id = data.get('test_type_id') or 1  # 默认 1 代表 UI
    mark_id = data.get('mark_id')
    file_ids = data.get('file_ids', [])

    # 处理测试步骤：如果是列表，转换为JSON字符串
    if isinstance(steps, list):
        # 验证步骤格式
        validated_steps = []
        for i, step in enumerate(steps):
            if isinstance(step, dict):
                # 确保每个步骤都有必要的字段
                validated_step = {
                    'step': step.get('step', i + 1),
                    'description': step.get('description', ''),
                    'expected': step.get('expected', ''),
                    'actual': step.get('actual', ''),
                    'status': step.get('status', 'pending'),
                    'data': step.get('data', {})
                }
                validated_steps.append(validated_step)
            else:
                # 如果是字符串，转换为简单步骤对象
                validated_steps.append({
                    'step': i + 1,
                    'description': str(step),
                    'expected': '',
                    'actual': '',
                    'status': 'pending',
                    'data': {}
                })
        steps_json = json.dumps(validated_steps, ensure_ascii=False)
    else:
        # 如果是字符串，尝试解析为JSON，否则作为普通文本处理
        try:
            if steps:
                steps_data = json.loads(steps)
                steps_json = json.dumps(steps_data, ensure_ascii=False)
            else:
                steps_json = '[]'
        except:
            # 如果是普通文本，转换为简单步骤
            steps_list = [{'step': 1, 'description': steps, 'expected': '', 'actual': '', 'status': 'pending', 'data': {}}]
            steps_json = json.dumps(steps_list, ensure_ascii=False)

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
        steps=steps_json,  # 使用JSON格式的步骤
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

    return jsonify({
        'id': tc.id,
        'message': '测试用例创建成功',
        'steps_format': 'json'
    }), 201

@testcase_bp.route('/<int:tc_id>', methods=['PUT'],strict_slashes=False)
def update_testcase(tc_id):
    tc = TestCase.query.get_or_404(tc_id)
    if tc.is_deleted:
        return jsonify({'error': 'Test case is deleted'}), 400
    
    data = request.json
    allowed = ['name', 'description', 'steps', 'expected_result', 'requirement_id', 'test_phase_id', 'test_type_id', 'mark_id']
    
    for field in allowed:
        if field in data:
            if field == 'steps':
                # 特殊处理steps字段：转换为JSON格式
                steps = data['steps']
                if isinstance(steps, list):
                    # 验证步骤格式
                    validated_steps = []
                    for i, step in enumerate(steps):
                        if isinstance(step, dict):
                            validated_step = {
                                'step': step.get('step', i + 1),
                                'description': step.get('description', ''),
                                'expected': step.get('expected', ''),
                                'actual': step.get('actual', ''),
                                'status': step.get('status', 'pending'),
                                'data': step.get('data', {})
                            }
                            validated_steps.append(validated_step)
                        else:
                            validated_steps.append({
                                'step': i + 1,
                                'description': str(step),
                                'expected': '',
                                'actual': '',
                                'status': 'pending',
                                'data': {}
                            })
                    setattr(tc, field, json.dumps(validated_steps, ensure_ascii=False))
                else:
                    # 如果是字符串，尝试解析为JSON
                    try:
                        if steps:
                            steps_data = json.loads(steps)
                            setattr(tc, field, json.dumps(steps_data, ensure_ascii=False))
                    except:
                        # 如果是普通文本，转换为简单步骤
                        steps_list = [{'step': 1, 'description': steps, 'expected': '', 'actual': '', 'status': 'pending', 'data': {}}]
                        setattr(tc, field, json.dumps(steps_list, ensure_ascii=False))
            else:
                setattr(tc, field, data[field])
    
    db.session.commit()
    
    # 返回更新后的数据
    return jsonify({
        'id': tc.id,
        'name': tc.name,
        'message': '测试用例更新成功',
        'steps_format': 'json'
    })

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