# 快速开始

本页面说明如何快速运行调度脚本并生成调度结果与地图。

前提
- 已安装 Python 3.8+。
- 建议安装依赖（部分功能如地图需要 `folium`）。

安装依赖（可选）：

```bash
pip install -r requirements.txt
```

运行示例

仓库提供了一个便捷脚本 `scripts/run_scheduler.py`（推荐以包方式运行）：

```bash
# 基本用法（位置参数）
python -m scripts.run_scheduler <input.csv> <output.csv> <map.html> [start_date] [max_pair_distance]

# 使用选项参数
python -m scripts.run_scheduler <input.csv> <output.csv> <map.html> [--start-date DATE] [--max-distance DISTANCE]

# 查看帮助
python -m scripts.run_scheduler --help
```

示例（位置参数格式）：

```bash
python -m scripts.run_scheduler ecuador_sites.csv scheduled_sites.csv site_map.html 2025-01-01 5.0
```

示例（选项参数格式）：

```bash
# 使用长选项
python -m scripts.run_scheduler ecuador_sites.csv scheduled_sites.csv site_map.html --start-date 2025-01-01 --max-distance 5.0

# 使用短选项
python -m scripts.run_scheduler ecuador_sites.csv scheduled_sites.csv site_map.html -s 2025-01-01 -d 5.0

# 启用详细日志
python -m scripts.run_scheduler ecuador_sites.csv scheduled_sites.csv site_map.html 2025-01-01 5.0 -v
```

说明：
- `input.csv`：输入站点 CSV，脚本会自动检测分隔符（`,` 或 `;`），并读取头为 `SiteName,Latitude,Longitude,City,EasyAccess,Subcon,TeamNumber,Date` 的列。
- `output.csv`：保存带有 `Date` 字段的调度结果（默认使用 `;` 分隔）。
- `map.html`：可视化输出，依赖 `folium`，显示城市中心、站点标注与队伍路线。
- `start_date`（可选，位置参数或 `--start-date`/-s`）：调度的起始日期，格式 `YYYY-MM-DD`（不提供则使用当前日期）。
- `max_pair_distance`（可选，位置参数或 `--max-distance`/`-d`）：配对阈值（单位：公里），默认 `5.0`。
- `-v, --verbose`（可选）：启用详细日志输出，用于调试。

常见问题

- 如果找不到 `example_sites.csv`，请提供正确路径或使用你自己的 CSV。
- 无法生成地图时，请确认已安装 `folium`：

```bash
pip install folium
```

- 想要查看详细的运行日志，使用 `-v` 或 `--verbose` 选项：

```bash
python -m scripts.run_scheduler ecuador_sites.csv scheduled_sites.csv site_map.html 2025-01-01 -v
```

- 脚本支持位置参数和选项参数的混合使用，选项参数会覆盖对应的位置参数。

下一步
- 如需批量运行或集成到调度管线，可将 `SiteScheduler`（`visit_project/site_scheduler.py`）作为库使用并在代码中调用 `schedule()`。
