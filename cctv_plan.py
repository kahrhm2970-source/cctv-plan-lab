"""Offline CCTV storage/PoE planning lab. Python 3.10+, stdlib only."""
import argparse
import html
import json
import math
from pathlib import Path
import re


def number(v, low, high):
    if type(v) not in (int,float) or not math.isfinite(v) or not low <= v <= high:
        raise ValueError('Numeric input outside documented bounds')


def keys(v, expected):
    if not isinstance(v,dict) or set(v) != set(expected):
        raise ValueError('Missing or extra fields')


def calculate(plan):
    keys(plan,['retention_days','usable_storage_tb','storage_margin_percent','poe_margin_percent','switches','camera_groups'])
    number(plan['retention_days'],1,3650); number(plan['usable_storage_tb'],0,100000)
    for key in ('storage_margin_percent','poe_margin_percent'): number(plan[key],0,100)
    if not isinstance(plan['switches'],list) or not 1 <= len(plan['switches']) <= 128:
        raise ValueError('Require 1-128 switches')
    if not isinstance(plan['camera_groups'],list) or not 1 <= len(plan['camera_groups']) <= 1000:
        raise ValueError('Require 1-1000 camera groups')
    switches={}
    for s in plan['switches']:
        keys(s,['id','ports','budget_w','port_limit_w'])
        if not isinstance(s['id'],str) or not re.fullmatch(r'SW-\d{1,4}',s['id']) or s['id'] in switches:
            raise ValueError('Require unique synthetic switch IDs SW-number')
        if type(s['ports']) is not int or not 1 <= s['ports'] <= 256: raise ValueError('Invalid port count')
        number(s['budget_w'],0,10000); number(s['port_limit_w'],0,1000)
        switches[s['id']]={**s,'used_ports':0,'load_w':0}
    ids=set(); daily=0; bitrate=0; camera_count=0; findings=[]
    for g in plan['camera_groups']:
        keys(g,['id','count','bitrate_mbps','recording_hours_per_day','pse_w_per_camera','switch_id'])
        if not isinstance(g['id'],str) or not re.fullmatch(r'GROUP-\d{1,4}',g['id']) or g['id'] in ids:
            raise ValueError('Require unique group IDs GROUP-number')
        ids.add(g['id'])
        if type(g['count']) is not int or not 1 <= g['count'] <= 10000: raise ValueError('Invalid camera count')
        number(g['bitrate_mbps'],0.001,1000); number(g['recording_hours_per_day'],0.001,24)
        number(g['pse_w_per_camera'],0.001,1000)
        if not isinstance(g['switch_id'],str) or g['switch_id'] not in switches: raise ValueError('Unknown switch')
        s=switches[g['switch_id']]; n=g['count']; camera_count+=n
        s['used_ports']+=n; s['load_w']+=n*g['pse_w_per_camera']
        bitrate+=n*g['bitrate_mbps']
        daily+=n*g['bitrate_mbps']*1e6/8*3600*g['recording_hours_per_day']/1e12
        if g['pse_w_per_camera']>s['port_limit_w']:
            findings.append({'code':'PORT_POWER_LIMIT','item':g['id']})
    sf=1+plan['storage_margin_percent']/100
    raw=daily*plan['retention_days']; required=raw*sf
    if required>plan['usable_storage_tb']: findings.append({'code':'STORAGE_SHORTFALL','item':'storage'})
    pf=1+plan['poe_margin_percent']/100
    loads=[]
    for sid,s in switches.items():
        if s['used_ports']>s['ports']: findings.append({'code':'PORT_COUNT_SHORTFALL','item':sid})
        if s['load_w']*pf>s['budget_w']: findings.append({'code':'POE_BUDGET_SHORTFALL','item':sid})
        loads.append({'id':sid,'used_ports':s['used_ports'],'available_ports':s['ports'],
                      'pse_load_w':round(s['load_w'],4),'planned_pse_w':round(s['load_w']*pf,4),'budget_w':s['budget_w']})
    return {'summary':{'camera_count':camera_count,'stream_bitrate_sum_mbps':round(bitrate,4),
                      'daily_video_tb':round(daily,6),'raw_video_tb':round(raw,6),
                      'planned_storage_tb':round(required,6),
                      'planning_retention_days':round(plan['usable_storage_tb']/(daily*sf),4),
                      'findings':len(findings)},'switches':loads,'findings':findings}


def render(report):
    body=html.escape(json.dumps(report,indent=2))
    return '<!doctype html><html lang="en"><meta charset="utf-8"><title>CCTV Plan Lab</title><style>body{font:16px system-ui;max-width:1000px;margin:40px auto;padding:20px;background:#f1f6fa;color:#16354b}pre{background:white;padding:22px;white-space:pre-wrap;border-radius:12px}h1{color:#147568}</style><h1>CCTV Plan Lab</h1><p>Offline estimates • synthetic inputs • human review required</p><pre>'+body+'</pre><p>TB = 10^12 bytes. Estimates are not a compliance certificate, retention guarantee, network throughput test or PoE compatibility test.</p></html>'


def unique(pairs):
    out={}
    for k,v in pairs:
        if k in out: raise ValueError('Duplicate JSON key')
        out[k]=v
    return out


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('plan',type=Path)
    p.add_argument('--out',type=Path,default=Path('reports')); a=p.parse_args(argv)
    try:
        with a.plan.open('rb') as f: raw=f.read(1048577)
        if len(raw)>1048576: raise ValueError('Input exceeds 1 MiB')
        report=calculate(json.loads(raw.decode('utf-8-sig'),object_pairs_hook=unique))
        a.out.mkdir(parents=True,exist_ok=True)
        (a.out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        (a.out/'report.html').write_text(render(report),encoding='utf-8')
        print(json.dumps(report['summary'])); return 1 if report['findings'] else 0
    except (OSError,ValueError) as exc:
        print('Unable to complete: '+str(exc)); return 2

if __name__=='__main__': raise SystemExit(main())
