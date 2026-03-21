#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#-------------------------------------------------------------
Name    : file.py
Time    : 2026/3/21
Author  : xixi
File    : app/routes
#-------------------------------------------------------------
"""
import os
import uuid
from flask import Blueprint, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
from .. import db
from ..models import File, TestCase, Requirement

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt', 'xls', 'xlsx'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

file_bp = Blueprint('file', __name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@file_bp.route('/upload/temp', methods=['POST'])
def upload_temp_file():
    """Upload a temporary file (not yet associated with any entity)"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > MAX_FILE_SIZE:
        return jsonify({'error': 'File too large. Maximum size is 10MB'}), 400

    # Generate unique filename
    original_filename = secure_filename(file.filename)
    filename = f"{uuid.uuid4().hex}_{original_filename}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    # Save file
    file.save(file_path)

    # Create file record (not associated with any entity yet)
    new_file = File(
        filename=filename,
        original_filename=original_filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type
    )
    db.session.add(new_file)
    db.session.commit()

    return jsonify({
        'id': new_file.id,
        'filename': filename,
        'original_filename': original_filename,
        'file_size': file_size,
        'file_size_formatted': get_file_size(file_size),
        'mime_type': file.content_type,
        'uploaded_at': new_file.uploaded_at.isoformat()
    }), 201

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size(size_bytes):
    """Convert bytes to human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes} {unit}"
        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} {unit}"
        if size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} {unit}"
        size_bytes /= 1024 * 1024 * 1024

@file_bp.route('/upload/testcase/<int:testcase_id>', methods=['POST'])
def upload_testcase_file(testcase_id):
    """Upload a file for a test case"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > MAX_FILE_SIZE:
        return jsonify({'error': 'File too large. Maximum size is 10MB'}), 400

    testcase = TestCase.query.get_or_404(testcase_id)
    if testcase.is_deleted:
        return jsonify({'error': 'Test case is deleted'}), 400

    # Generate unique filename
    original_filename = secure_filename(file.filename)
    filename = f"{uuid.uuid4().hex}_{original_filename}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    # Save file
    file.save(file_path)

    # Create file record
    new_file = File(
        filename=filename,
        original_filename=original_filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type
    )
    db.session.add(new_file)
    testcase.files.append(new_file)
    db.session.commit()

    return jsonify({
        'id': new_file.id,
        'filename': filename,
        'original_filename': original_filename,
        'file_size': file_size,
        'file_size_formatted': get_file_size(file_size),
        'mime_type': file.content_type
    }), 201

@file_bp.route('/upload/requirement/<int:requirement_id>', methods=['POST'])
def upload_requirement_file(requirement_id):
    """Upload a file for a requirement"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > MAX_FILE_SIZE:
        return jsonify({'error': 'File too large. Maximum size is 10MB'}), 400

    requirement = Requirement.query.get_or_404(requirement_id)
    if requirement.is_deleted:
        return jsonify({'error': 'Requirement is deleted'}), 400

    # Generate unique filename
    original_filename = secure_filename(file.filename)
    filename = f"{uuid.uuid4().hex}_{original_filename}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    # Save file
    file.save(file_path)

    # Create file record
    new_file = File(
        filename=filename,
        original_filename=original_filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type
    )
    db.session.add(new_file)
    requirement.files.append(new_file)
    db.session.commit()

    return jsonify({
        'id': new_file.id,
        'filename': filename,
        'original_filename': original_filename,
        'file_size': file_size,
        'file_size_formatted': get_file_size(file_size),
        'mime_type': file.content_type
    }), 201

@file_bp.route('/<int:file_id>', methods=['GET'])
def get_file(file_id):
    """Get file information"""
    file_record = File.query.get_or_404(file_id)
    return jsonify(file_record.to_dict())

@file_bp.route('/download/<int:file_id>', methods=['GET'])
def download_file(file_id):
    """Download a file"""
    file_record = File.query.get_or_404(file_id)

    if not os.path.exists(file_record.file_path):
        return jsonify({'error': 'File not found'}), 404

    return send_file(file_record.file_path, as_attachment=True, download_name=file_record.original_filename)

@file_bp.route('/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    """Delete a file"""
    file_record = File.query.get_or_404(file_id)

    # Remove associations
    testcase = TestCase.query.filter(TestCase.files.any(id=file_record.id)).first()
    if testcase:
        testcase.files = [f for f in testcase.files if f.id != file_record.id]

    requirement = Requirement.query.filter(Requirement.files.any(id=file_record.id)).first()
    if requirement:
        requirement.files = [f for f in requirement.files if f.id != file_record.id]

    # Delete file
    db.session.delete(file_record)

    # Delete physical file
    if os.path.exists(file_record.file_path):
        os.remove(file_record.file_path)

    db.session.commit()
    return '', 204

@file_bp.route('/testcase/<int:testcase_id>', methods=['GET'])
def get_testcase_files(testcase_id):
    """Get all files for a test case"""
    testcase = TestCase.query.get_or_404(testcase_id)
    if testcase.is_deleted:
        return jsonify({'error': 'Test case is deleted'}), 400

    files = [f.to_dict() for f in testcase.files]
    return jsonify(files)

@file_bp.route('/requirement/<int:requirement_id>', methods=['GET'])
def get_requirement_files(requirement_id):
    """Get all files for a requirement"""
    requirement = Requirement.query.get_or_404(requirement_id)
    if requirement.is_deleted:
        return jsonify({'error': 'Requirement is deleted'}), 400

    files = [f.to_dict() for f in requirement.files]
    return jsonify(files)

@file_bp.route('/preview/<int:file_id>', methods=['GET'])
def preview_file(file_id):
    """Preview a file (image/pdf)"""
    file_record = File.query.get_or_404(file_id)

    if not os.path.exists(file_record.file_path):
        return jsonify({'error': 'File not found'}), 404

    # Determine if file is an image
    image_types = ['image/png', 'image/jpeg', 'image/gif', 'image/webp']

    if file_record.mime_type.startswith('image/'):
        return send_file(file_record.file_path)
    elif file_record.mime_type == 'application/pdf':
        # For PDF, we just return it as a file that the browser can preview
        return send_file(file_record.file_path)
    else:
        # For other file types, download instead of preview
        return send_file(file_record.file_path, as_attachment=True, download_name=file_record.original_filename)
