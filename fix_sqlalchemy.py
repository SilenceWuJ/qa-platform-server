#!/usr/bin/env python3
"""
修复SQLAlchemy兼容性问题
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 临时修复SQLAlchemy兼容性问题
try:
    import sqlalchemy as sa
    import sqlalchemy.orm as orm
    
    # 检查DeclarativeBase是否存在
    if not hasattr(orm, 'DeclarativeBase'):
        print("检测到旧版本SQLAlchemy，添加DeclarativeBase兼容性...")
        
        # 为旧版本SQLAlchemy添加兼容性
        class DeclarativeBase:
            pass
        
        orm.DeclarativeBase = DeclarativeBase
        print("✅ DeclarativeBase兼容性修复完成")
        
except ImportError as e:
    print(f"导入SQLAlchemy失败: {e}")
    sys.exit(1)

# 现在导入Flask应用
try:
    from app import create_app
    from app import socketio
    
    print("✅ Flask应用导入成功")
    
    # 创建应用实例
    app = create_app()
    
    print("\n" + "=" * 60)
    print("QA平台后端服务")
    print("=" * 60)
    print(f"访问地址: http://localhost:5002")
    print(f"API基础路径: /api")
    print(f"看板API: http://localhost:5002/api/dashboard/stats")
    print("=" * 60)
    
    # 打印注册的路由
    print("\n已注册的API路由:")
    api_routes = []
    for rule in app.url_map.iter_rules():
        if rule.rule.startswith('/api/'):
            methods = ','.join(rule.methods)
            api_routes.append(f"  {rule.rule:40} [{methods}]")
    
    # 按路由排序
    api_routes.sort()
    for route in api_routes:
        print(route)
    
    print("\n" + "=" * 60)
    print("启动服务中...")
    print("按 Ctrl+C 停止服务")
    print("=" * 60)
    
    # 启动服务
    socketio.run(app, debug=True, host='0.0.0.0', port=5002, allow_unsafe_werkzeug=True)
    
except Exception as e:
    print(f"❌ 启动失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)