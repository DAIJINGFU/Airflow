"""
JoinQuant 策略代码验证和加载器

提供策略代码的安全验证、解析和动态加载功能
"""

from __future__ import annotations

import ast
import re
from typing import Any, Dict, Optional, Tuple, Callable
from dataclasses import dataclass


# =============================================================================
# 1. 策略验证结果
# =============================================================================

@dataclass
class StrategyValidationResult:
    """策略验证结果"""
    is_valid: bool
    security: Optional[str] = None  # 提取的股票代码
    strategy_name: Optional[str] = None  # 策略名称
    errors: list = None  # 错误列表
    warnings: list = None  # 警告列表
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


# =============================================================================
# 2. 危险操作检测
# =============================================================================

DANGEROUS_PATTERNS = [
    # 文件操作
    (r'\bopen\s*\(', "禁止使用 open() 进行文件操作"),
    (r'\bfile\s*\(', "禁止使用 file() 进行文件操作"),
    (r'\bos\.', "禁止使用 os 模块"),
    (r'\bsys\.', "禁止使用 sys 模块（除导入外）"),
    (r'\bsubprocess\.', "禁止使用 subprocess 模块"),
    (r'\bshutil\.', "禁止使用 shutil 模块"),
    (r'\bpathlib\.Path\(.*\)\.write', "禁止使用 pathlib 写入文件"),
    
    # 代码执行
    (r'\bexec\s*\(', "禁止使用 exec() 执行代码"),
    (r'\beval\s*\(', "禁止使用 eval() 执行代码"),
    (r'\bcompile\s*\(', "禁止使用 compile() 编译代码"),
    (r'\b__import__\s*\(', "禁止使用 __import__() 动态导入"),
    
    # 网络操作
    (r'\burllib\b', "禁止使用 urllib 进行网络请求"),
    (r'\brequests\b', "禁止使用 requests 进行网络请求"),
    (r'\bsocket\b', "禁止使用 socket 进行网络操作"),
    (r'\bhttp\b', "禁止使用 http 模块"),
    (r'\bftplib\b', "禁止使用 ftplib 模块"),
    
    # 危险内置函数
    (r'\bglobals\s*\(', "禁止使用 globals() 访问全局命名空间"),
    (r'\blocals\s*\(', "禁止使用 locals() 访问局部命名空间"),
    (r'\bvars\s*\(', "禁止使用 vars() 访问变量字典"),
    (r'\bdir\s*\(', "禁止使用 dir() 内省"),
    (r'\bgetattr\s*\(', "警告: getattr() 可能被滥用，请谨慎使用"),
    (r'\bsetattr\s*\(', "警告: setattr() 可能被滥用，请谨慎使用"),
    (r'\bdelattr\s*\(', "警告: delattr() 可能被滥用，请谨慎使用"),
    
    # 退出操作
    (r'\bexit\s*\(', "禁止使用 exit() 退出程序"),
    (r'\bquit\s*\(', "禁止使用 quit() 退出程序"),
    
    # 数据库操作
    (r'\bsqlite3\b', "警告: sqlite3 数据库操作可能存在风险"),
    (r'\bmysql\b', "警告: MySQL 数据库操作可能存在风险"),
    (r'\bpsycopg\b', "警告: PostgreSQL 数据库操作可能存在风险"),
]


def check_dangerous_operations(code: str) -> list:
    """
    检查代码中的危险操作
    
    优化点：
    - 增加更多危险模式
    - 改进错误信息格式
    - 区分错误和警告
    
    Returns:
        错误列表
    """
    errors = []
    warnings = []
    
    for pattern, message in DANGEROUS_PATTERNS:
        matches = re.finditer(pattern, code, re.IGNORECASE)
        for match in matches:
            # 计算行号
            line_num = code[:match.start()].count('\n') + 1
            matched_text = match.group(0)
            
            if "警告" in message:
                warnings.append(f"第 {line_num} 行 [{matched_text}]: {message}")
            else:
                errors.append(f"第 {line_num} 行 [{matched_text}]: {message}")
    
    return errors + warnings  # 合并返回


# =============================================================================
# 3. AST 分析器
# =============================================================================

class StrategyASTAnalyzer(ast.NodeVisitor):
    """策略代码 AST 分析器"""
    
    def __init__(self):
        self.has_initialize = False
        self.has_handle_data = False
        self.security_value = None
        self.imports = []
        self.function_defs = []
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """访问函数定义"""
        self.function_defs.append(node.name)
        
        if node.name == 'initialize':
            self.has_initialize = True
        elif node.name == 'handle_data':
            self.has_handle_data = True
        
        self.generic_visit(node)
    
    def visit_Assign(self, node: ast.Assign):
        """访问赋值语句，查找 g.security"""
        for target in node.targets:
            if isinstance(target, ast.Attribute):
                # 检查是否是 g.security = '...'
                if (isinstance(target.value, ast.Name) and 
                    target.value.id == 'g' and 
                    target.attr == 'security'):
                    # 提取赋值的字符串值
                    if isinstance(node.value, ast.Str):
                        self.security_value = node.value.s
                    elif isinstance(node.value, ast.Constant):
                        self.security_value = node.value.value
        
        self.generic_visit(node)
    
    def visit_Import(self, node: ast.Import):
        """访问 import 语句"""
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """访问 from ... import 语句"""
        if node.module:
            self.imports.append(node.module)
        self.generic_visit(node)


def analyze_strategy_code(code: str) -> Tuple[bool, Optional[str], list]:
    """
    分析策略代码结构
    
    Returns:
        (是否有效, 股票代码, 错误列表)
    """
    errors = []
    
    # 解析 AST
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        errors.append(f"语法错误（第 {e.lineno} 行）: {e.msg}")
        return False, None, errors
    
    # 分析 AST
    analyzer = StrategyASTAnalyzer()
    analyzer.visit(tree)
    
    # 检查必需函数
    if not analyzer.has_initialize:
        errors.append("缺少 initialize(context) 函数")
    
    if not analyzer.has_handle_data:
        errors.append("缺少 handle_data(context, data) 函数")
    
    # 检查股票代码
    if not analyzer.security_value:
        errors.append("未找到 g.security 赋值语句（必须在代码中指定股票代码）")
    
    is_valid = len(errors) == 0
    
    return is_valid, analyzer.security_value, errors


# =============================================================================
# 4. 策略代码验证器
# =============================================================================

def validate_strategy_code(code: str, strategy_name: Optional[str] = None) -> StrategyValidationResult:
    """
    验证策略代码
    
    优化点：
    - 添加更详细的验证信息
    - 区分错误和警告
    - 改进错误提示格式
    
    Args:
        code: 策略代码
        strategy_name: 策略名称（可选）
    
    Returns:
        验证结果
    """
    errors = []
    warnings = []
    
    # 1. 检查代码不为空
    if not code or not code.strip():
        errors.append("策略代码不能为空")
        return StrategyValidationResult(
            is_valid=False,
            errors=errors
        )
    
    # 2. 检查危险操作
    dangerous_issues = check_dangerous_operations(code)
    # 区分错误和警告
    for issue in dangerous_issues:
        if "警告" in issue:
            warnings.append(issue)
        else:
            errors.append(issue)
    
    # 3. 分析代码结构
    is_valid_structure, security, structure_errors = analyze_strategy_code(code)
    errors.extend(structure_errors)
    
    # 4. 额外验证
    # 检查代码长度（防止过大代码）
    if len(code) > 100000:  # 100KB
        warnings.append("策略代码过大（>100KB），可能影响性能")
    
    # 检查是否有无限循环风险
    if re.search(r'\bwhile\s+True\s*:', code):
        warnings.append("检测到 'while True' 无限循环，请确保有退出条件")
    
    # 5. 生成策略名称
    if not strategy_name:
        if security:
            # 使用股票代码作为策略名
            strategy_name = f"strategy_{security.replace('.', '_')}"
        else:
            # 使用时间戳
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            strategy_name = f"strategy_{timestamp}"
    
    # 6. 返回结果
    is_valid = len([e for e in errors if "警告" not in e]) == 0
    
    result = StrategyValidationResult(
        is_valid=is_valid,
        security=security,
        strategy_name=strategy_name,
        errors=errors,
        warnings=warnings
    )
    
    # 打印验证结果（调试用）
    if not is_valid:
        print(f"[VALIDATION] 策略验证失败: {len(errors)} 个错误")
    if warnings:
        print(f"[VALIDATION] {len(warnings)} 个警告")
    
    return result


# =============================================================================
# 5. 策略代码加载器
# =============================================================================

def load_strategy_functions(code: str) -> Tuple[Optional[Callable], Optional[Callable], Dict[str, Any]]:
    """
    动态加载策略代码，提取 initialize 和 handle_data 函数
    
    Args:
        code: 策略代码
    
    Returns:
        (initialize 函数, handle_data 函数, 全局命名空间)
    """
    # 创建受限的命名空间
    namespace = {
        '__builtins__': {
            # 允许的内置函数
            'abs': abs,
            'all': all,
            'any': any,
            'bool': bool,
            'dict': dict,
            'enumerate': enumerate,
            'filter': filter,
            'float': float,
            'int': int,
            'len': len,
            'list': list,
            'map': map,
            'max': max,
            'min': min,
            'print': print,
            'range': range,
            'round': round,
            'set': set,
            'sorted': sorted,
            'str': str,
            'sum': sum,
            'tuple': tuple,
            'zip': zip,
            # 数学函数
            'pow': pow,
            'divmod': divmod,
        },
        # JoinQuant API 导入
        '__name__': '__main__',
    }
    
    # 导入 JoinQuant 适配器
    jq_adapter_code = """
from jq_adapter import (
    g, log, attribute_history, get_price,
    order, order_value, order_target, order_target_value,
    set_benchmark, set_option,
    run_daily, run_weekly, run_monthly,
    record
)
"""
    
    try:
        # 先执行适配器导入
        exec(jq_adapter_code, namespace)
        
        # 执行策略代码
        exec(code, namespace)
        
        # 提取函数
        initialize_func = namespace.get('initialize')
        handle_data_func = namespace.get('handle_data')
        
        return initialize_func, handle_data_func, namespace
        
    except Exception as e:
        print(f"策略加载失败: {e}")
        return None, None, {}


# =============================================================================
# 6. 测试辅助函数
# =============================================================================

def test_validate_simple_strategy():
    """测试简单策略验证"""
    code = """
from jqdata import *

def initialize(context):
    g.security = '000001.XSHE'
    set_benchmark('000300.XSHG')

def handle_data(context, data):
    current_price = data[g.security].close
    if current_price > 10:
        order_value(g.security, 10000)
"""
    
    result = validate_strategy_code(code)
    print(f"验证结果: {result.is_valid}")
    print(f"股票代码: {result.security}")
    print(f"策略名称: {result.strategy_name}")
    print(f"错误: {result.errors}")
    print(f"警告: {result.warnings}")


if __name__ == '__main__':
    test_validate_simple_strategy()
