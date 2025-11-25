#!/usr/bin/env python3
"""创建 Airflow 管理员用户 - Airflow 3.x 兼容版本"""

import os
os.environ.setdefault('AIRFLOW__CORE__AUTH_MANAGER', 'airflow.providers.fab.auth_manager.fab_auth_manager.FabAuthManager')

try:
    from airflow.www.app import create_app
    
    app = create_app()
    
    with app.app_context():
        from flask_appbuilder.security.sqla.models import User
        
        sm = app.appbuilder.sm
        
        # 检查用户是否已存在
        existing_user = sm.find_user(username='airflow')
        
        if existing_user:
            print("ℹ️  用户 'airflow' 已存在")
        else:
            # 创建Admin角色用户
            role_admin = sm.find_role('Admin')
            
            if not role_admin:
                print("❌ Admin 角色不存在，正在创建...")
                role_admin = sm.add_role('Admin')
            
            user = sm.add_user(
                username='airflow',
                first_name='Air',
                last_name='Flow',
                email='airflow@example.com',
                role=role_admin,
                password='airflow'
            )
            
            if user:
                print("✅ 管理员用户 'airflow' 创建成功！")
                print("   用户名: airflow")
                print("   密码: airflow")
            else:
                print("❌ 用户创建失败")
                
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
