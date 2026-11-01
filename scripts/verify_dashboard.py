"""Reproduce saved and previously cached custom comparisons with networking blocked."""
import hashlib,json,socket,sys,os
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
def deny(*args,**kwargs):raise RuntimeError('Network blocked for verification')
socket.socket.connect=deny;socket.getaddrinfo=deny;socket.create_connection=deny
os.environ.pop('GEMINI_API_KEY',None)
from app import create_app
from portfolio import analyse
client=create_app({'TESTING':True}).test_client()
requests={
 'saved':{'source':'saved','current':[{'symbol':'RELIANCE','weight':40},{'symbol':'HDFCBANK','weight':30},{'symbol':'INFY','weight':30}], 'alternative':[{'symbol':'RELIANCE','weight':20},{'symbol':'HDFCBANK','weight':40},{'symbol':'INFY','weight':40}]},
 'custom':{'source':'historical','start':'2021-01-01','end':'2023-12-31','current':[{'symbol':'TCS','weight':60},{'symbol':'INFY','weight':40}],'alternative':[{'symbol':'TCS','weight':40},{'symbol':'INFY','weight':60}]}}
preview=client.get('/home-preview')
assert preview.status_code==200,preview.json
assert client.get('/').status_code==200
results={}
for name,payload in requests.items():
 response=client.post('/dashboard/analyse',json=payload)
 assert response.status_code==200,response.json
 data=response.json
 results[name]={'request':payload, 'period':data['period'],'metrics':{n:p['metrics'] for n,p in data['portfolios'].items()}, 'coverage':data['coverage'],'excluded_dates':data['excluded_dates'],'provenance':data['dataset']}
 if name=='saved':
  assert preview.json['portfolios']==data['portfolios']
  base=analyse((ROOT/'samples/portfolio.csv').read_bytes(),ROOT/'data/local')
  assert data['portfolios']['current']['metrics']==base['metrics']
  results[name]['foundation_metrics_unchanged']=True
  results[name]['gemini_status']=client.post('/dashboard/interpret',json={'analysis_id':data['analysis_id']}).json['status']
paths=['app.py','portfolio.py','market.py','dashboard.py','interpretation.py','static/dashboard.js','static/home.js','static/home.css','templates/home.html','static/dashboard_state.js','static/dashboard.css','templates/dashboard.html','requirements-ai.txt','requirements-lock.txt']
evidence={'verified_at_utc':datetime.now(timezone.utc).isoformat(),'network':'Python DNS/TCP blocked before app import','source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},'results':results}
(ROOT/'docs/evidence/dashboard-verification.json').write_text(json.dumps(evidence,indent=2)+'\n')
print(json.dumps({n:r['metrics'] for n,r in results.items()},indent=2))
