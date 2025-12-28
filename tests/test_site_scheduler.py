import os
import csv
import math
import tempfile

import pytest
from cursor_project.site_scheduler import SiteScheduler, load_sites_from_csv, Site


def test_haversine_distance():
    s = SiteScheduler([])
    # 大约 1 度经度在赤道约111.2 km（近似）
    d = s._haversine_distance(0.0, 0.0, 0.0, 1.0)
    assert pytest.approx(d, rel=1e-3) == 111.195


def test_find_all_pairs():
    sites = [
        Site('A', 0.0, 0.0, 'City', '', 'Sub', 1),
        Site('B', 0.0, 0.03, 'City', '', 'Sub', 1),  # ~3.3km
        Site('C', 1.0, 1.0, 'City', '', 'Sub', 1),
    ]
    s = SiteScheduler(sites)
    pairs = s._find_all_pairs(sites, max_distance=5.0)
    # 只有 A-B 成对
    assert len(pairs) == 1
    p = pairs[0]
    assert (p[0].site_name, p[1].site_name) in [('A', 'B'), ('B', 'A')]


def test_load_sites_from_csv(tmp_path):
    csv_path = tmp_path / 'test.csv'
    headers = ['SiteName', 'Latitude', 'Longitude', 'City', 'EasyAccess', 'Subcon', 'TeamNumber', 'Date']
    rows = [
        ['S1', '0.0', '0.0', 'City', 'Yes', 'Sub', '1', ''],
        ['S2', '10.0', '10.0', 'City', 'No', 'Sub', '', '']
    ]
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(headers)
        writer.writerows(rows)

    sites = load_sites_from_csv(str(csv_path))
    assert len(sites) == 2
    assert sites[0].site_name == 'S1'
    assert sites[1].team_number == 1
