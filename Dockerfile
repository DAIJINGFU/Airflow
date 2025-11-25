FROM apache/airflow:3.1.3

# 安装量化分析依赖（使用预编译wheel包，无需编译器）
USER airflow
RUN pip install --no-cache-dir \
    backtrader>=1.9.76 \
    loguru>=0.7.0 \
    pandas>=2.0.0 \
    numpy>=1.24.0 \
    pyqlib>=0.9.0
