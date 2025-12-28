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

仓库提供了一个便捷脚本 `scripts/run_scheduler.py`：

```bash
python3 scripts/run_scheduler.py <input.csv> <output.csv> <map.html> [start_date] [max_pair_distance]
```

示例：

```bash
python3 scripts/run_scheduler.py example_sites.csv scheduled_sites.csv site_map.html 2025-01-01 5.0
```

说明：
- `input.csv`：输入站点 CSV，脚本会自动检测分隔符（`,` 或 `;`），并读取头为 `SiteName,Latitude,Longitude,City,EasyAccess,Subcon,TeamNumber,Date` 的列。
- `output.csv`：保存带有 `Date` 字段的调度结果（默认使用 `;` 分隔）。
- `map.html`：可视化输出，依赖 `folium`，显示城市中心、站点标注与队伍路线。
- `start_date`（可选）：调度的起始日期，格式 `YYYY-MM-DD`（不提供则使用当前日期）。
- `max_pair_distance`（可选）：配对阈值（单位：公里），默认 `5.0`。

常见问题
- 如果找不到 `example_sites.csv`，请提供正确路径或使用你自己的 CSV。
- 无法生成地图时，请确认已安装 `folium`：

```bash
pip install folium
```

下一步
- 如需批量运行或集成到调度管线，可将 `SiteScheduler`（`visit_project/site_scheduler.py`）作为库使用并在代码中调用 `schedule()`。
