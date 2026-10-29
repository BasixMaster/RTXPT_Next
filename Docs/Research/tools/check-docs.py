from pathlib import Path
from sys import executable
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
b1='7010bb4cda80788eb13cd9ee6143eb2f52a5b6ee'
assert git('rev-parse','rtxpt-1.9-baseline')==baseline
assert git('rev-parse','baseline/rtxpt-1.9')==baseline
expected={'Rtxpt/AdvancedSampleUI.cpp':(1,1),'Rtxpt/RTXDI/RtxdiPass.cpp':(10,10),'Rtxpt/RTXDI/RtxdiResources.cpp':(2,2),'Rtxpt/SampleUI.cpp':(1,1)}
actual={}
for row in git('diff','--ignore-submodules=all','--numstat',baseline,b1,'--','Rtxpt','CMakeLists.txt','Testing','Docs/Design.md').splitlines():
    added,removed,name=row.split('\t');actual[name]=(int(added),int(removed))
assert actual==expected,actual
development_source_changes=git('diff','--ignore-submodules=all','--name-only',b1,'--','Rtxpt','CMakeLists.txt','Testing','Docs/Design.md').splitlines()
development_source_changes+=git('ls-files','--others','--exclude-standard','--','Rtxpt').splitlines()
for ref,runtime in [(baseline,'a14e079c727ed8c4fd3173bd2aea8244c9d9f6d6'),(b1,'f12037fa8e97ebc08e9e3edfd2de528ed1772a4b'),('HEAD','f12037fa8e97ebc08e9e3edfd2de528ed1772a4b')]:
    assert 'a56be4ed65029d2733fd02f00f4027ffd541eda8' in git('ls-tree',ref,'Assets')
    assert runtime in git('ls-tree',ref,'External/Rtxdi')
assert subprocess.check_output(['git','-C',str(P/'External/Rtxdi'),'rev-parse','HEAD'],text=True).strip()=='f12037fa8e97ebc08e9e3edfd2de528ed1772a4b'
assert not subprocess.check_output(['git','-C',str(P/'Assets'),'status','--porcelain'],text=True).strip()
checks.append(dict(name='Immutable baseline, exact four-file legacy B1 API migration and pinned runtime/assets',status='passed',baseline_sha=baseline,b1_sha=b1,host_diff=actual))
scenes=sorted(p.name for p in (P/'Assets').glob('*.scene.json'));assert len(scenes)==11
checks.append(dict(name='Pinned original scene files present',status='passed',scenes=scenes))
versions=json.loads((P/'Benchmarks/versions.json').read_text(encoding='utf-8'))
by_id={x['id']:x for x in versions['versions']}
assert list(by_id)==['B'+str(i) for i in range(11)]
assert versions['numbering_scheme']=='2026-10-29-user-confirmed-B0-B10'
for name in ['B0','B1','B2']:assert by_id[name]['source_sha']==baseline and by_id[name]['rtxdi_sha']=='a14e079c727ed8c4fd3173bd2aea8244c9d9f6d6'
for name in ['B3','B4','B5']:assert by_id[name]['source_sha']==b1 and by_id[name]['rtxdi_sha']=='f12037fa8e97ebc08e9e3edfd2de528ed1772a4b'
for name in ['B6','B7']:assert by_id[name]['source_sha']=='de9fe651903f203327830e7361ac4237e00d508c'
for name in ['B8','B9','B10']:assert by_id[name]['source_sha'] is None and by_id[name]['ref'] is None and by_id[name]['status'].startswith('planned')
flags={'B1':(1,0,0),'B2':(1,1,0),'B3':(0,0,0),'B4':(1,0,0),'B5':(1,1,0),'B6':(0,0,1),'B7':(1,0,1),'B8':(1,1,1),'B9':(1,1,1),'B10':(1,1,1)}
for name,expected_flags in flags.items():assert tuple(by_id[name]['configuration'][k] for k in ['restir_di','restir_gi','restir_pt'])==expected_flags
assert 'original defaults' in by_id['B0']['configuration']
assert (D/'VERSION_MAPPING.md').is_file() and (P/'Benchmarks/legacy/versions-before-2026-10-29.json').is_file()
checks.append(dict(name='Canonical B0–B10 configurations, preserved B0 defaults and legacy mapping',status='passed',development_source_changes=development_source_changes,reason='Registry validation does not prove runtime activation or estimator correctness.'))
coverage=json.loads(subprocess.check_output([executable,str(P/'Benchmarks/tools/coverage_matrix.py'),str(P/'Benchmarks/comparison-matrix.json'),'--repo',str(P)],text=True))
matrix=json.loads((P/'Benchmarks/comparison-matrix.json').read_text())
expected_variants={'B0' if entry['id']=='RTXPT-1.9' else entry['id'] for entry in versions['versions']}
assert set(matrix['variants'])==expected_variants
assert coverage['rows']==len(expected_variants)*len(matrix['required_scenes']) and (D/'ALGORITHM_VARIANTS.md').is_file() and (D/'B3_IMPLEMENTATION.md').is_file()
checks.append(dict(name='Mandatory version/algorithm labels and original-scene coverage rows',status='passed',coverage=coverage))
pilot=P/'Benchmarks/development/2026-10-28-b3-activation'
if pilot.exists():
    inventory=json.loads((pilot/'index.json').read_text())
    for name,expected_hash in inventory['files'].items():
        assert hashlib.sha256((pilot/name).read_bytes()).hexdigest()==expected_hash,name
    captures=list((pilot/'quality').glob('*/capture.json'));timings=list((pilot/'timing').glob('*/run.json'))
    assert len(captures)==60 and len(timings)==12
    assert all(json.loads(p.read_text())['measurement_status']=='captured' for p in captures)
    assert all(json.loads(p.read_text())['status']=='timed_completed' for p in timings)
    checks.append(dict(name='Legacy B3 pilot / canonical B7 limited ablation retained capture/trace identities',status='passed',captures=60,timed_processes=12,hashed_files=len(inventory['files']),limits='Retained evidence identity/completeness only; not a full PT++ or original-scene validation proof.'))
canonical=P/'Benchmarks/development/2026-10-29-canonical-native-di'
if canonical.exists():
    index=json.loads((canonical/'index.json').read_text())
    for name,digest in index['files'].items():assert hashlib.sha256((canonical/name).read_bytes()).hexdigest()==digest,name
    captures=list((canonical/'quality').glob('*/capture.json'));assert len(captures)==12
    for path in captures:
        capture=json.loads(path.read_text());assert capture['measurement_status']=='captured'
        assert capture['effective_canonical_experiment']['flags']==dict(di=1,gi=0,pt=0) and capture['artifact_identity_after_capture']['validated']
    exclusions=json.loads((canonical/'excluded-timing.json').read_text());assert exclusions['accepted_timing_runs']==0 and len(exclusions['attempts'])==2
    assert all(x['restoration_verified'] for x in exclusions['attempts'])
    checks.append(dict(name='Frozen native-DI quality identities and initial excluded timing attempts',status='passed',captures=12,hashed_files=len(index['files'])))
for dataset,expected_runs in [('2026-10-29-canonical-native-di-timing',12),('2026-10-29-registered-room',12)]:
    base=P/'Benchmarks/development'/dataset
    index=json.loads((base/'index.json').read_text())
    for name,digest in index['files'].items():assert hashlib.sha256((base/name).read_bytes()).hexdigest()==digest,name
    runs=list((base/'timing').glob('*/run.json'));assert len(runs)==expected_runs
    for path in runs:
        run=json.loads(path.read_text());rest=json.loads((path.parent/'restoration.json').read_text())
        assert run['status']=='timed_completed' and rest['restoration_verified'] and run['image_write_count']==0 and not run['reported_trace_loss']
        assert run['artifact_identity_after_capture']['validated'] and run['cap_control']['observed_sync_interval']==0
        variant=run['canonical_experiment']['variant'];expected_flags=dict(di=int(variant in ['B1','B4','B7']),gi=0,pt=int(variant in ['B6','B7']))
        assert run['effective_canonical_experiment']['flags']==expected_flags
    checks.append(dict(name=dataset+' retained hashes, modes, traces and restoration',status='passed',timed_processes=expected_runs,hashed_files=len(index['files'])))
room=P/'Benchmarks/development/2026-10-29-registered-room'
assert len(list((room/'quality').glob('*/capture.json')))==30 and len(list((room/'references').glob('*/capture.json')))==3
for variant in ['B6','B7']:
    activation=json.loads((room/'activation'/variant/'reservoir-summary.json').read_text())['statistics']
    assert activation['final_index']['midpath_reconnection_valid']>0 and activation['final_index']['m_greater_than_one']>0
    assert all(x['nonfinite_m']==x['nonfinite_weight_valid']==x['nonfinite_target_valid']==0 for x in activation.values())
oracle=json.loads((P/'Benchmarks/development/2026-10-29-b8-partition-oracles/receipt.json').read_text())
for name,digest in oracle['source_hashes'].items():assert hashlib.sha256((P/'Benchmarks/tools'/name).read_bytes()).hexdigest()==digest
assert oracle['partition_cases']==56
checks.append(dict(name='Room quality/reference counts, finite active PT diagnostic and exact CPU prerequisite source identity',status='passed',limits='No B8 GPU implementation follows from these CPU checks.'))
result=next(x for x in versions['results'] if x['id']=='2026-10-28-b1')
assert result['status']=='measured' and (P/result['report']).is_file()
evidence=P/result['path'];assert evidence.is_dir()
for scene in ['convergence','kitchen']:
    for version in ['B0','B1']:
        group=json.loads((evidence/'analysis'/scene/(version+'.json')).read_text(encoding='utf-8'))
        assert group['process_runs']==5 and len(group['runs'])==5
        for i in range(1,6):
            run=evidence/'timing'/f'{scene}-{version}-r{i}'
            manifest=json.loads((run/'manifest.json').read_text(encoding='utf-8'))
            assert manifest['status']=='timed_completed' and manifest['image_write_count']==0
            assert hashlib.sha256((run/'presentmon.csv').read_bytes()).hexdigest()==manifest['presentmon_csv_sha256']
    comparison=json.loads((evidence/'analysis'/scene/'comparison.json').read_text(encoding='utf-8'))
    assert comparison['comparisons']['GPUBusy']['baseline_ms']>0
for name in ['hardware-build.json','migration-audit.json','checksums.json','quality/summary.json']:
    assert (evidence/name).is_file(),name
for name,digest in json.loads((evidence/'checksums.json').read_text()).items():
    assert hashlib.sha256((evidence/name).read_bytes()).hexdigest()==digest,name
quality=json.loads((evidence/'quality/summary.json').read_text())
for scene in ['convergence','kitchen']:
    assert quality[scene]['reference_spp']==4096
    for version in ['B0','B1']:
        assert len(quality[scene]['versions'][version]['samples'])==5
        for i in range(1,6):
            q=json.loads((evidence/'quality'/f'{scene}-{version}-r{i}.json').read_text())
            assert q['flip']['status']=='measured' and q['flip']['evaluator_version']=='1.7'
            capture=evidence/'quality-captures'/f'{scene}-{version}-r{i}'/q['test']['file']
            ref=evidence/'quality-captures'/f'{scene}-reference-4096'/q['reference']['file']
            assert hashlib.sha256(capture.read_bytes()).hexdigest()==q['test']['sha256']
            assert hashlib.sha256(ref.read_bytes()).hexdigest()==q['reference']['sha256']
checks.append(dict(name='Legacy original-scene registry:20 accepted process runs and preserved CSV hashes',status='passed',evidence=result['path']))
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
checks.append(dict(name='Build/GPU and display-quality evidence recorded',status='evidence_present',reason='This checker validates retained identity/completeness; it does not rebuild binaries, rerun GPU measurements or prove estimator correctness. See the native-DI/registered-room reports, legacy reports and result manifests.'))
receipt=dict(updated_on='2026-10-29',project='Basix Pathtracing',product='RTXPT Next',repository='BasixMaster/RTXPT_Next',checks=checks,passed=not errors,limits=['Source audit is not algorithm correctness proof.','One GPU. Legacy migration:two original scenes/five process pairs. New native DI:two original scenes/three processes per configuration; registered room:four configurations/three timing processes.','PresentMon GPU active duration is not exclusive DI/GI or complete critical-path latency.','Native controls have display metrics; modern room captures include raw HDR/HDR-FLIP and explicit seeds. Motion, reconstruction and equal-time/error convergence remain pending.','Canonical B1/B4 native controls and B6/B7 registered-room measurements are scoped evidence. Original Convergence/Kitchen PT gates remain. Legacy limited PT++ maps to B7 ablations. B8 GPU sharing and B9/B10 remain planned.'])
(D/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
if errors:raise SystemExit(json.dumps(errors))
print(json.dumps(dict(passed=True,checks=len(checks),scenes=len(scenes),math_expressions=page.count('<math '))))
