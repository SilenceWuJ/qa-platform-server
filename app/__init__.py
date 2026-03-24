#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
#-------------------------------------------------------------
Name    : __init__.py.py
Time    : 2026/3/20 
Author  : xixi
File    : app
#-------------------------------------------------------------
"""
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_cors import CORS
from .conf.config import Config

db = SQLAlchemy()
socketio = SocketIO(async_mode='threading', cors_allowed_origins="*")

def create_app(config_class=Config):
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    app.config.from_object(config_class)

    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')

    # 注册蓝图
    from .routes import project_bp, requirement_bp, testcase_bp, execution_bp, report_bp, mark_bp, file_bp, dashboard_bp, execution_enhanced_bp
    app.register_blueprint(project_bp, url_prefix='/api/projects')
    app.register_blueprint(requirement_bp, url_prefix='/api/requirements')
    app.register_blueprint(testcase_bp, url_prefix='/api/testcases')
    app.register_blueprint(execution_bp, url_prefix='/api/executions')
    app.register_blueprint(execution_enhanced_bp, url_prefix='/api/executions-enhanced')
    app.register_blueprint(report_bp, url_prefix='/api/reports')
    app.register_blueprint(mark_bp, url_prefix='/api/marks')
    app.register_blueprint(file_bp, url_prefix='/api/files')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')

    # 创建表（生产环境应使用迁移工具）
    with app.app_context():
        db.create_all()
        # 预置测试阶段和测试类型数据
        init_predefined_data()

    # 导入并初始化WebSocket处理器
    from .websocket_handler import init_websocket_events
    init_websocket_events()

    return app

def init_predefined_data():
    """初始化固定数据：测试阶段、测试类型"""
    from .models.test_phase import TestPhase
    from .models.test_type import TestType
    phases = ['冒烟测试', '回归测试', '集成测试']
    for name in phases:
        if not TestPhase.query.filter_by(name=name).first():
            db.session.add(TestPhase(name=name))
    types = ['UI', '接口', '场景']
    for name in types:
        if not TestType.query.filter_by(name=name).first():
            db.session.add(TestType(name=name))
    db.session.commit()