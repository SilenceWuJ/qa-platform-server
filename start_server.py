#!/usr/bin/env python3
"""
启动QA平台后端服务（兼容版本）
"""
import os
import sys

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 临时修复SQLAlchemy兼容性问题
try:
    import sqlalchemy as sa
    import sqlalchemy.orm as orm
    
    # 检查DeclarativeBase是否存在
    if not hasattr(orm, 'DeclarativeBase'):
        # 为旧版本SQLAlchemy添加兼容性
        class DeclarativeBase:
            pass
        
        orm.DeclarativeBase = DeclarativeBase
        
except ImportError:
    pass

from app import create_app
from app import socketio

if __name__ == '__main__':
    app = create_app()
    
    print("=" * 60)
    print("QA平台后端服务启动")
    print("=" * 60)
    print(f"访问地址: http://localhost:5002")
    print(f"API文档: http://localhost:5002/api/dashboard/health")
    print("=" * 60)
    
    # 打印注册的路由
    print("\n已注册的路由:")
    for rule in app.url_map.iter_rules():
        if rule.rule.startswith('/api/'):
            methods = ','.join(rule.methods)
            print(f"  {rule.rule:40} [{methods}]")
    
    print("\n" + "=" * 60)
    
    # 启动服务
    socketio.run(app, debug=True, host='0.0.0.0', port=5002, allow_unsafe_werkzeug=True)