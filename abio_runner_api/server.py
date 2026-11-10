#!/usr/bin/env python3
"""ABIO runner API v1. Run behind TLS reverse proxy, never directly on public internet."""
import argparse, datetime, hashlib, hmac, itertools, json, os, re, resource, shutil, sqlite3, subprocess, sys, threading, time, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ID_RE=re.compile(r'^[A-Za-z0-9_-]{1,100}$')
RANGES={'rule_density':(0.01,1.0),'catalysis_rate':(0.001,0.5), 'decay':(0.0,0.2), 'supply':(0.0,0.5), 'initial_density':(0.01,0.8), 'bond_form':(0.0,1.0),'bond_break':(0.0,1.0),'background_rate':(0.0,0.2)}
INT_PARAMS={'size':(8,64),'steps':(20,3000)}
MAX_SEEDS=20; MAX_REGIMES=12; MAX_TOTAL=120; MAX_JSON=32768
ALLOWED_CONTROLS={'sham','target_block','control_block','product_scramble'}

class BadRequest(Exception): pass

def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def clean_id(s, label):
    if not isinstance(s,str) or not ID_RE.fullmatch(s):raise BadRequest(f'{label} must be 1-100 letters, digits, _ or -')
    return s

def validate(payload):
    if not isinstance(payload,dict):raise BadRequest('JSON object required')
    try: uuid.UUID(payload['request_id'])
    except (KeyError,TypeError,ValueError):raise BadRequest('request_id must be a UUID')
    campaign=clean_id(payload.get('campaign_id'),'campaign_id')
    if not isinstance(payload.get('title'),str) or not 1<=len(payload['title'])<=200:raise BadRequest('title must be 1-200 characters')
    if type(payload.get('criteria_version')) is not int or payload['criteria_version']<1:raise BadRequest('positive criteria_version required')
    p=payload.get('protocol')
    if not isinstance(p,dict):raise BadRequest('protocol object required')
    for key in ('version','date','hypothesis','controls','stopping','criterion'):
        if key not in p: raise BadRequest(f'protocol.{key} required')
    if not isinstance(p['hypothesis'],str) or not p['hypothesis'].strip() or len(p['hypothesis'])>2000:raise BadRequest('invalid hypothesis')
    if not isinstance(p['version'],(str,int)) or not str(p['version']).strip():raise BadRequest('invalid protocol.version')
    if not isinstance(p['date'],str) or len(p['date'])>50: raise BadRequest('invalid protocol.date')
    controls=p['controls']
    if not isinstance(controls,list) or not controls or any(not isinstance(x,str) or x not in ALLOWED_CONTROLS for x in controls):raise BadRequest('unsupported protocol.controls')
    if 'sham' not in controls:raise BadRequest('sham control required')
    if not isinstance(p['criterion'],(str,dict)) or not p['criterion']:raise BadRequest('protocol.criterion required')
    stopping=p['stopping']
    if not isinstance(stopping,dict) or set(stopping)-{'max_steps','max_runs','max_wall_seconds'}:raise BadRequest('stopping must specify enforceable max_steps/max_runs/max_wall_seconds')
    if 'max_steps' not in stopping or 'max_runs' not in stopping:raise BadRequest('stopping.max_steps and max_runs required')
    for k,limit in [('max_steps',3000),('max_runs',120),('max_wall_seconds',14400)]:
        if k in stopping and (type(stopping[k]) is not int or not 1<=stopping[k]<=limit):raise BadRequest(f'invalid stopping.{k}')
    seeds=p.get('seeds')
    if type(seeds) is not int or not 1<=seeds<=MAX_SEEDS:raise BadRequest(f'seeds must be 1..{MAX_SEEDS}')
    values=p.get('parameters')
    if not isinstance(values,dict):raise BadRequest('protocol.parameters must be map')
    params={}
    for key,arr in values.items():
        if key not in RANGES and key not in INT_PARAMS:raise BadRequest(f'unsupported parameter: {key}')
        if not isinstance(arr,list) or not 1<=len(arr)<=MAX_REGIMES:raise BadRequest(f'{key} must have 1..{MAX_REGIMES} numeric entries')
        lo,hi=(RANGES|INT_PARAMS)[key]
        from math import isfinite
        if any(type(x) not in (float,int) or not isfinite(x) or x<lo or x>hi for x in arr):raise BadRequest(f'{key} outside [{lo},{hi}] or not finite')
        if key in INT_PARAMS and any(type(x) is not int for x in arr):raise BadRequest(f'{key} requires integer values')
        params[key]=arr
    if 'steps' not in params:params['steps']=[min(600,stopping['max_steps'])]
    if 'size' not in params:params['size']=[24]
    if any(x>stopping['max_steps'] for x in params['steps']):raise BadRequest('steps exceed stopping.max_steps')
    regimes=1
    for v in params.values():regimes*=len(v)
    if regimes>MAX_REGIMES:raise BadRequest(f'parameter grid >{MAX_REGIMES} regimes')
    if seeds*regimes>MAX_TOTAL or seeds*regimes>stopping['max_runs']:raise BadRequest('requested runs exceed max_runs or server budget')
    normalized=dict(payload)
    normalized['protocol']=dict(p,parameters=params)
    return normalized,regimes,seeds

class Backend:
    def __init__(self,db_path,root):
        self.db_path=Path(db_path);self.db_path.parent.mkdir(parents=True,exist_ok=True)
        self.root=Path(root).expanduser().resolve();self.out=self.root/'track2/rco002/remote_batches';self.out.mkdir(parents=True,exist_ok=True)
        self.sim=self.root/'track2/rco002/rco002_experiment011/sim.py';self.analyzer=self.root/'track2/rco002/rco002_experiment012/analyze.py'
        if not self.sim.is_file() or not self.analyzer.is_file():raise RuntimeError('Install E011 sim.py and E012 analyze.py in ~/abio first')
        self.lock=threading.RLock();self.cv=threading.Condition(self.lock);self.shutdown=threading.Event()
        with self.conn() as db:
            db.execute('CREATE TABLE IF NOT EXISTS batches (id TEXT PRIMARY KEY, request_id TEXT UNIQUE NOT NULL, payload_hash TEXT NOT NULL, payload TEXT NOT NULL, status TEXT NOT NULL, completed INTEGER NOT NULL, total INTEGER NOT NULL, cpu_seconds REAL NOT NULL DEFAULT 0, errors TEXT NOT NULL DEFAULT "[]", summary TEXT NOT NULL DEFAULT "[]", created TEXT NOT NULL, updated TEXT NOT NULL)')
            db.execute("UPDATE batches SET status='queued' WHERE status IN ('running','pausing')")
        self.worker=threading.Thread(target=self.loop,daemon=True);self.worker.start()
    def conn(self):
        db=sqlite3.connect(self.db_path,timeout=30)
        db.row_factory=sqlite3.Row
        db.execute('PRAGMA journal_mode=WAL')
        return db
    def get(self,bid):
        with self.lock,self.conn() as db:return db.execute('SELECT * FROM batches WHERE id=?',(bid,)).fetchone()
    def create(self,payload):
        clean,regimes,seeds=validate(payload)
        raw=json.dumps(clean,sort_keys=True,separators=(',',':'));digest=hashlib.sha256(raw.encode()).hexdigest();rid=clean['request_id']
        with self.lock,self.conn() as db:
            prior=db.execute('SELECT * FROM batches WHERE request_id=?',(rid,)).fetchone()
            if prior:
                if prior['payload_hash']!=digest:raise BadRequest('request_id already used with different payload')
                return self.snapshot(prior)
            bid='batch_'+uuid.uuid4().hex[:20];stamp=utc()
            db.execute('INSERT INTO batches (id,request_id,payload_hash,payload,status,completed,total,created,updated) VALUES (?,?,?,?,?,?,?,?,?)',(bid,rid,digest,raw,'queued',0,regimes*seeds,stamp,stamp))
        with self.cv:self.cv.notify_all()
        return self.get_snapshot(bid)
    def snapshot(self,row):
        p=json.loads(row['payload']);seeds=p['protocol']['seeds'];entries=json.loads(row['summary']);total=row['total'];runs=[]
        done={x['regime'] for x in entries};params=p['protocol']['parameters'];keys=sorted(params)
        combos=list(itertools.product(*(params[k] for k in keys)))
        for i,vals in enumerate(combos):
            label='regime_'+str(i).zfill(2);status='completed' if label in done else 'queued'
            if status=='queued' and row['status'] in ('running','pausing') and i==len(entries):status='running'
            if row['status']=='failed' and status=='queued':status='failed'
            for seed in range(seeds):runs.append({'id':f'{label}_seed{seed}','seed':seed,'condition':label,'status':status})
        ret={'id':row['id'],'status':row['status'],'completed':row['completed'],'total':total,'resources':{'cpu_seconds':round(row['cpu_seconds'],3)},'errors':json.loads(row['errors']),'runs':runs}
        if row['status']=='completed':ret['report']={'schema':'abio-auto-sweep-v1','batch':row['id'],'summary':entries,'scientific_caveat':'Rule cycles and catalytic ancestry do not establish organizational self-maintenance. The selected-lineage E011 criterion can miss spatial closure elsewhere.'}
        return ret
    def get_snapshot(self,bid):
        row=self.get(bid)
        return self.snapshot(row) if row else None
    def status(self,bid,action):
        with self.lock,self.conn() as db:
            row=db.execute('SELECT * FROM batches WHERE id=?',(bid,)).fetchone()
            if not row:return None
            state=row['status']
            if action=='pause' and state in ('running','queued'):
                state='pausing' if state=='running' else 'paused'
            elif action=='resume' and state in ('paused','pausing'):state='queued'
            if state!=row['status']:
                db.execute('UPDATE batches SET status=?,updated=? WHERE id=?',(state,utc(),bid))
        with self.cv:self.cv.notify_all()
        return self.get_snapshot(bid)
    def update(self,bid,**kwargs):
        with self.lock,self.conn() as db:
            parts=','.join(f'{k}=?' for k in kwargs)+',updated=?'
            db.execute(f'UPDATE batches SET {parts} WHERE id=?',(*kwargs.values(),utc(),bid))
    def run_command(self,command,log,timeout):
        start=resource.getrusage(resource.RUSAGE_CHILDREN)
        with open(log,'w') as output:
            subprocess.run(command,cwd=self.root,stdout=output,stderr=subprocess.STDOUT,check=True,timeout=timeout)
        end=resource.getrusage(resource.RUSAGE_CHILDREN)
        return max(0,end.ru_utime+end.ru_stime-start.ru_utime-start.ru_stime)
    def loop(self):
        while not self.shutdown.is_set():
            with self.lock,self.conn() as db:
                job=db.execute("SELECT id FROM batches WHERE status='queued' ORDER BY created ASC LIMIT 1").fetchone()
            if not job:
                with self.cv:self.cv.wait(timeout=1)
                continue
            bid=job['id']
            try:self.execute(bid)
            except Exception as exc:
                row=self.get(bid)
                errors=json.loads(row['errors']) if row else []
                errors.append(str(exc)[:500]);self.update(bid,status='failed',errors=json.dumps(errors))
    def execute(self,bid):
        row=self.get(bid)
        if not row or row['status']!='queued':return
        p=json.loads(row['payload']);prot=p['protocol'];parameters=prot['parameters'];keys=sorted(parameters)
        combinations=list(itertools.product(*(parameters[k] for k in keys)))
        seeds=prot['seeds'];base=self.out/bid;base.mkdir(parents=True,exist_ok=True)
        deadline=datetime.datetime.fromisoformat(row['created']).timestamp()+prot['stopping'].get('max_wall_seconds',14400)
        for i,combo in enumerate(combinations):
            row=self.get(bid)
            if row['status']=='pausing':self.update(bid,status='paused');return
            if row['status'] not in ('queued','running'):return
            if time.time()>=deadline:raise RuntimeError('Campaign max_wall_seconds exceeded')
            self.update(bid,status='running')
            name=f'regime_{i:02d}'
            if any(x['regime']==name for x in json.loads(row['summary'])):continue
            opts=dict(zip(keys,combo));folder=base/name
            if folder.exists():shutil.rmtree(folder)
            folder.mkdir();source=folder/'e011';analysis=folder/'e012'
            cmd=[sys.executable,str(self.sim),'--seeds',str(seeds),'--out',str(source)]
            for key,value in opts.items():cmd.extend(['--'+key.replace('_','-'),str(value)])
            audit=[sys.executable,str(self.analyzer),'--e011',str(source),'--out',str(analysis)]
            (folder/'provenance.json').write_text(json.dumps({'parameters':opts,'seeds':seeds,'sim_sha256':hashlib.sha256(self.sim.read_bytes()).hexdigest(),'analyzer_sha256':hashlib.sha256(self.analyzer.read_bytes()).hexdigest(),'commands':[cmd,audit]},indent=2))
            cpu=self.run_command(cmd,folder/'simulation.log',max(1,deadline-time.time()))
            # E011 may omit events.csv when a tiny run produces no events.
            # E012 expects the file even when there is nothing to analyze.
            if not (source/'events.csv').exists():
                (source/'events.csv').write_text('seed,mode,step,event,particle_id,particle_type,catalyst_a,catalyst_b\n')
            if time.time()>=deadline:raise RuntimeError('Campaign max_wall_seconds exceeded before analysis')
            cpu+=self.run_command(audit,folder/'analysis.log',max(1,min(deadline-time.time(),1200)))
            result=json.loads((analysis/'report.json').read_text())
            entry={'regime':name,'rule_density':opts.get('rule_density',0.65),'catalysis_rate':opts.get('catalysis_rate',0.14),'cycle_groups':result['structural_cycle_groups'],'input_covered':result['input_covered_cycle_groups'],'max_ancestry':result['maximal_realized_catalytic_ancestry'],'strict_candidate_steps':result['strict_candidate_steps_total'],'report_path':str(analysis/'report.json')}
            row=self.get(bid);summary=json.loads(row['summary']);summary.append(entry)
            self.update(bid,summary=json.dumps(summary),completed=len(summary)*seeds,cpu_seconds=row['cpu_seconds']+cpu)
        row=self.get(bid)
        if row['status']=='pausing':self.update(bid,status='paused');return
        if row['status'] in ('queued','running'):
            report=self.snapshot(row)
            # Save report with final schema directly (not intermediary status snapshot)
            obj={'schema':'abio-auto-sweep-v1','batch':bid,'summary':json.loads(row['summary']),'scientific_caveat':'Potential rule cycles and ancestry are not demonstrated self-maintenance.'}
            (base/'lab_import.json').write_text(json.dumps(obj,indent=2))
            self.update(bid,status='completed')

class Handler(BaseHTTPRequestHandler):
    backend=None;token=None
    def log_message(self,fmt,*args):pass # Don't log Authorization or request contents.
    def respond(self,status,obj):
        raw=json.dumps(obj,separators=(',',':'),allow_nan=False).encode()
        if len(raw)>2_000_000:return self.respond(500,{'error':'response too large'})
        self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)
    def authorized(self):
        header=self.headers.get('Authorization','')
        if not hmac.compare_digest(header,'Bearer '+self.token):self.respond(401,{'error':'unauthorized'});return False
        return True
    def do_GET(self):
        if not self.authorized():return
        path=urlsplit(self.path).path.rstrip('/')
        if path in ('/health','/v1/health'):return self.respond(200,{'ok':True})
        m=re.fullmatch(r'/(?:v1/)?batches/([A-Za-z0-9_-]{1,100})',path)
        if m:
            item=self.backend.get_snapshot(m.group(1))
            return self.respond(200,item) if item else self.respond(404,{'error':'batch not found'})
        self.respond(404,{'error':'not found'})
    def do_POST(self):
        if not self.authorized():return
        path=urlsplit(self.path).path.rstrip('/')
        length=self.headers.get('Content-Length','')
        if not length.isdigit() or int(length)>MAX_JSON:return self.respond(413,{'error':'request body limit exceeded'})
        try:payload=json.loads(self.rfile.read(int(length)))
        except (ValueError,UnicodeError):return self.respond(400,{'error':'invalid JSON'})
        if path in ('/batches','/v1/batches'):
            try:return self.respond(202,self.backend.create(payload))
            except BadRequest as exc:return self.respond(400,{'error':str(exc)})
            except sqlite3.IntegrityError:return self.respond(409,{'error':'duplicate request conflict'})
        m=re.fullmatch(r'/(?:v1/)?batches/([A-Za-z0-9_-]{1,100})/(pause|resume)',path)
        if m:
            if payload!={}:return self.respond(400,{'error':'body must be {}'})
            result=self.backend.status(m.group(1),m.group(2))
            return self.respond(200,result) if result else self.respond(404,{'error':'batch not found'})
        self.respond(404,{'error':'not found'})

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',default=str(Path.home()/'abio'))
    p.add_argument('--host',default='127.0.0.1')
    p.add_argument('--port',type=int,default=8765)
    a=p.parse_args()
    token=os.getenv('ABIO_RUNNER_TOKEN','')
    if len(token)<32:raise SystemExit('Set ABIO_RUNNER_TOKEN to a random secret of at least 32 characters')
    if a.host not in ('127.0.0.1','::1','localhost'):raise SystemExit('Bind only to loopback; use a TLS-authenticated reverse proxy or private tunnel')
    root=Path(a.root).expanduser().resolve()
    Handler.backend=Backend(root/'.abio_runner_api'/'batches.sqlite3',root)
    Handler.token=token
    server=ThreadingHTTPServer((a.host,a.port),Handler)
    print(f'ABIO runner listening on http://{a.host}:{a.port} (loopback only); HTTPS tunnel required for Sites',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=='__main__':main()
