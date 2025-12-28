#!/bin/bash
# 项目初始化脚本 - 创建虚拟环境并安装依赖

echo "正在设置项目环境..."

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到python3，请先安装Python 3.7+"
    exit 1
fi

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
else
    echo "虚拟环境已存在，跳过创建"
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 升级pip
echo "升级pip..."
pip install --upgrade pip

# 安装依赖
echo "安装项目依赖..."
pip install -r requirements.txt

echo ""
echo "=========================================="
echo "项目环境设置完成！"
echo "=========================================="
echo ""
echo "要激活虚拟环境，请运行:"
echo "  source venv/bin/activate"
echo "或者:"
echo "  source activate.sh"
echo ""
echo "要运行站点访问计划生成器:"
echo "  python site_scheduler.py example_sites.csv"
echo "或者:"
echo "  python run_scheduler.py example_sites.csv"
echo ""



