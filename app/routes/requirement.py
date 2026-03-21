#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#-------------------------------------------------------------
Name    : requirement.py
Time    : 2026/3/20 
Author  : xixi
File    : app/routes
#-------------------------------------------------------------
"""
import pandas as pd
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from flask import Blueprint, request, jsonify
from .. import db
from ..models import Requirement, Project
from datetime import datetime
import pandas as pd
from werkzeug.utils import secure_filename
import os
from datetime import datetime



requirement_bp = Blueprint('requirement', __name__)



@requirement_bp.route('/', methods=['GET'],strict_slashes=False)
def list_requirements():
    project_id = request.args.get('project_id')
    query = Requirement.query.filter_by(is_deleted=False)
    if project_id:
        query = query.filter_by(project_id=project_id)
    requirements = query.all()
    return jsonify([{
        'id': r.id,
        'name': r.name,
        'start_date': r.start_date.isoformat() if r.start_date else None,
        'end_date': r.end_date.isoformat() if r.end_date else None,
        'creator': r.creator,
        'tester': r.tester,
        'developer': r.developer,
        'project_id': r.project_id,
        'created_at': r.created_at.isoformat(),
        'updated_at': r.updated_at.isoformat(),
        'files': [{'id': f.id, 'filename': f.filename, 'file_size': f.file_size} for f in r.files]
    } for r in requirements])

@requirement_bp.route('/', methods=['POST'],strict_slashes=False)
def create_requirement():
    data = request.json
    required = ['name', 'project_id']
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields'}), 400
    project = Project.query.get(data['project_id'])
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    file_ids = data.get('file_ids', [])
    req = Requirement(
        name=data['name'],
        start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date() if data.get('start_date') else None,
        end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date() if data.get('end_date') else None,
        creator=data.get('creator'),
        tester=data.get('tester'),
        developer=data.get('developer'),
        project_id=data['project_id']
    )
    db.session.add(req)
    db.session.commit()

    # 关联文件
    from ..models import File
    for file_id in file_ids:
        file_obj = File.query.get(file_id)
        if file_obj:
            req.files.append(file_obj)
    db.session.commit()

    return jsonify({'id': req.id}), 201

@requirement_bp.route('/<int:req_id>', methods=['PUT'],strict_slashes=False)
def update_requirement(req_id):
    req = Requirement.query.get_or_404(req_id)
    if req.is_deleted:
        return jsonify({'error': 'Requirement is deleted'}), 400
    data = request.json
    for field in ['name', 'start_date', 'end_date', 'creator', 'tester', 'developer']:
        if field in data:
            if field == 'start_date' and data[field]:
                setattr(req, field, datetime.strptime(data[field], '%Y-%m-%d').date())
            elif field == 'end_date' and data[field]:
                setattr(req, field, datetime.strptime(data[field], '%Y-%m-%d').date())
            else:
                setattr(req, field, data[field])
    db.session.commit()
    return jsonify({'id': req.id})

@requirement_bp.route('/<int:req_id>', methods=['DELETE'],strict_slashes=False)
def delete_requirement(req_id):
    req = Requirement.query.get_or_404(req_id)
    req.is_deleted = True
    db.session.commit()
    return '', 204


ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@requirement_bp.route('/batch_upload', methods=['POST'],strict_slashes=False)
def batch_upload_requirements():
    project_id = request.args.get('project_id')
    if not project_id:
        return jsonify({'error': 'project_id is required'}), 400
    project = Project.query.get(project_id)
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
    except Exception as e:
        return jsonify({'error': f'Failed to parse file: {str(e)}'}), 400

    required_columns = {'name'}
    if not required_columns.issubset(df.columns):
        return jsonify({'error': f'Missing columns: {required_columns - set(df.columns)}'}), 400

    optional_columns = {'start_date', 'end_date', 'creator', 'tester', 'developer'}
    success_count = 0
    errors = []

    for idx, row in df.iterrows():
        try:
            name = row.get('name')
            if pd.isna(name):
                errors.append(f"Row {idx+2}: name is empty")
                continue

            start_date = row.get('start_date') if 'start_date' in row else None
            if start_date and not pd.isna(start_date):
                try:
                    start_date = datetime.strptime(str(start_date), '%Y-%m-%d').date()
                except:
                    start_date = None
            else:
                start_date = None

            end_date = row.get('end_date') if 'end_date' in row else None
            if end_date and not pd.isna(end_date):
                try:
                    end_date = datetime.strptime(str(end_date), '%Y-%m-%d').date()
                except:
                    end_date = None
            else:
                end_date = None

            creator = row.get('creator') if 'creator' in row and not pd.isna(row.get('creator')) else None
            tester = row.get('tester') if 'tester' in row and not pd.isna(row.get('tester')) else None
            developer = row.get('developer') if 'developer' in row and not pd.isna(row.get('developer')) else None

            req = Requirement(
                name=name,
                start_date=start_date,
                end_date=end_date,
                creator=creator,
                tester=tester,
                developer=developer,
                project_id=project_id
            )
            db.session.add(req)
            success_count += 1
        except Exception as e:
            errors.append(f"Row {idx+2}: {str(e)}")

    db.session.commit()
    return jsonify({
        'success': success_count,
        'errors': errors,
        'total': len(df)
    }), 200 if not errors else 207