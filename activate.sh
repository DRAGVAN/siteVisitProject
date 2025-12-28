#!/bin/bash
# 激活虚拟环境的便捷脚本

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 激活虚拟环境
source "$SCRIPT_DIR/venv/bin/activate"

echo "虚拟环境已激活！"
echo "Python路径: $(which python)"
echo "Python版本: $(python --version)"
echo ""
echo "要退出虚拟环境，请输入: deactivate"



