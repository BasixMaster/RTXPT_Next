from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
from collections import Counter
import json,sqlite3,subprocess,hashlib,sys,xml.etree.ElementTree as ET
D=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1];P=D.parents[1]
class Page(HTMLParser):
    def __init__(self):super().__init__();self.ids=[];self.links=[]
    def handle_starttag(self,t,a):
        a=dict(a)
        if 'id'in a:self.ids.append(a['id'])
        if t in ['a','link','script','img']:
            value=a.get('href') or a.get('src')
            if value:self.links.append(value)
def git(*a):return subprocess.check_output(['git','-C',str(P),*a],text=True).strip()
checks=[];errors=[]
for p in D.rglob('*.html'):
    page=Page();page.feed(p.read_text(encoding='utf-8'))
    duplicate=[k for k,v in Counter(page.ids).items() if v>1]
    if duplicate:errors.append(str(p.relative_to(D))+': duplicate IDs '+str(duplicate))
    for link in page.links:
        u=urlsplit(link)
        if u.scheme or u.netloc:continue
        target=p if not u.path else p.parent/unquote(u.path)
        if not target.exists():errors.append(str(p.relative_to(D))+': missing '+link);continue
        if u.fragment and target.suffix=='.html':
            other=page
            if target!=p:other=Page();other.feed(target.read_text(encoding='utf-8'))
            if unquote(u.fragment) not in other.ids:errors.append(str(p.relative_to(D))+': bad fragment '+link)
checks.append(dict(name='HTML unique anchors and local links',status='passed' if not errors else 'failed',errors=errors))
catalog=json.loads((D/'paper-catalog.json').read_text(encoding='utf-8'))
assert [x['rank'] for x in catalog]==list(range(1,21))
checks.append(dict(name='Newest12/wider20 catalog',status='passed',papers=20))
baseline='303b408ab81790a5051abd7573830b7a4112eb8e'
assert git('rev-parse','rtxpt-1.9-baseline')==baseline
assert git('rev-parse','baseline/rtxpt-1.9')==baseline
render_diff=git('diff','--ignore-submodules=all','--name-only',baseline,'--','Rtxpt','CMakeLists.txt','Testing','Docs/Design.md')
assert not render_diff,render_diff
for item,sha in [('Assets','a56be4ed65029d2733fd02f00f4027ffd541eda8'),('External/Rtxdi','a14e079c727ed8c4fd3173bd2aea8244c9d9f6d6')]:
    assert sha in git('ls-tree','HEAD',item)
checks.append(dict(name='Baseline refs, renderer/build/test source and original dependency/asset pins',status='passed',source_sha=baseline))
scenes=sorted(p.name for p in (P/'Assets').glob('*.scene.json'));assert len(scenes)==11
checks.append(dict(name='Pinned original scene files present',status='passed',scenes=scenes))
versions=json.loads((P/'Benchmarks/versions.json').read_text(encoding='utf-8'));assert versions['results']==[]
assert all(x['status']=='planned' for x in versions['versions'][1:])
checks.append(dict(name='B1/B2 planned state and no fabricated results',status='passed'))
for p in (D/'assets').glob('*.svg'):ET.parse(p)
page=(D/'index.html').read_text(encoding='utf-8');assert page.count('<math ')>=40
assert '<h1>RTXPT Next</h1>' in page and 'Basix Pathtracing' in page
assert 'The repository remains named RTXDI_Next.' not in page
checks.append(dict(name='Brand assets valid SVG, final titles and native MathML',status='passed',math_expressions=page.count('<math ')))
data=json.loads((D/'library.json').read_text(encoding='utf-8'))
with sqlite3.connect(D/'evidence/index.sqlite') as db:
    n=db.execute("SELECT count(*) FROM records WHERE records MATCH 'SMAPE'").fetchone()[0]
assert n>=2
checks.append(dict(name='Structured evidence schema separately validated; SQLite metric search',status='passed',smape_matches=n,sources=len(data['sources']),findings=len(data['findings'])))
assert not list(D.rglob('*.pdf'))
checks.append(dict(name='No full-paper PDFs exported',status='passed'))
checks.extend([dict(name='Renderer/shader build and GPU benchmarks',status='not_run',reason='Baseline/roadmap stage; no renderer changes. Available CMake3.31.5 is below upstream4.1 requirement; other build dependencies not initialized.'),dict(name='Image quality evaluator implementation / captured results',status='planned',reason='Paper-specific specification and capture gaps documented; no metric code or GPU results claimed.')])
receipt=dict(updated_on='2026-10-28',project='Basix Pathtracing',product='RTXPT Next',repository='BasixMaster/RTXPT_Next',checks=checks,passed=not errors,limits=['Static source audit, not algorithm correctness proof.','Original scene files fetched but not rendered.','Renderer and B1/B2 benchmarks remain future stages.'])
(D/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
if errors:raise SystemExit(json.dumps(errors))
print(json.dumps(dict(passed=True,checks=len(checks),scenes=len(scenes),math_expressions=page.count('<math '))))
