#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
便捷运行脚本（位于 scripts/）
使用方法: python3 run_scheduler.py [options]
"""

import sys
import argparse
import logging
from pathlib import Path

# Ensure project root is on sys.path when running this script directly
# so sibling package `visit_project` can be imported.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from visit_project.site_scheduler import (
    load_sites_from_csv,
    SiteScheduler,
    save_sites_to_csv,
    generate_map
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='站点访问计划生成器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 run_scheduler.py ecuador_sites.csv scheduled_sites.csv site_map.html 2025-01-01 5.0
  python3 run_scheduler.py ecuador_sites.csv scheduled_sites.csv site_map.html --start-date 2025-01-01 --max-distance 5.0
  python3 run_scheduler.py --help
        """
    )
    
    parser.add_argument(
        'input_file',
        nargs='?',
        default='example_sites.csv',
        help='输入CSV文件路径 (默认: example_sites.csv)'
    )
    parser.add_argument(
        'output_file',
        nargs='?',
        default='scheduled_sites.csv',
        help='输出CSV文件路径 (默认: scheduled_sites.csv)'
    )
    parser.add_argument(
        'map_file',
        nargs='?',
        default='site_map.html',
        help='输出地图文件路径 (默认: site_map.html)'
    )
    parser.add_argument(
        'start_date_pos',
        nargs='?',
        default=None,
        help='开始日期 (位置参数，格式: YYYY-MM-DD)'
    )
    parser.add_argument(
        'max_distance_pos',
        nargs='?',
        type=float,
        default=None,
        help='最大配对距离 (位置参数)'
    )
    parser.add_argument(
        '-s', '--start-date',
        default=None,
        help='开始日期 (格式: YYYY-MM-DD，覆盖位置参数)'
    )
    parser.add_argument(
        '-d', '--max-distance',
        type=float,
        default=None,
        help='最大配对距离 (覆盖位置参数)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='启用详细日志输出'
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()
    
    # 配置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 处理位置参数和选项参数的兼容性
    start_date = args.start_date or args.start_date_pos
    max_pair_distance = args.max_distance or args.max_distance_pos
    
    logger.info(f"正在加载站点数据: {args.input_file}")
    try:
        sites = load_sites_from_csv(args.input_file)
        logger.info(f"成功加载 {len(sites)} 个站点")
    except FileNotFoundError:
        logger.error(f"找不到文件: {args.input_file}")
        logger.info("请确保文件存在")
        return 1
    except Exception as e:
        logger.error(f"加载文件时出错: {e}")
        return 1

    if not sites:
        logger.error("没有找到有效的站点数据")
        logger.info("请检查CSV文件格式是否正确")
        return 1

    # 生成访问计划
    logger.info("正在生成访问计划...")
    try:
        scheduler = SiteScheduler(sites, start_date, max_pair_distance=max_pair_distance)
        scheduled_sites = scheduler.schedule()
    except Exception as e:
        logger.error(f"生成访问计划时出错: {e}")
        return 1

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
    for subcon, info in sorted(summary['by_subcon'].items()):
        print(f"  {subcon}: {info['count']} 个站点, {len(info['dates'])} 天")
    print("\n按城市统计:")
    for city, info in sorted(summary['by_city'].items()):
        print(f"  {city}: {info['count']} 个站点")
    print("="*80 + "\n")

    # 保存结果
    logger.info(f"正在保存结果到: {args.output_file}")
    try:
        save_sites_to_csv(scheduled_sites, args.output_file)
        logger.info("结果已保存")
    except Exception as e:
        logger.error(f"保存文件时出错: {e}")
        return 1

    # 生成地图
    logger.info(f"正在生成地图: {args.map_file}")
    try:
        generate_map(scheduled_sites, args.map_file, scheduler)
        logger.info("地图已生成")
    except Exception as e:
        logger.error(f"生成地图时出错: {e}")
        return 1
    
    print("✅ 完成！")
    print(f"\n请打开 {args.map_file} 查看可视化地图")
    return 0


if __name__ == '__main__':
    sys.exit(main())
