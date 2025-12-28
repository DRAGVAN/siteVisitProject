#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
站点访问计划生成器库模块
"""

import csv
import math
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
import json


@dataclass
class Site:
    """站点信息数据类"""
    site_name: str
    latitude: float
    longitude: float
    city: str
    easy_access: str
    subcon: str
    team_number: int
    date: str = ""


class SiteScheduler:
    """站点访问计划调度器"""
    
    # 可配置常量（可通过CLI传入覆盖）
    DEFAULT_MAX_PAIR_DISTANCE = 5.0  # 公里

    def __init__(self, sites: List[Site], start_date: Optional[str] = None, max_pair_distance: Optional[float] = None):
        """
        初始化调度器
        
        Args:
            sites: 站点列表
            start_date: 开始日期（格式：YYYY-MM-DD），默认为今天
        """
        self.sites = sites
        if start_date:
            self.current_date = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            self.current_date = datetime.now()
        # 最大配对距离（公里）
        self.max_pair_distance = max_pair_distance if max_pair_distance is not None else self.DEFAULT_MAX_PAIR_DISTANCE
        
        # 按城市和分包商分组
        self.sites_by_city_subcon = defaultdict(lambda: defaultdict(list))
        for site in sites:
            self.sites_by_city_subcon[site.city][site.subcon].append(site)
        
        # 计算每个城市的中心点（所有站点的平均经纬度）
        self.city_centers = {}
        for city, subcon_dict in self.sites_by_city_subcon.items():
            all_city_sites = []
            for sites_list in subcon_dict.values():
                all_city_sites.extend(sites_list)
            if all_city_sites:
                center_lat = sum(s.latitude for s in all_city_sites) / len(all_city_sites)
                center_lon = sum(s.longitude for s in all_city_sites) / len(all_city_sites)
                self.city_centers[city] = (center_lat, center_lon)
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        使用 Haversine 公式计算两点间的大圆距离（单位：公里）。

        明确接受四个浮点参数：`lat1, lon1, lat2, lon2`。
        """
        R = 6371.0  # 地球半径（公里）

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def distance_between_sites(self, site1: Site, site2: Site) -> float:
        """
        站点对象间距离包装函数，便于对 Site 对象直接调用。
        """
        return self._haversine_distance(site1.latitude, site1.longitude,
                                        site2.latitude, site2.longitude)
    
    def _find_nearby_sites(self, site: Site, sites: List[Site], max_distance: Optional[float] = None) -> List[Site]:
        """
        查找附近的站点（5km内）
        
        Args:
            site: 参考站点
            sites: 候选站点列表
            max_distance: 最大距离（公里）
            
        Returns:
            附近的站点列表
        """
        if max_distance is None:
            max_distance = self.max_pair_distance

        nearby = []
        for s in sites:
            if s != site and not s.date:  # 未分配日期的站点
                distance = self._haversine_distance(site.latitude, site.longitude, s.latitude, s.longitude)
                if distance <= max_distance:
                    nearby.append((s, distance))
        
        # 按距离排序
        nearby.sort(key=lambda x: x[1])
        return [s for s, _ in nearby]
    
    def _distance_to_center(self, site: Site, city: str) -> float:
        """
        计算站点到城市中心的距离
        
        Args:
            site: 站点
            city: 城市名称
            
        Returns:
            到城市中心的距离（公里）
        """
        if city not in self.city_centers:
            return 0.0
        center_lat, center_lon = self.city_centers[city]
        return self._haversine_distance(site.latitude, site.longitude, center_lat, center_lon)
    
    def _get_site_id(self, site: Site) -> str:
        """获取站点的唯一标识符"""
        return f"{site.site_name}_{site.latitude}_{site.longitude}"
    
    def _find_all_pairs(self, sites: List[Site], max_distance: Optional[float] = None) -> List[Tuple[Site, Site, float]]:
        """
        找出所有5km内的成对站点
        优先数量多，然后距离近
        
        Args:
            sites: 候选站点列表
            max_distance: 最大距离（公里）
            
        Returns:
            站点对列表，每个元素为 (站点1, 站点2, 距离)
        """
        pairs = []
        used_site_ids = set()
        
        # 找出所有可能的站点对
        if max_distance is None:
            max_distance = self.max_pair_distance

        for i, site1 in enumerate(sites):
            site1_id = self._get_site_id(site1)
            if site1_id in used_site_ids:
                continue
            for j, site2 in enumerate(sites[i+1:], start=i+1):
                site2_id = self._get_site_id(site2)
                if site2_id in used_site_ids:
                    continue
                distance = self._haversine_distance(site1.latitude, site1.longitude,
                                                    site2.latitude, site2.longitude)
                if distance <= max_distance:
                    pairs.append((site1, site2, distance))
        
        # 按距离排序（距离近的优先）
        pairs.sort(key=lambda x: x[2])
        
        # 贪心选择：尽可能多的不重叠的站点对
        selected_pairs = []
        used_site_ids_in_pairs = set()
        
        for site1, site2, dist in pairs:
            site1_id = self._get_site_id(site1)
            site2_id = self._get_site_id(site2)
            if site1_id not in used_site_ids_in_pairs and site2_id not in used_site_ids_in_pairs:
                selected_pairs.append((site1, site2, dist))
                used_site_ids_in_pairs.add(site1_id)
                used_site_ids_in_pairs.add(site2_id)
        
        return selected_pairs
    
    def schedule(self) -> List[Site]:
        """
        生成站点访问计划
        
        新算法规则：
        1. 按城市划分簇，每个城市独立处理
        2. 在每个簇中找出所有尽可能多的5km内的成对站点（优先数量多，然后距离近）
        3. 从城市中心出发，找距离出发点最近的站点：
           - 如果属于成对站点，访问两个（先近后远）
           - 如果不属于成对站点，只访问一个
           - 每天访问完回家，第二天继续
        4. 每个城市分包商队伍数量假设为始终为1
        
        Returns:
            已分配日期的站点列表
        """
        # 按城市分组处理，每个城市独立调度
        for city, subcon_dict in self.sites_by_city_subcon.items():
            # 每个城市从开始日期独立开始
            city_start_date = self.current_date
            
            # 按分包商处理
            for subcon, sites in subcon_dict.items():
                # 假设每个城市分包商队伍数量始终為1
                team_count = 1
                
                # 获取未分配的站点
                unassigned_sites = [s for s in sites if not s.date]
                
                if not unassigned_sites:
                    continue
                
                # 步骤2：找出所有尽可能多的5km内的成对站点
                # 优先数量多，然后距离近
                pairs = self._find_all_pairs(unassigned_sites, max_distance=5.0)
                
                # 创建站点对集合（用于快速查找）
                paired_site_ids = set()
                site_to_pair = {}  # 站点ID -> 配对信息 (partner_site, distance)
                for site1, site2, dist in pairs:
                    site1_id = self._get_site_id(site1)
                    site2_id = self._get_site_id(site2)
                    paired_site_ids.add(site1_id)
                    paired_site_ids.add(site2_id)
                    site_to_pair[site1_id] = (site2, dist)
                    site_to_pair[site2_id] = (site1, dist)
                
                # 步骤3：从城市中心出发，按距离排序，依次安排访问
                current_date = city_start_date
                
                while unassigned_sites:
                    # 找出距离城市中心最近的未分配站点
                    unassigned_sites.sort(key=lambda s: self._distance_to_center(s, city))
                    nearest_site = unassigned_sites[0]
                    
                    # 判断这个站点是否属于成对站点
                    nearest_site_id = self._get_site_id(nearest_site)
                    if nearest_site_id in paired_site_ids and nearest_site_id in site_to_pair:
                        # 属于成对站点，访问两个站点
                        partner_site, pair_distance = site_to_pair[nearest_site_id]
                        partner_site_id = self._get_site_id(partner_site)
                        
                        # 确保配对站点也在未分配列表中
                        if partner_site in unassigned_sites:
                            # 确定访问顺序：先访问距离城市中心近的，再访问远的
                            dist1 = self._distance_to_center(nearest_site, city)
                            dist2 = self._distance_to_center(partner_site, city)
                            
                            if dist1 <= dist2:
                                day_group = [nearest_site, partner_site]
                            else:
                                day_group = [partner_site, nearest_site]
                            
                            # 分配日期
                            date_str = current_date.strftime("%Y-%m-%d")
                            for site in day_group:
                                site.date = date_str
                                if not hasattr(site, 'team_index'):
                                    site.team_index = 0
                            
                            # 从未分配列表中移除
                            unassigned_sites.remove(nearest_site)
                            unassigned_sites.remove(partner_site)
                            
                            # 从配对集合中移除（避免重复使用）
                            paired_site_ids.discard(nearest_site_id)
                            paired_site_ids.discard(partner_site_id)
                            if nearest_site_id in site_to_pair:
                                del site_to_pair[nearest_site_id]
                            if partner_site_id in site_to_pair:
                                del site_to_pair[partner_site_id]
                        else:
                            # 配对站点已被分配，只访问当前站点
                            date_str = current_date.strftime("%Y-%m-%d")
                            nearest_site.date = date_str
                            if not hasattr(nearest_site, 'team_index'):
                                nearest_site.team_index = 0
                            unassigned_sites.remove(nearest_site)
                            paired_site_ids.discard(nearest_site_id)
                            if nearest_site_id in site_to_pair:
                                del site_to_pair[nearest_site_id]
                    else:
                        # 不属于成对站点，只访问这一个站点
                        date_str = current_date.strftime("%Y-%m-%d")
                        nearest_site.date = date_str
                        if not hasattr(nearest_site, 'team_index'):
                            nearest_site.team_index = 0
                        unassigned_sites.remove(nearest_site)
                    
                    # 移动到下一天
                    current_date += timedelta(days=1)
        
        return self.sites
    
    def get_schedule_summary(self) -> Dict:
        """
        获取调度摘要信息
        
        Returns:
            调度摘要字典
        """
        summary = {
            'total_sites': len(self.sites),
            'scheduled_sites': len([s for s in self.sites if s.date]),
            'date_range': {},
            'by_subcon': defaultdict(lambda: {'count': 0, 'dates': set()}),
            'by_city': defaultdict(lambda: {'count': 0})
        }
        
        dates = [s.date for s in self.sites if s.date]
        if dates:
            summary['date_range']['start'] = min(dates)
            summary['date_range']['end'] = max(dates)
        
        for site in self.sites:
            if site.date:
                summary['by_subcon'][site.subcon]['count'] += 1
                summary['by_subcon'][site.subcon]['dates'].add(site.date)
                summary['by_city'][site.city]['count'] += 1
        
        # 转换set为list以便JSON序列化
        for subcon_info in summary['by_subcon'].values():
            subcon_info['dates'] = sorted(list(subcon_info['dates']))
        
        return summary


def load_sites_from_csv(filepath: str) -> List[Site]:
    """
    从CSV文件加载站点信息
    
    Args:
        filepath: CSV文件路径
        
    Returns:
        站点列表
    """
    sites = []

    with open(filepath, 'r', encoding='utf-8') as f:
        # 尝试不同的分隔符
        sample = f.read(1024)
        f.seek(0)

        delimiter = ';' if ';' in sample else ','
        reader = csv.DictReader(f, delimiter=delimiter)

        for lineno, row in enumerate(reader, start=2):
            # 跳过空行
            if not row.get('SiteName', '').strip():
                continue

            try:
                lat = float(row.get('Latitude', 0))
                lon = float(row.get('Longitude', 0))
                # 简单的经纬度校验
                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    logging.warning("跳过行 %d: 经纬度超出范围: %s", lineno, row)
                    continue

                team_str = row.get('TeamNumber', '').strip()
                team_num = int(team_str) if team_str else 1

                site = Site(
                    site_name=row.get('SiteName', '').strip(),
                    latitude=lat,
                    longitude=lon,
                    city=row.get('City', '').strip(),
                    easy_access=row.get('EasyAccess', '').strip(),
                    subcon=row.get('Subcon', '').strip(),
                    team_number=team_num,
                    date=row.get('Date', '').strip()
                )
                sites.append(site)
            except (ValueError, KeyError) as e:
                logging.warning("警告: 跳过无效行 %d: %s, 错误: %s", lineno, row, e)
                continue

    return sites


def save_sites_to_csv(sites: List[Site], filepath: str):
    """
    保存站点信息到CSV文件
    
    Args:
        sites: 站点列表
        filepath: 输出文件路径
    """
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['SiteName', 'Latitude', 'Longitude', 'City', 'EasyAccess', 'Subcon', 'TeamNumber', 'Date'])
        
        for site in sites:
            writer.writerow([
                site.site_name,
                site.latitude,
                site.longitude,
                site.city,
                site.easy_access,
                site.subcon,
                site.team_number,
                site.date
            ])


def generate_map(sites: List[Site], output_file: str = 'site_map.html', scheduler: SiteScheduler = None):
    """
    生成站点访问计划地图
    每个队伍用不同颜色标记，显示按日期顺序的路线
    """
    try:
        import folium
        from folium import plugins
    except ImportError:
        logging.error("需要安装 folium 库来生成地图。请运行: pip install folium")
        return
    
    # 计算地图中心点
    if not sites:
        logging.error("没有站点数据，无法生成地图")
        return
    
    avg_lat = sum(s.latitude for s in sites) / len(sites)
    avg_lon = sum(s.longitude for s in sites) / len(sites)
    
    # 创建地图
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=10)
    
    # 计算每个城市的中心点
    city_centers = {}
    if scheduler and hasattr(scheduler, 'city_centers'):
        city_centers = scheduler.city_centers
    else:
        # 如果没有传入scheduler，从站点数据计算城市中心
        city_sites = defaultdict(list)
        for site in sites:
            city_sites[site.city].append(site)
        for city, city_sites_list in city_sites.items():
            if city_sites_list:
                center_lat = sum(s.latitude for s in city_sites_list) / len(city_sites_list)
                center_lon = sum(s.longitude for s in city_sites_list) / len(city_sites_list)
                city_centers[city] = (center_lat, center_lon)

    # 在地图上标记城市中心
    for city, (center_lat, center_lon) in city_centers.items():
        folium.Marker(
            location=[center_lat, center_lon],
            popup=folium.Popup(f'<b>{city}</b><br>城市中心（出发地）', max_width=200),
            tooltip=f'{city} - 城市中心',
            icon=folium.Icon(color='black', icon='home', prefix='fa')
        ).add_to(m)
        # 添加城市中心标记
        folium.CircleMarker(
            location=[center_lat, center_lon],
            radius=15,
            popup=f'{city} - 城市中心',
            color='black',
            fillColor='black',
            fillOpacity=0.8,
            weight=3
        ).add_to(m)

    # 定义队伍颜色列表（为每个分包商+城市组合分配颜色）
    team_colors = [
        'red', 'blue', 'green', 'purple', 'orange', 'darkred',
        'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue',
        'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen',
        'gray', 'black', 'lightgray'
    ]

    # 为每个分包商+城市组合分配颜色
    team_color_map = {}
    team_counter = 0

    # 按日期和分包商分组站点
    sites_by_date_subcon_city = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for site in sites:
        if site.date:
            sites_by_date_subcon_city[site.date][site.subcon][site.city].append(site)

    # 为每个分包商+城市组合分配颜色
    for date in sorted(sites_by_date_subcon_city.keys()):
        for subcon in sites_by_date_subcon_city[date].keys():
            for city in sites_by_date_subcon_city[date][subcon].keys():
                team_key = f"{subcon}_{city}"
                if team_key not in team_color_map:
                    team_color_map[team_key] = team_colors[team_counter % len(team_colors)]
                    team_counter += 1

    # 使用站点的唯一标识符作为key
    def get_site_key(site):
        return f"{site.site_name}_{site.latitude}_{site.longitude}"

    # 为每个站点分配访问顺序（每个城市独立编号）
    visit_order = {}

    # 按城市、日期、分包商分组处理，分配访问顺序
    # 先按城市分组
    sites_by_city = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for site in sites:
        if site.date:
            sites_by_city[site.city][site.date][site.subcon].append(site)

    # 为每个城市独立分配顺序
    for city in sorted(sites_by_city.keys()):
        city_order_counter = 1
        sorted_dates = sorted(sites_by_city[city].keys())
        for date in sorted_dates:
            for subcon in sorted(sites_by_city[city][date].keys()):
                day_sites = sites_by_city[city][date][subcon]
                # 如果同一天有多个站点（5km内的），按距离城市中心的距离排序
                if len(day_sites) > 1:
                    # 按距离城市中心的距离排序
                    if city in city_centers:
                        center_lat, center_lon = city_centers[city]
                        day_sites.sort(key=lambda s: (
                            (s.latitude - center_lat)**2 + (s.longitude - center_lon)**2
                        ))
                    else:
                        # 如果没有城市中心，按经纬度排序
                        center_lat = sum(s.latitude for s in day_sites) / len(day_sites)
                        center_lon = sum(s.longitude for s in day_sites) / len(day_sites)
                        day_sites.sort(key=lambda s: (
                            (s.latitude - center_lat)**2 + (s.longitude - center_lon)**2
                        ))
                
                for site in day_sites:
                    visit_order[get_site_key(site)] = city_order_counter
                    city_order_counter += 1

    # 计算日期序号（第一天、第二天等），基于所有站点的全局日期集合
    all_dates = sorted({s.date for s in sites if s.date})
    date_to_day_number = {d: i + 1 for i, d in enumerate(all_dates)}

    # 为每个站点添加标记
    for site in sites:
        if not site.date:
            continue
        
        order = visit_order.get(get_site_key(site), 0)
        day_num = date_to_day_number.get(site.date, 0)
        team_key = f"{site.subcon}_{site.city}"
        team_color = team_color_map.get(team_key, 'gray')
        
        # 根据EasyAccess选择标记颜色（站点本身的颜色）
        easy_access_lower = site.easy_access.lower() if site.easy_access else ''
        # folium只支持特定颜色，yellow不在列表中，使用orange代替
        marker_color = 'green' if easy_access_lower in ['yes', 'true', '1', '是'] else 'orange'
        
        # 创建弹出窗口内容
        popup_html = f"""
        <div style="font-family: Arial, sans-serif;">
            <h4 style="margin: 5px 0;">{site.site_name}</h4>
            <p style="margin: 3px 0;"><strong>分包商:</strong> {site.subcon}</p>
            <p style="margin: 3px 0;"><strong>城市:</strong> {site.city}</p>
            <p style="margin: 3px 0;"><strong>访问日期:</strong> {site.date} (第{day_num}天)</p>
            <p style="margin: 3px 0;"><strong>访问顺序:</strong> {order if order > 0 else '未分配'} ({site.city}城市内)</p>
            <p style="margin: 3px 0;"><strong>EasyAccess:</strong> {site.easy_access}</p>
        </div>
        """
        
        # 添加标记，在标签中显示顺序（每个城市独立编号）
        label_text = f"{order}. {site.site_name}" if order > 0 else site.site_name
        folium.Marker(
            location=[site.latitude, site.longitude],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=label_text,
            icon=folium.Icon(color=marker_color, icon='info-sign', prefix='glyphicon')
        ).add_to(m)
    
    # 为每个队伍按日期顺序添加路线连线
    # 按分包商+城市分组
    teams_routes = defaultdict(lambda: defaultdict(list))
    for site in sites:
        if site.date:
            team_key = f"{site.subcon}_{site.city}"
            teams_routes[team_key][site.date].append(site)
    
    # 为每个队伍绘制路线（只连接站点，不连接城市中心）
    # 按分包商+城市+日期分组
    teams_routes_detailed = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for site in sites:
        if site.date:
            team_key = f"{site.subcon}_{site.city}"
            team_idx = getattr(site, 'team_index', 0)  # 获取队伍索引
            teams_routes_detailed[team_key][team_idx][site.date].append(site)
    
    # 定义不同队伍的线型（用于区分同一分包商的不同队伍）
    dash_patterns = [None, '10, 5', '5, 5']
    
    # 为每个队伍绘制路线
    for team_key, teams_dict in teams_routes_detailed.items():
        team_color = team_color_map.get(team_key, 'gray')
        subcon, city = team_key.split('_', 1)
        
        # 为每个队伍（同一分包商的不同队伍）绘制路线
        for team_idx, dates_dict in teams_dict.items():
            # 按日期排序
            sorted_team_dates = sorted(dates_dict.keys())
            
            # 选择线型（区分不同队伍）
            dash_pattern = dash_patterns[team_idx % len(dash_patterns)]
            line_weight = 4 - team_idx  # 不同队伍用不同粗细
            
            # 为同一天的站点绘制路线（只连接站点，不连接城市中心）
            for date in sorted_team_dates:
                day_sites = dates_dict[date]
                day_num = date_to_day_number.get(date, 0)
                
                if len(day_sites) > 1:
                    # 按访问顺序排序
                    day_sites.sort(key=lambda s: visit_order.get(get_site_key(s), 9999))
                    
                    # 只连接站点之间的路线
                    route_locations = [[s.latitude, s.longitude] for s in day_sites]
                    
                    # 队伍标识
                    team_label = f"队伍{team_idx + 1}" if len(teams_dict) > 1 else ""
                    
                    # 绘制路线
                    folium.PolyLine(
                        locations=route_locations,
                        color=team_color,
                        weight=line_weight,
                        opacity=0.7,
                        dashArray=dash_pattern,
                        popup=f"{subcon} {team_label} ({city}) - 第{day_num}天 ({len(day_sites)}个站点)",
                        tooltip=f"{subcon} {team_label} - 第{day_num}天"
                    ).add_to(m)
        
        # 为不同日期之间的站点连线（显示时间顺序）
        if len(teams_dict) > 0:
            main_team_dates = sorted(teams_dict[0].keys()) if 0 in teams_dict else []
            if len(main_team_dates) > 1:
                for i in range(len(main_team_dates) - 1):
                    prev_date = main_team_dates[i]
                    next_date = main_team_dates[i + 1]
                    
                    prev_sites = teams_dict[0][prev_date]
                    next_sites = teams_dict[0][next_date]
                    
                    if prev_sites and next_sites:
                        prev_sites.sort(key=lambda s: visit_order.get(get_site_key(s), 9999))
                        next_sites.sort(key=lambda s: visit_order.get(get_site_key(s), 9999))
                        
                        last_site = prev_sites[-1]
                        first_site = next_sites[0]
                        
                        # 绘制虚线连接：前一天最后一个站点 → 第二天第一个站点
                        folium.PolyLine(
                            locations=[[last_site.latitude, last_site.longitude],
                                      [first_site.latitude, first_site.longitude]],
                            color=team_color,
                            weight=2,
                            opacity=0.3,
                            dashArray='5, 10',
                            popup=f"{subcon} ({city}) - 第{date_to_day_number.get(prev_date, 0)}天 → 第{date_to_day_number.get(next_date, 0)}天",
                            tooltip=f"{subcon} - 跨天路线"
                        ).add_to(m)
    
    # 添加图例
    legend_items = []
    legend_items.append('<h4 style="margin: 0 0 10px 0;">图例</h4>')
    legend_items.append('<p style="margin: 5px 0;"><span style="color: green; font-size: 18px;">●</span> EasyAccess站点</p>')
    legend_items.append('<p style="margin: 5px 0;"><span style="color: #FFD700; font-size: 18px;">●</span> 其他站点</p>')
    legend_items.append('<p style="margin: 10px 0 5px 0;"><strong>队伍路线颜色:</strong></p>')
    
    # 为每个队伍添加图例
    for team_key, color in sorted(team_color_map.items()):
        subcon, city = team_key.split('_', 1)
        legend_items.append(f'<p style="margin: 3px 0;"><span style="color: {color}; font-size: 18px;">━</span> {subcon} ({city})</p>')
    
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 250px; max-height: 500px; overflow-y: auto;
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px; border-radius: 5px;">
    {''.join(legend_items)}
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # 保存地图
    m.save(output_file)
    logging.info("地图已保存到: %s", output_file)
