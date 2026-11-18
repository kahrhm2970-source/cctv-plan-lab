import copy,json,tempfile,unittest
from pathlib import Path
import cctv_plan as c
BASE=json.loads(Path('examples/plan.json').read_text())
class Tests(unittest.TestCase):
 def test_example(self):
  r=c.calculate(BASE); self.assertEqual(r['summary']['planned_storage_tb'],12.4416)
  self.assertEqual(r['summary']['raw_video_tb'],10.368)
  self.assertEqual(r['summary']['stream_bitrate_sum_mbps'],32)
  self.assertEqual(r['switches'][0]['planned_pse_w'],144)
  self.assertEqual({f['code'] for f in r['findings']},{'STORAGE_SHORTFALL','POE_BUDGET_SHORTFALL'})
 def test_corrected(self):
  x=copy.deepcopy(BASE); x['usable_storage_tb']=16; x['switches'][0]['budget_w']=180
  self.assertEqual(c.calculate(x)['findings'],[])
 def test_single_camera_formula(self):
  x=copy.deepcopy(BASE); x['camera_groups'][0]['count']=1; x['camera_groups'][0]['bitrate_mbps']=1
  self.assertEqual(c.calculate(x)['summary']['daily_video_tb'],0.0108)
 def test_hours(self):
  x=copy.deepcopy(BASE); x['camera_groups'][0]['recording_hours_per_day']=12
  self.assertEqual(c.calculate(x)['summary']['daily_video_tb'],c.calculate(BASE)['summary']['daily_video_tb']/2)
 def test_port_count(self):
  x=copy.deepcopy(BASE); x['switches'][0]['ports']=7
  self.assertIn('PORT_COUNT_SHORTFALL',{f['code'] for f in c.calculate(x)['findings']})
 def test_port_power(self):
  x=copy.deepcopy(BASE); x['switches'][0]['port_limit_w']=14
  self.assertIn('PORT_POWER_LIMIT',{f['code'] for f in c.calculate(x)['findings']})
 def test_boundary(self):
  x=copy.deepcopy(BASE); x['usable_storage_tb']=12.4416; x['switches'][0]['budget_w']=144
  self.assertEqual(c.calculate(x)['findings'],[])
 def test_unknown_switch(self):
  x=copy.deepcopy(BASE); x['camera_groups'][0]['switch_id']='SW-2'
  with self.assertRaises(ValueError): c.calculate(x)
 def test_duplicate_id(self):
  x=copy.deepcopy(BASE); x['camera_groups']*=2
  with self.assertRaises(ValueError): c.calculate(x)
 def test_invalid_numbers(self):
  for v in (True,0,-1,float('nan'),float('inf'),'4',None):
   x=copy.deepcopy(BASE); x['camera_groups'][0]['bitrate_mbps']=v
   with self.subTest(v=v),self.assertRaises(ValueError): c.calculate(x)
 def test_extra_field(self):
  x=copy.deepcopy(BASE); x['password']='private'
  with self.assertRaises(ValueError): c.calculate(x)
 def test_zero_storage(self):
  x=copy.deepcopy(BASE); x['usable_storage_tb']=0
  self.assertEqual(c.calculate(x)['summary']['planning_retention_days'],0)
 def test_multiple_switches(self):
  x=copy.deepcopy(BASE); x['switches'].append(dict(id='SW-2',ports=4,budget_w=100,port_limit_w=30))
  g=copy.deepcopy(x['camera_groups'][0]); g.update(id='GROUP-2',switch_id='SW-2',count=2); x['camera_groups'].append(g)
  self.assertEqual(c.calculate(x)['switches'][1]['pse_load_w'],30)
 def test_duplicate_json(self):
  with self.assertRaises(ValueError): json.loads('{"a":1,"a":2}',object_pairs_hook=c.unique)
 def test_cli(self):
  with tempfile.TemporaryDirectory() as t:
   self.assertEqual(c.main(['examples/plan.json','--out',t]),1)
   self.assertEqual(json.loads((Path(t)/'report.json').read_text())['summary']['camera_count'],8)
 def test_html(self): self.assertNotIn('<script>',c.render({'x':'<script>'}))
