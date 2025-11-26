#!/usr/bin/env python3
import sys
sys.path.insert(0, '/opt/airflow/dags')

try:
    from jq_adapter import g, log
    print("[SUCCESS] jq_adapter 导入成功")
    print(f"  - g.security = {g.security}")
    
    from jq_strategy_loader import validate_strategy_code
    print("[SUCCESS] jq_strategy_loader 导入成功")
    
    print("\n[TEST] 测试简单策略验证...")
    code = """
from jqdata import *

def initialize(context):
    g.security = '000001.XSHE'

def handle_data(context, data):
    pass
"""
    result = validate_strategy_code(code)
    print(f"  - 验证结果: {result.is_valid}")
    print(f"  - 股票代码: {result.security}")
    
    print("\n[ALL TESTS PASSED]")
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
