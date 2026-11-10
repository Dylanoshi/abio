#!/usr/bin/env python3
"""Local smoke test for authenticated ABIO runner v1."""
import argparse, json, os, time, urllib.request, urllib.error, uuid
p=argparse.ArgumentParser();p.add_argument('--base',default='http://127.0.0.1:8765/v1');p.add_argument('--submit',action='store_true');a=p.parse_args()
token=os.environ.get('ABIO_RUNNER_TOKEN','')
if not token:raise SystemExit('Set ABIO_RUNNER_TOKEN first')
base=a.base.rstrip('/')
def request(method,path,obj=None,authorize=True):
    raw=None if obj is None else json.dumps(obj).encode()
    headers={'Accept':'application/json','Content-Type':'application/json'}
    if authorize:headers['Authorization']='Bearer '+token
    req=urllib.request.Request(base+path,data=raw,headers=headers,method=method)
    try:
        with urllib.request.urlopen(req,timeout=20) as res:return res.status,json.load(res)
    except urllib.error.HTTPError as err:return err.code,json.loads(err.read())
status,_=request('GET','/health',authorize=False)
assert status==401, 'Unauthenticated health must be rejected'
status,resp=request('GET','/health');assert status==200 and resp=={'ok':True}
print('PASS: authenticated health and unauthorized rejection')
if not a.submit:raise SystemExit(0)
payload={'request_id':str(uuid.uuid4()),'campaign_id':'E013_smoke','title':'ABIO API functional smoke test','criteria_version':1,'protocol':{'version':'1','date':'2026-11-10','hypothesis':'Validate pipeline execution, not biological success','seeds':1,'parameters':{'size':[8],'steps':[20],'rule_density':[0.65]},'controls':['sham','target_block','control_block','product_scramble'],'stopping':{'max_steps':20,'max_runs':1,'max_wall_seconds':120},'criterion':'E011 strict audit, no inference of self-maintenance'}}
status,res=request('POST','/batches',payload);assert status==202,res
bid=res['id'];print('QUEUED',bid)
status,dup=request('POST','/batches',payload);assert status==202 and dup['id']==bid
print('PASS: request-ID idempotency')
for _ in range(120):
    time.sleep(1)
    status,res=request('GET','/batches/'+bid)
    assert status==200
    if res['status'] in ('completed','failed'):
        print('FINAL',json.dumps(res,indent=2))
        assert res['status']=='completed',res['errors']
        assert res['report']['schema']=='abio-auto-sweep-v1'
        break
else:raise SystemExit('Timed out waiting for smoke batch; check server logs')
print('PASS: completed batch and final report schema')
