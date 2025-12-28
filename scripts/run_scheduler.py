#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
便捷运行脚本（位于 scripts/）
"""

import sys
from cursor_project.site_scheduler import (
    load_sites_from_csv,
    SiteScheduler,
    save_sites_to_csv,
    generate_map
)


def main():
    # 默认使用示例文件
    input_file = 'example_sites.csv'
    output_file = 'scheduled_sites.csv'
    map_file = 'site_map.html'
    start_date = None
    max_pair_distance = None
    
    # 如果提供了命令行参数
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    if len(sys.argv) > 3:
        map_file = sys.argv[3]
    if len(sys.argv) > 4:
        start_date = sys.argv[4]
    if len(sys.argv) > 5:
        try:
            max_pair_distance = float(sys.argv[5])
        except Exception:
            max_pair_distance = None

    print(f"正在加载站点数据: {input_file}")
    try:
        sites = load_sites_from_csv(input_file)
        print(f"成功加载 {len(sites)} 个站点")
    except FileNotFoundError:
        print(f"错误: 找不到文件 {input_file}")
        print(f"请确保文件存在，或使用 example_sites.csv 作为示例")
        return
    except Exception as e:
        print(f"错误: 加载文件时出错: {e}")
        return

    if not sites:
        print("错误: 没有找到有效的站点数据")
        print("请检查CSV文件格式是否正确")
        return

    # 生成访问计划
    print("正在生成访问计划...")
    scheduler = SiteScheduler(sites, start_date, max_pair_distance=max_pair_distance)
    scheduled_sites = scheduler.schedule()

    # 打印摘要
    summary = scheduler.get_schedule_summary()
    print("\n" + "="*80)
    print("站点访问计划摘要")
    print("="*80)
    print(f"总站点数: {summary['total_sites']}")
    print(f"已分配站点数: {summary['scheduled_sites']}")
    if summary['date_range']:
        print(f"日期范围: {summary['date_range']['start']} 至 {summary['date_range']['end']}")
    print("\n按分包商统计:")
    for subcon, info in summary['by_subcon'].items():
        print(f"  {subcon}: {info['count']} 个站点, {len(info['dates'])} 天")
    print("\n按城市统计:")
    for city, info in summary['by_city'].items():
        print(f"  {city}: {info['count']} 个站点")
    print("="*80 + "\n")

    # 保存结果
    print(f"正在保存结果到: {output_file}")
    save_sites_to_csv(scheduled_sites, output_file)
    print("结果已保存")

    # 生成地图
    print(f"正在生成地图: {map_file}")
    generate_map(scheduled_sites, map_file, scheduler)
    print("完成！")
    print(f"\n请打开 {map_file} 查看可视化地图")


if __name__ == '__main__':
    main()
