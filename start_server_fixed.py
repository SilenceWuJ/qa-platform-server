#!/usr/bin/env python3
"""
启动QA平台后端服务（修复SQLAlchemy兼容性问题）
"""
import os
import sys

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 在导入任何其他模块之前修复SQLAlchemy兼容性问题
import sqlalchemy as sa
import sqlalchemy.orm as orm

# 修复DeclarativeBase
if not hasattr(orm, 'DeclarativeBase'):
    print("检测到旧版本SQLAlchemy，添加DeclarativeBase兼容性...")
    class DeclarativeBase:
        pass
    orm.DeclarativeBase = DeclarativeBase

# 修复DeclarativeBaseNoMeta  
if not hasattr(orm, 'DeclarativeBaseNoMeta'):
    print("检测到旧版本SQLAlchemy，添加DeclarativeBaseNoMeta兼容性...")
    class DeclarativeBaseNoMeta:
        pass
    orm.DeclarativeBaseNoMeta = DeclarativeBaseNoMeta

print("✅ SQLAlchemy兼容性修复完成")

# 现在导入Flask应用
try:
    from app import create_app
    from app import socketio
    
    print("✅ Flask应用导入成功")
    
    # 创建应用实例
    app = create_app()
    
    print("\n" + "=" * 60)
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
    print("启动WebSocket服务器在端口 5002...")
    socketio.run(app, debug=True, host='0.0.0.0', port=5002, allow_unsafe_werkzeug=True)
    
except Exception as e:
    print(f"❌ 启动失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)