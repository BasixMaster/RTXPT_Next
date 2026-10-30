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
expected_ids=['B'+str(i) for i in range(11)]+['B10.75','B10.50','B10.25']+['B'+str(i) for i in range(11,17)]
assert list(by_id)==expected_ids
for key,rate,mode in [('B10.75',.75,1),('B10.50',.5,2),('B10.25',.25,3)]:
    assert by_id[key]['average_spp']==rate and by_id[key]['native_subsampling_mode']==mode and by_id[key]['status']=='planned'
assert versions['numbering_scheme']=='2026-10-29-user-confirmed-B0-B10'
for name in ['B0','B1','B2']:assert by_id[name]['source_sha']==baseline and by_id[name]['rtxdi_sha']=='a14e079c727ed8c4fd3173bd2aea8244c9d9f6d6'
for name in ['B3','B4','B5']:assert by_id[name]['source_sha']==b1 and by_id[name]['rtxdi_sha']=='f12037fa8e97ebc08e9e3edfd2de528ed1772a4b'
for name in ['B6','B7']:assert by_id[name]['source_sha']=='de9fe651903f203327830e7361ac4237e00d508c'
for name in ['B8','B9','B10']:
    assert by_id[name]['source_sha'] is None and by_id[name]['ref'] is None
    assert by_id[name]['status'] in ['development_partition_gi_initial_only','development_limited_ptpp_gi_initial_only','development_gaussian_pairing_pilot','development_nvidia_gi_approximation','development_limited_ptpp_on_b8']
    assert (P/by_id[name]['development_evidence']/'summary.json').is_file()
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
native_completion=P/'Benchmarks/development/2026-10-29-native-matrix-completion'
native_index=json.loads((native_completion/'index.json').read_text())
assert native_index['counts']=={'quality_captures':27,'timed_runs':27}
for relative,digest in native_index['files'].items():assert hashlib.sha256((native_completion/relative).read_bytes()).hexdigest()==digest
for folder in (native_completion/'timing').iterdir():
    result=json.loads((folder/'run.json').read_text());restoration=json.loads((folder/'restoration.json').read_text())
    assert result['status']=='timed_completed' and result['artifact_identity_after_capture']['validated'] and restoration['restoration_verified']
    assert result['image_write_count']==0 and not result['reported_trace_loss']
checks.append(dict(name='Native B2/B3/B5 completion:27Q/27T frozen identities and restoration',status='passed'))
overview=json.loads((D/'comparison-overview.json').read_text(encoding='utf-8'))
assert len(overview['rows'])==60 and len({(x['variant'],x['scene']) for x in overview['rows']})==60
assert {x['variant'] for x in overview['rows']}==set(expected_ids)
assert {x['scene'] for x in overview['rows']}=={'convergence','kitchen','opaque-room'}
for row in overview['rows']:
    assert row['gpu_busy_ms'] is None or row['gpu_busy_ms']>0
    if row['image']:assert (D/row['image']).is_file()
    if row['variant'] in ['B8','B9','B10']:
        assert row['gpu_busy_ms'] is None and row['hdr_flip'] is None and row['ldr_flip'] is None
        assert row['report']==('B10_GAUSSIAN_PAIRING.md' if row['variant']=='B10' else 'B9_RESULTS.md' if row['variant']=='B9' else 'B8_STAGED_IMPLEMENTATION.md')
        if row['image'] is not None:
            assert 'development' in row['status']
            expected_size=('640x360' if row['scene']=='opaque-room' else '1280x720') if row['variant'] in ['B8','B9','B10'] else '176x90'
            assert expected_size in row['note']
for relative,digest in overview['source_hashes'].items():
    assert hashlib.sha256((P/relative).read_bytes()).hexdigest()==digest
assert 'id="comparison-overview"' in page and 'comparison-overview.json' in page
checks.append(dict(name='Unified canonical overview: all60 scene/variant rows, exact evidence hashes and explicit missing values',status='passed'))
extended=P/'Benchmarks/development/2026-10-29-original-scene-pt-development'
ext_index=json.loads((extended/'index.json').read_text())
assert ext_index['status']=='development_not_accepted' and ext_index['counts']['original_resolution_captures']==4
for name,digest in ext_index['files'].items():assert hashlib.sha256((extended/name).read_bytes()).hexdigest()==digest
for folder in (extended/'original-resolution').iterdir():
    capture=json.loads((folder/'capture.json').read_text());statistics=json.loads((folder/'reservoir-statistics.json').read_text())['final_index']
    assert capture['measurement_status']=='captured' and capture['artifact_identity_after_capture']['validated']
    assert capture['effective_extended_scene_contract']['canonical_accepted'] is False
    assert capture['settings']['width']==1280 and capture['settings']['height']==720
    assert statistics['positive_age_valid']>0 and statistics['m_greater_than_one']>0 and statistics['midpath_reconnection_valid']==0
for scene in ['convergence','kitchen']:
    after=json.loads((extended/'identity-replay'/('after-'+scene+'.json')).read_text());assert after['identity_replay_failures']==0
    for v in ['B6','B7']:
        row=next(x for x in overview['rows'] if x['scene']==scene and x['variant']==v)
        assert row['status']=='in_progress' and row['gpu_busy_ms'] is None and row['image']
checks.append(dict(name='Guarded original-scene evidence:4original-resolution captures, active finite reuse, zero pure-replay self failures and explicit non-acceptance',status='passed'))

finite=P/'Benchmarks/development/2026-10-29-finite-shift-guard'
finite_index=json.loads((finite/'index.json').read_text());assert finite_index['status']=='quality_measured_timing_pending'
assert finite_index['counts']==dict(original_resolution_quality=20,reduced_quality=40,native_di_quality=10,references=12,selected_raw_pfms=6)
for name,digest in finite_index['files'].items():assert hashlib.sha256((finite/name).read_bytes()).hexdigest()==digest
for cohort,count in [('original-resolution',20),('reduced',40),('native-di-control',10)]:
    captures=list((finite/cohort).rglob('capture.json'));assert len(captures)==count
    for path in captures:
        capture=json.loads(path.read_text());assert capture['measurement_status']=='captured' and capture['artifact_identity_after_capture']['validated']
        assert capture['effective_environment_filter']['diffuse_mip']==0
    summary=json.loads((finite/(cohort+'-quality-summary.json')).read_text())
    assert len(summary['rows'])==count
for path in (finite/'original-resolution').rglob('diagnostic-counters.json'):
    counters=json.loads(path.read_text());assert counters['hybrid_returned_nonfinite_target']==counters['hybrid_returned_nonfinite_weight_product']==0
assert len(list(finite.rglob('*.pfm')))==6 and (D/'FINITE_SHIFT_GUARD.md').exists()
for row in overview['rows']:
    if row['variant'] in ['B6','B7'] and row['scene']!='opaque-room':
        assert row['quality_status']=='measured_guarded_matched_filter' and row['gpu_busy_ms'] is None and row['hdr_flip'] is not None
checks.append(dict(name='Finite rejected-shift targets:70quality images,12references,6selected raw PFMs, matched filters, finite returned diagnostics and no invented throughput',status='passed'))

precision=P/'Benchmarks/development/2026-10-29-gbuffer-precision'
if precision.exists():
    index=json.loads((precision/'index.json').read_text())
    assert index['counts']==dict(quality=40,scenes=2,variants=2,precision_settings=2,seeds=5,selected_raw_pfms=2)
    for name,digest in index['files'].items():assert hashlib.sha256((precision/name).read_bytes()).hexdigest()==digest
    summary=json.loads((precision/'quality-summary.json').read_text());assert len(summary['rows'])==40 and len(summary['groups'])==8
    observed=set()
    for path in (precision/'captures').glob('*/capture.json'):
        m=json.loads(path.read_text());assert m['measurement_status']=='captured'
        assert m['artifact_identity']['validated'] and m['artifact_identity_after_capture']['validated']
        assert m['artifact_identity']==m['artifact_identity_after_capture']
        assert m['effective_environment_filter']['diffuse_mip']==0
        q=json.loads((path.parent/'quality.json').read_text());assert m['effective_gbuffer_precision']['rounded_materials']==q['rounded']
        observed.add((q['scene'],q['variant'],q['rounded'],q['seed']))
    assert observed=={(scene,variant,mode,seed) for scene in ['convergence','kitchen'] for variant in ['B4','B7'] for mode in [0,1] for seed in [0,11,47,1019,4093]}
    default=json.loads((precision/'implicit-default-probe.json').read_text())
    assert default['measurement_status']=='captured' and default['effective_gbuffer_precision']['rounded_materials']==0 and not default['effective_gbuffer_precision']['explicit_override']
    invalid=json.loads((precision/'invalid-mode-cli.json').read_text());assert invalid['completed'] and invalid['expected_diagnostic_present']
    old_art=json.loads((precision/'frozen-artifacts.json').read_text());final_art=json.loads((precision/'post-cli-artifacts.json').read_text());assert old_art['shader_file_hashes']==final_art['shader_file_hashes']
    for variant,mode in [('B4',0),('B7',1)]:
        post=json.loads((precision/('post-cli-'+variant+'.json')).read_text());assert post['measurement_status']=='captured' and post['effective_gbuffer_precision']['rounded_materials']==mode and post['artifact_identity_after_capture']['validated']
    assert len(list(precision.rglob('*.pfm')))==2
    assert (D/'GBUFFER_PRECISION.md').exists() and '[RESULT_INTERPRETATION]' not in (D/'GBUFFER_PRECISION.md').read_text()
    assert 'material_precision_ablation' in overview and len(overview['rows'])==60
    checks.append(dict(name='Material precision:40matched captures,8groups,2rawPFMs,exact artifacts,explicit0/1 plus implicit legacy default and separate overview ablation',status='passed'))

di_reuse=P/'Benchmarks/development/2026-10-29-di-reuse-isolation'
if di_reuse.exists():
    import statistics,math
    index=json.loads((di_reuse/'index.json').read_text());assert index['counts']==dict(quality=80,scenes=2,variants=2,di_modes=4,seeds=5,selected_raw_pfms=2)
    for name,digest in index['files'].items():assert hashlib.sha256((di_reuse/name).read_bytes()).hexdigest()==digest
    summary=json.loads((di_reuse/'quality-summary.json').read_text());assert len(summary['rows'])==80 and len(summary['groups'])==16 and len(summary['contrasts_vs_initial'])==12
    observed=set()
    for path in (di_reuse/'captures').glob('*/capture.json'):
        m=json.loads(path.read_text());q=json.loads((path.parent/'quality.json').read_text());assert m['measurement_status']=='captured' and m['artifact_identity']['validated'] and m['artifact_identity_after_capture']['validated'] and m['artifact_identity']==m['artifact_identity_after_capture']
        actual=m['effective_di_reuse'];assert actual['active'] and actual['mode']==q['di_mode'] and not actual['gi'] and actual['pt']==(q['variant']=='B7')
        assert actual['temporal']==(q['di_mode'] in [1,3]) and actual['spatial']==(q['di_mode'] in [2,3])
        assert m['effective_gbuffer_precision']['rounded_materials']==0 and m['effective_environment_filter']['diffuse_mip']==0
        observed.add((q['scene'],q['variant'],q['di_mode'],q['seed']))
    assert observed=={(scene,variant,mode,seed) for scene in ['convergence','kitchen'] for variant in ['B4','B7'] for mode in range(4) for seed in [0,11,47,1019,4093]}
    for group in summary['groups']:
        sample=[x for x in summary['rows'] if (x['scene'],x['variant'],x['di_mode'])==(group['scene'],group['variant'],group['di_mode'])];assert len(sample)==5 and group['n']==5
        values=[x['signed_mean_y_percent'] for x in sample]
        assert abs(statistics.mean(values)-group['mean_signed_y_percent'])<1e-12 and abs(statistics.stdev(values)/math.sqrt(5)-group['signed_y_sample_se'])<1e-12
        assert statistics.median(x['hdr_flip']['mean'] for x in sample)==group['median_hdr_flip']
    exclusion=json.loads((di_reuse/'excluded-timing/outcome.json').read_text());assert exclusion['accepted_timing_samples']==0 and exclusion['driver_restoration_verified']
    audit=json.loads((di_reuse/'retained-trace-log-audit.json').read_text());assert audit['checked']==72 and audit['reported_loss_count']==0
    assert len(list(di_reuse.rglob('*.pfm')))==2 and len(overview['rows'])==60 and 'di_reuse_ablation' in overview
    assert '[RESULT_INTERPRETATION]' not in (D/'DI_REUSE_ISOLATION.md').read_text()
    checks.append(dict(name='DI reuse isolation:80original-scene captures,16groups,12contrasts,actual activation/flags,exact artifacts,reference agreement and independent aggregate checks',status='passed'))

prefix=P/'Benchmarks/development/2026-10-29-prefix-throughput-probe'
if prefix.exists():
    import struct,array,sys
    index=json.loads((prefix/'index.json').read_text());assert index['counts']==dict(physical_captures=8,synthetic_verified_captures=1,packed_textures=9,selected_raw_pfms=2)
    for name,digest in index['files'].items():assert hashlib.sha256((prefix/name).read_bytes()).hexdigest()==digest
    physical=json.loads((prefix/'physical-summary.json').read_text());assert len(physical['rows'])==8 and not physical['any_preserved_values_above_one']
    observed=set();buffers={}
    for path in (prefix/'physical').glob('*/capture.json'):
        m=json.loads(path.read_text());assert m['measurement_status']=='captured' and m['artifact_identity']['validated'] and m['artifact_identity_after_capture']['validated'] and m['artifact_identity']==m['artifact_identity_after_capture']
        actual=m['effective_prefix_throughput'];assert actual['capture_packed'];packed=next(path.parent.glob('*.throughput.bin'));blob=packed.read_bytes();assert blob[:8]==b'RTXPTTHP' and struct.unpack_from('<4I',blob,8)==(1,1280,720,4) and len(blob)==24+1280*720*4
        words=array.array('I');assert words.itemsize==4;words.frombytes(blob[24:])
        if sys.byteorder!='little':words.byteswap()
        assert all((w&0x7ff)<=0x3c0 and ((w>>11)&0x7ff)<=0x3c0 and ((w>>22)&0x3ff)<=0x1e0 for w in words)
        scene='convergence' if path.parent.name.startswith('convergence') else 'kitchen';variant='B4' if '-B4-' in path.parent.name else 'B7';mode=actual['preserve_above_one'];observed.add((scene,variant,mode));buffers[scene,variant,mode]=blob
        assert m['packed_throughput'][0]['statistics']['pixels_above_one']==0 and m['packed_throughput'][0]['statistics']['nonfinite_components']==0
    assert observed=={(scene,variant,mode) for scene in ['convergence','kitchen'] for variant in ['B4','B7'] for mode in [False,True]}
    for scene in ['convergence','kitchen']:
        for variant in ['B4','B7']:assert buffers[scene,variant,False]==buffers[scene,variant,True]
    cal=prefix/'synthetic-calibration';m=json.loads((cal/'capture.json').read_text());assert m['artifact_identity_after_capture']['validated'];blob=next(cal.glob('*.throughput.bin')).read_bytes();words=array.array('I');words.frombytes(blob[24:])
    if sys.byteorder!='little':words.byteswap()
    expected=0x400 | (0x380<<11) | (0x220<<22);assert any(words) and all(w in [0,expected] for w in words)
    restore=json.loads((prefix/'physical-producer-restoration.json').read_text());assert restore['restored'] and restore['runtime_source_copy_restored']
    artifact=json.loads((prefix/'physical-artifacts.json').read_text());assert artifact['shader_file_hashes']['ShaderDynamic/Source/Rtxpt/PathTracerSurfaceBridgeDonut.hlsli']==restore['sha256']
    assert len(list(prefix.rglob('*.pfm')))==2 and len(json.loads((prefix/'radiance-finite-checks.json').read_text()))==8
    for row in json.loads((prefix/'radiance-finite-checks.json').read_text()):assert row['nonfinite_components']==0
    for row in json.loads((prefix/'native-cli-validation.json').read_text()):assert row['exit_code']!=0 and row['expected_diagnostic_present']
    assert 'prefix_throughput_diagnostic' in overview and len(overview['rows'])==60
    checks.append(dict(name='Calibrated prefix:8frozen physical snapshots,exact default/preserve buffers,known synthetic packed words,restoration,finite radiance and CLI rejection',status='passed'))

staged=P/'Benchmarks/development/2026-10-29-b8-staged-partition'
if staged.exists():
    import gzip
    for item in json.loads((staged/'files.json').read_text()):
        blob=(staged/item['path']).read_bytes()
        assert len(blob)==item['bytes'] and hashlib.sha256(blob).hexdigest()==item['sha256']
    identity=json.loads((staged/'final-renderer-artifacts.json').read_text())
    assert hashlib.sha256(gzip.decompress((staged/'renderer-source.patch.gz').read_bytes())).hexdigest()==identity['working_diff_sha256']
    smoke=json.loads((staged/'summary.json').read_text())['runs']
    for cap in range(1,5):
        run=smoke['smoke-cap'+str(cap)];assert run['status']=='captured'
        component=run['checks'][0]['components']
        assert (component['gi_short']['nonzero_pixels']==0)==(cap<2)
        assert (component['pt_long']['nonzero_pixels']==0)==(cap<3)
    assert smoke['b8-sequence-clockfixed']['images']==smoke['b7-sequence']['images']==64
    assert smoke['original-convergence-test']['offline_revalidation']['combined_partition']
    assert smoke['original-kitchen-with-test-stuff']['status']=='captured'
    packed=json.loads((staged/'staged-reservoir-checks.json').read_text())
    for run in packed.values():
        assert run['diagnostic_counters']['replay_roulette_tests']==0
        for slot in run['reservoirs'].values():
            assert slot['nonfinite_m']==slot['nonfinite_target_valid']==slot['nonfinite_weight_valid']==0
            assert all(int(k)>=4 for k in slot['positive_weight_path_length_histogram'])
    assert packed['stage2-pt3-di3']['diagnostic_counters']['roulette_tests']>0
    checks.append(dict(name='B8 staged frozen bytes, same-frame cap support, completed sequences, scoped original scenes and initial-only roulette',status='passed',limits='GI reuse off; no canonical acceptance or new timing.'))

paired=P/'Benchmarks/development/2026-10-29-b10-paired-vector-pilot'
if paired.exists():
    import gzip
    for item in json.loads((paired/'files.json').read_text()):
        blob=(paired/item['path']).read_bytes()
        assert len(blob)==item['bytes'] and hashlib.sha256(blob).hexdigest()==item['sha256']
    identity=json.loads((paired/'final-renderer-artifacts.json').read_text())
    assert hashlib.sha256(gzip.decompress((paired/'renderer-source.patch.gz').read_bytes())).hexdigest()==identity['working_diff_sha256']
    summary=json.loads((paired/'summary.json').read_text())
    assert summary['runs']['final-guard-check']['exe_sha256']==identity['executable_sha256']
    gpu=json.loads((paired/'gpu-checks.json').read_text())
    assert len(gpu)==7
    for run in gpu.values():
        s=run['raw_counters'];meta=run['counters']
        assert 2*s['paired_eligible_pairs']+s['paired_fallback_pixels']==s['paired_vector_output_pixels']==meta['pixels']
        assert s['paired_directed_shift_calls']<=2*s['paired_eligible_pairs']
        assert s['paired_nonfinite_vectors']==s['replay_roulette_tests']==0
        for slot in run['reservoirs'].values():
            assert slot['nonfinite_target_valid']==slot['nonfinite_weight_valid']==slot['nonfinite_m']==0
            assert all(int(k)>=4 for k in slot['positive_weight_path_length_histogram'])
    for filename in ['flip-quality.json','b8-supplemental-flip-quality.json']:
        quality=json.loads((paired/filename).read_text())
        for group in quality['groups'].values():
            assert len(group['frames'])==64
            assert group['mean_image_hdr_flip']['evaluator_version']=='1.7'
            assert group['mean_image_hdr_flip']['parameters']==quality['hdr_parameters']
            assert all(0<=f['hdr_flip_mean']<=1 and 0<=f['ldr_flip_mean']<=1 for f in group['frames'])
    assert json.loads((paired/'vector-output-activation.json').read_text())['different_pixels']>0
    checks.append(dict(name='B10 paired/vector frozen source and bytes, 7GPU ownership/finite receipts and 256official HDR/display FLIP frame evaluations',status='passed',limits='Adjacent single-pair policy and GI initial only; full mechanisms, acceptance and total timing pending.'))

gaussian=P/'Benchmarks/development/2026-10-29-gaussian-pairing'
if gaussian.exists():
    import gzip,struct
    for item in json.loads((gaussian/'files.json').read_text()):
        blob=(gaussian/item['path']).read_bytes()
        assert len(blob)==item['bytes'] and hashlib.sha256(blob).hexdigest()==item['sha256']
    identity=json.loads((gaussian/'final-renderer-artifacts.json').read_text())
    assert hashlib.sha256(gzip.decompress((gaussian/'renderer-source.patch.gz').read_bytes())).hexdigest()==identity['working_diff_sha256']
    cohort_identity=json.loads((gaussian/'cohort-renderer-artifacts.json').read_text())
    assert hashlib.sha256(gzip.decompress((gaussian/'cohort-renderer-source.patch.gz').read_bytes())).hexdigest()==cohort_identity['working_diff_sha256']
    guards=json.loads((gaussian/'final-branch-validation.json').read_text())
    assert guards['comparison']['same_frame_index'] and guards['comparison']['packed_reservoir_bytes_equal']
    for label in ['final-gaussian-guard','final-adjacent-guard']:
        g=guards[label]
        assert g['stats']['paired_nonfinite_vectors']==g['stats']['paired_nonreciprocal_links']==0
        assert all(v['nonfinite_target_valid']==v['nonfinite_weight_valid']==v['nonfinite_m']==0 for v in g['reservoirs'].values())
    native=gzip.decompress((gaussian/'native-pairing.bin.gz').read_bytes())
    native_hash=hashlib.sha256(native).hexdigest()
    assert len(native)==1292128
    summary=json.loads((gaussian/'summary.json').read_text())
    assert summary['native_payload_sha256']==native_hash and len(summary['runs'])==10
    assert all(r['status']=='captured' and r['exe_sha256']==identity['executable_sha256'] for r in summary['runs'].values())
    gpu=json.loads((gaussian/'gpu-checks.json').read_text());assert len(gpu)==7
    for run in gpu.values():
        s=run['stats'];r=run['checks']
        assert run['gpu_tables_sha256']==native_hash
        assert s['paired_nonreciprocal_links']==s['paired_nonfinite_vectors']==s['replay_roulette_tests']==0
        assert s['paired_in_view_nonlocal_pairs']>0 and s['paired_max_link_distance_squared']>1
        assert 2*s['paired_eligible_pairs']+s['paired_fallback_pixels']==s['paired_vector_output_pixels']==r['pixels']
        assert s['paired_directed_shift_calls']<=2*s['paired_eligible_pairs']
        assert all(v['nonfinite_target_valid']==v['nonfinite_weight_valid']==v['nonfinite_m']==0 for v in run['reservoirs'].values())
    for cap in (1,2):
        c=summary['runs']['gaussian-cap'+str(cap)]['component_checks'][0]['components']
        assert c['pt_long']['nonzero_pixels']==0
        if cap==1:assert c['gi_short']['nonzero_pixels']==0
    flip=json.loads((gaussian/'flip-quality.json').read_text())
    for scene in ['room','convergence','kitchen']:
        for g in flip[scene]['groups'].values():
            assert len(g['frames'])==(64 if scene=='room' else 1)
            assert g['mean_image_hdr_flip']['evaluator_version']=='1.7'
            assert g['mean_image_hdr_flip']['parameters']==flip[scene]['hdr_parameters']
    q=json.loads((gaussian/'quality.json').read_text())
    assert q['gaussian-room64']['single_frame_mse_mean']>q['adjacent-room64']['single_frame_mse_mean']
    assert 'gaussian_pairing_development' in overview and len(overview['gaussian_pairing_development']['rows'])==4
    for name,size in [('room',(640,360)),('convergence',(1280,720)),('kitchen',(1280,720))]:
        assert struct.unpack('>II',(D/'assets/b10-gaussian'/f'{name}.png').read_bytes()[16:24])==size
    checks.append(dict(name='Gaussian native/GPU exact bytes, 7reciprocity/coverage gates, original-resolution images, 130official FLIP evaluations and explicit quality tradeoff',status='passed',limits='One table/neighbor per frame; GI initial only; queues, remaining features and timing pending.'))

# Subsequent measured cohorts remain separate from full-version acceptance.
for cohort,expected_count in [('2026-10-29-gaussian-timing',18),('2026-10-29-fresh-b0-pt-only',9)]:
    root=P/'Benchmarks/development'/cohort
    index=json.loads((root/'files.json').read_text())
    for name,expected_sha in index.items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==expected_sha,name
    runs=list((root/'timing').glob('*/run.json'));assert len(runs)==expected_count
    for file in runs:
        run=json.loads(file.read_text());restore=json.loads((file.parent/'restoration-receipt.json').read_text())
        assert run['status']=='timed_completed' and run['image_write_count']==0 and not run['reported_trace_loss']
        assert run['artifact_identity_after_capture']['validated'] and restore['restoration_verified']
    checks.append(dict(name=cohort+' exact evidence hashes and accepted cap/freeze/restoration receipts',status='passed',timed_processes=expected_count))
assert len(overview['b0_pt_only_override']['rows'])==3 and len(overview['gaussian_pairing_timing']['rows'])==3
checkpoint_rows=overview['checkpoint_rows']
assert len(checkpoint_rows)==30
for scene in ['opaque-room','convergence','kitchen']:
    scoped=[x for x in checkpoint_rows if x['scene']==scene]
    assert {x['kind'] for x in scoped}=={'native_pt_only','gaussian_timing','gaussian_quality','spatial_queue_oracle','b8_gi_initial','b8_gi_reuse','b9_matched_B8','b9_limited','duplication_off','duplication_on'}
    assert all(x.get('gpu_busy_ms') is None for x in scoped if x['kind'] in ['gaussian_quality','spatial_queue_oracle'])
    assert all(x.get('ldr_flip') is None and x.get('hdr_flip') is None for x in scoped if x['kind'] in ['gaussian_timing','spatial_queue_oracle'])
    for x in scoped:
        if x.get('image'):assert (D/x['image']).is_file()
checks.append(dict(name='30scoped checkpoints inline beside B0/B8/B9/B10 across all three scene tables; timing/quality/oracle scopes separated',status='passed'))
b8=P/'Benchmarks/development/2026-10-29-b8-nvidia-gi'
for name,expected_sha in json.loads((b8/'files.json').read_text()).items():
    assert hashlib.sha256((b8/name).read_bytes()).hexdigest()==expected_sha,name
b8_summary=json.loads((b8/'summary.json').read_text())
assert len(b8_summary['runs'])==14 and not b8_summary['canonical_acceptance']
for scene,group,size in [('room','full',(640,360)),('convergence','full-continuation',(1280,720)),('kitchen','full-continuation',(1280,720))]:
    m=json.loads((b8/'runs'/group/(scene+'-gi3')/'manifest.json').read_text())
    assert m['measurement_status']=='captured' and m['effective_b8_partition']['gi_reuse']
    assert m['gi_reservoir_snapshots'][0]['statistics']['positive_age_valid']>0
    assert struct.unpack('>II',(D/'assets/b8-nvidia-gi'/(scene+'-gi3.png')).read_bytes()[16:24])==size
checks.append(dict(name='B8 NVIDIA GI approximation:14finite/support GPU snapshots, actual GI history participation and full-resolution original scenes',status='passed',limits='Nondirectional GI approximation; static quality mixed; scoped timing measured, no canonical promotion.'))
b8q=json.loads((b8/'quality.json').read_text())
assert set(b8q['groups'])=={'room','convergence','kitchen'}
for scene,groups in b8q['groups'].items():
    assert len(groups)==2
    for value in groups.values():
        assert value['frames']==64 and len(value['curve'])==64
        assert [f['frame'] for f in value['selected_frame_flip']]==[1,8,32,64]
        assert len({f['hdr_flip']['native_sha256'] for f in value['selected_frame_flip']})==1
        assert all(f['linear_mse']>=0 and f['mean_image_mse']>=0 for f in value['curve'])
assert b8q['groups']['kitchen']['kitchen-gi3']['mean_frame_linear_mse']>b8q['groups']['kitchen']['kitchen-gi-1']['mean_frame_linear_mse']
checks.append(dict(name='B8 six64-frame all-scene quality sequences, official selected-frame FLIP, explicit Kitchen regression and convergence figure',status='passed',limits='One seed/static sequence; not equal-time or independent replication.'))
b8t=b8/'timing-evidence'
assert len(list((b8t/'timing').glob('*/run.json')))==18
for file in (b8t/'timing').glob('*/run.json'):
    run=json.loads(file.read_text());restore=json.loads((file.parent/'restoration-receipt.json').read_text())
    assert run['status']=='timed_completed' and run['image_write_count']==0 and not run['reported_trace_loss']
    assert run['artifact_identity_after_capture']['validated'] and restore['restoration_verified']
    assert run['cap_control']['observed_sync_interval']==0
assert len(overview['b8_gi_timing']['rows'])==3 and len(overview['b8_gi_quality']['groups'])==3
checks.append(dict(name='B8 all18uncapped timing receipts: frozen identities, no image writes/loss and verified restoration',status='passed',limits='Per-process GPU busy/cadence, not complete frame latency or equal-quality speedup.'))

b9=P/'Benchmarks/development/2026-10-30-b9-on-b8'
for name,expected_sha in json.loads((b9/'files.json').read_text()).items():
    assert hashlib.sha256((b9/name).read_bytes()).hexdigest()==expected_sha,name
b9g=json.loads((b9/'gpu-checks.json').read_text());assert len(b9g)==8
for row in b9g:
    assert row['roulette']['replay_tests']==0
    assert row['roulette']['tests']==row['roulette']['survivals']+row['roulette']['terminations']
    if row['case'] in ['convergence-B9','kitchen-B9']:
        assert row['contract']['full_prefix_replay'] and not row['contract']['footprint']
        assert row['pt']['final_index']['midpath_reconnection_valid']==0
    if row['case']=='room-B9':assert row['contract']['footprint'] and row['pt']['final_index']['midpath_reconnection_valid']>0
b9q=json.loads((b9/'quality.json').read_text());assert set(b9q['scenes'])=={'room','convergence','kitchen'}
b9f=json.loads((b9/'timing-evidence/frozen-artifacts.json').read_text());qexes=set()
for scene,item in b9q['scenes'].items():
    assert len(item['groups'])==6
    for version in ['B8','B9']:
        assert item['summary'][version]['runs']==3 and item['summary'][version]['seeds']==[47,1019,4093]
    for value in item['groups'].values():
        assert len(value['curve'])==value['frames']==64
        assert value['actual_resolution']==([640,360] if scene=='room' else [1280,720])
        assert [f['frame'] for f in value['selected_frame_flip']]==[1,8,32,64]
        qexes.add(value['source_exe_sha256'])
        if scene!='room':assert value['contract']['full_prefix_replay'] and not value['contract']['footprint']
assert qexes=={b9f['executable_sha256']}
import gzip
for scene,item in b9q['scenes'].items():
    for version in ['B8','B9']:
        label=f'{scene}-{version}-s47';g=item['groups'][label]
        assert hashlib.sha256((D/'assets/b9-on-b8'/f'{scene}-{version}.png').read_bytes()).hexdigest()==g['selected_frame_flip'][-1]['png_sha256']
        raw=next((b9/'selected-raw'/label).glob('*.gz'))
        assert hashlib.sha256(gzip.decompress(raw.read_bytes())).hexdigest()==g['curve'][-1]['pfm_sha256']
assert json.loads((b9/'paired-quality.json').read_text())['quality_sha256']==hashlib.sha256((b9/'quality.json').read_bytes()).hexdigest()
assert json.loads((b9/'overlay-verification.json').read_text())['matches_frozen_renderer_diff']

assert len(overview['b9_on_b8_quality']['rows'])==6 and len(overview['b9_on_b8_timing']['rows'])==3
assert not json.loads((b9/'summary.json').read_text())['canonical_accepted']
checks.append(dict(name='B9 on B8:8GPU activation/support cases,18three-seed64-frame quality sequences, scene-specific footprint/replay scope and exact exported hashes',status='passed',limits='Original-scene footprint unsupported; cross-process full-image identity unestablished; no canonical promotion.'))
b9runs=list((b9/'timing-evidence').glob('*/run.json'));assert len(b9runs)==18
for file in b9runs:
    run=json.loads(file.read_text());restore=json.loads((file.parent/'restoration-receipt.json').read_text());active=json.loads((file.parent/'b9-effective.json').read_text())
    assert run['status']=='timed_completed' and run['image_write_count']==0 and not run['reported_trace_loss']
    assert run['artifact_identity']['validated'] and run['artifact_identity_after_capture']['validated'] and restore['restoration_verified']
    assert run['cap_control']['observed_sync_interval']==0 and active['gi_reuse']
checks.append(dict(name='B9/B8 all18uncapped timing receipts: source/exe/cache identity, activation, no image writes/loss and verified cap restoration',status='passed',limits='Per-process GPU busy/cadence; three repeats, not complete frame latency or equal-quality speedup.'))
queue=P/'Benchmarks/development/2026-10-29-replay-queue'
index=json.loads((queue/'files.json').read_text())
for name,expected_sha in index.items():assert hashlib.sha256((queue/name).read_bytes()).hexdigest()==expected_sha,name
q=json.loads((queue/'gpu-checks.json').read_text());assert q['status']=='passed_scoped_scheduling_oracle' and len(q['rows'])==11
for row in q['rows']:
    assert row['compared_pixels']==row['width']*row['height'] and row['finite_nonnegative_rgb']
    assert row['reservoir_mismatches']==row['vector_mismatches']==row['overflow']==0
for scene in ['convergence','kitchen']:
    row=next(v for v in q['rows'] if v['case']==scene)
    assert (row['width'],row['height'])==(1280,720) and row['replay_requests']>0
assert len(json.loads((queue/'queue-disabled-regressions.json').read_text()))==2
assert overview['replay_compaction_status']['state']=='partial_gpu_snapshot_oracles_passed'
checks.append(dict(name='11exact GPU queue snapshots, real original-scene replay, disabled regressions and source/evidence hashes',status='passed',limits='Captured-frame checks only; queue-only histories, timing, full GI reuse and complete PT++ remain pending.'))

history_root=P/'Benchmarks/development/2026-10-30-queue-history'
history=json.loads((history_root/'summary.json').read_text())
assert history['status']=='partial_gpu_queue_history_oracles_passed' and not history['canonical_accepted']
assert len(history['rows'])==5 and history['frames_compared']==272
identity=json.loads((history_root/'source-identity.json').read_text())
assert hashlib.sha256((history_root/'renderer-source.patch').read_bytes()).hexdigest()==identity['renderer_patch_sha256']
for row in history['rows']:
    folder=history_root/row['case'];stats=json.loads((folder/'stats.json').read_text())
    assert hashlib.sha256((folder/'stats.json').read_bytes()).hexdigest()==row['stats_sha256']
    assert stats['queue_sequence_frames']==row['frames'] and stats['queue_oracle_pixels']==row['width']*row['height']
    assert all(stats[k]==0 for k in ['queue_sequence_reservoir_failure','queue_sequence_vector_failure','queue_sequence_overflow_failure','queue_reservoir_mismatches','queue_vector_mismatches','queue_overflow'])
    assert hashlib.sha256((folder/'image.png').read_bytes()).hexdigest()==row['image_sha256']
    assert hashlib.sha256((D/'assets/b10-history'/(row['case']+'.png')).read_bytes()).hexdigest()==row['image_sha256']
    assert all(x['finite'] and (x['width'],x['height'])==(row['width'],row['height']) for x in json.loads((folder/'hdr-payloads.json').read_text()))
fault=json.loads((history_root/'fault-sequence-third/stats.json').read_text())
assert fault['queue_reservoir_mismatches']==0 and fault['queue_sequence_reservoir_failure']==1 and fault['queue_sequence_frames']==16
negative=json.loads((history_root/'fault-sequence-third/receipt.json').read_text())
assert negative['expected_rejection'] and negative['last_frame_clean'] and negative['earlier_failure_sticky']
assert negative['restored_shader_sha256']==identity['renderer_source_files']['Rtxpt/RTXDI/PT/ReplayCompaction.hlsl']
assert len(json.loads((history_root/'excluded-attempts.json').read_text()))==3
assert overview['queue_history_validation']==history
assert 'id=\"b10-queue-history\"' in page and 'id=\"b11-integration\"' in page
checks.append(dict(name='B10 static queue history:5GPU cases/272frames, exact state/vector comparisons, earlier-fault rejection, retained excluded attempts and export hashes',status='passed',limits='One spatial neighbor; static chronology; no full PT++, new performance/quality gain or B11 activation.'))

dup_root=P/'Benchmarks/development/2026-10-30-duplication-history'
dup=json.loads((dup_root/'diagnostics.json').read_text())
assert dup['frames']==384 and len(dup['cases'])==6 and not dup['canonical_accepted']
import numpy as np
import sys
sys.path.insert(0,str(P/'Benchmarks/tools'))
from duplication_contract import count_reference
for row in dup['cases']:
    folder=dup_root/'diagnostics'/row['case'];stats=json.loads((folder/'stats.json').read_text())
    assert hashlib.sha256((folder/'stats.json').read_bytes()).hexdigest()==row['stats_sha256']
    assert stats['queue_sequence_frames']==64
    assert all(stats[k]==0 for k in ['queue_sequence_reservoir_failure','queue_sequence_vector_failure','queue_sequence_overflow_failure'])
    if row['enabled']:
        check=json.loads((folder/'count-check.json').read_text())
        assert hashlib.sha256((folder/'oracle-inputs.npz').read_bytes()).hexdigest()==check['oracle_inputs_sha256']
        arrays=np.load(folder/'oracle-inputs.npz');packed=arrays['packed_final'];counts=arrays['counts']
        ids=np.where(packed[...,3].copy().view('<f4')==0,0,packed[...,15])
        assert np.array_equal(counts,count_reference(ids))
        assert stats['duplication_produced_pixels']==row['width']*row['height'] and stats['duplication_nonzero_reads']>0 and check['negative']['expected_rejection']
    else:assert stats['duplication_map_reads']==stats['duplication_produced_pixels']==0
summary=json.loads((dup_root/'summary.json').read_text())
assert overview['duplication_temporal_history']==summary and summary['eligible_quality_sequences']==18 and not summary['canonical_accepted']
assert summary['timing']=='complete18_uncapped_processes' and len(summary['missing_quality_cases'])==0
eligibility=json.loads((dup_root/'quality-eligibility.json').read_text())
assert len(eligibility['eligible_sequences'])==14 and eligibility['eligible_frames']==896
assert len({x['case'] for x in eligibility['eligible_sequences']})==14
for capture in eligibility['eligible_sequences']:
    assert capture['frames']==64 and capture['renderer_exit_code']==0 and len(capture['captures'])==64
    assert capture['executable_sha256']==json.loads((dup_root/'source.json').read_text())['executable_sha256']
    assert all(len(x['pfm_sha256'])==len(x['png_sha256'])==64 for x in capture['captures'])
assert 'id="b10-duplication-history"' in page
checks.append(dict(name='B10 duplication:6GPU cases/384frames, exact exported17x17 counts, negative oracle and active/disabled map reads; completed scoped quality/timing separately verified',status='passed',limits='Deliberately biased temporal cap; static gates only; no complete PT++ or B11 activation.'))

completed=json.loads((dup_root/'quality-completed-eligibility.json').read_text())
quality=json.loads((dup_root/'quality.json').read_text())
assert len(completed['eligible_sequences'])==18 and completed['frames']==1152
assert completed['quality_sha256']==hashlib.sha256((dup_root/'quality.json').read_bytes()).hexdigest()
assert len(quality['scenes'])==3 and sum(len(x['groups']) for x in quality['scenes'].values())==18
for scene,item in quality['scenes'].items():
    for label,group in item['groups'].items():
        assert group['frames']==64 and len(group['curve'])==64 and len(group['selected_frame_flip'])==4
        active=json.loads((dup_root/'quality-runs'/label/'duplication-effective.json').read_text())
        assert active['enabled']==('-on-' in label)
    for policy in ('off','on'):
        group=item['groups'][f'{scene}-{policy}-s47'];image=D/f'assets/b10-duplication/{scene}-{policy}.png'
        assert hashlib.sha256(image.read_bytes()).hexdigest()==group['selected_frame_flip'][-1]['png_sha256']
        raw=next((dup_root/'selected-raw'/f'{scene}-{policy}-s47').glob('*.gz'))
        assert hashlib.sha256(gzip.decompress(raw.read_bytes())).hexdigest()==group['curve'][-1]['pfm_sha256']
frozen=json.loads((dup_root/'frozen-artifacts.json').read_text())
assert frozen['root_source_sha']=='0bd96933236d753a932cb3046e4899a18056f176'
assert all(g['source_exe_sha256']==frozen['executable_sha256'] for x in quality['scenes'].values() for g in x['groups'].values())
runs=list((dup_root/'timing-evidence').glob('*/run.json'));assert len(runs)==18
for path in runs:
    run=json.loads(path.read_text());restore=json.loads((path.parent/'restoration-receipt.json').read_text())
    assert run['status']=='timed_completed' and run['image_write_count']==0 and not run['reported_trace_loss']
    assert run['artifact_identity']['validated'] and run['artifact_identity_after_capture']['validated']
    assert run['cap_control']['observed_sync_interval']==0 and restore['restoration_verified']
    assert run['exe_sha256']==frozen['executable_sha256']
assert json.loads((dup_root/'runtime-restoration.json').read_text())['exact_restoration']
assert json.loads((dup_root/'archive-verification.json').read_text())['all_hashes_match']
assert len(overview['duplication_quality']['rows'])==6 and len(overview['duplication_timing']['rows'])==3
assert (D/'assets/b10-duplication/convergence.svg').is_file()
checks.append(dict(name='B10 duplication complete18quality sequences/1152frames and18uncapped processes: exact exported images/raw hashes, identity, no capture writes/loss, cap and runtime restoration',status='passed',limits='Three static seeds/repeats; full PT++ and startup reliability remain pending; no universal gain.'))
from unified_lighting_oracle import enumerate_ris_mis
from fractions import Fraction as Fraction
oracle=P/'Benchmarks/development/2026-10-30-unified-ris-oracle/results.json';model=json.loads(oracle.read_text())
assert not model['renderer_implemented'] and not model['canonical_accepted']
assert hashlib.sha256((P/'Benchmarks/tools/unified_lighting_oracle.py').read_bytes()).hexdigest()==model['oracle_sha256']
for row in model['rows']:
    m=row['candidates'];value=enumerate_ris_mis([7,2,11],[Fraction(1,2),Fraction(1,3),Fraction(1,6)],[Fraction(1,5),Fraction(3,10),Fraction(1,2)],[1,9,2],m)
    assert value['combined']==20 and row['combined']==dict(numerator=20,denominator=1)
    assert value['missing_pss_conversion']!=20
    if m>1:assert value['stale_single_sample_bsdf_mis']!=20
assert 'id="b10-unified-lighting"' in page
checks.append(dict(name='Paper supplement RIS/MIS/PSS exact finite-domain prerequisite and source hash; unification renderer remains unimplemented',status='passed',limits='No continuous-measure, shift, delta, medium or GPU proof.'))

roadmap_names=['ROADMAP.md','VERSION_MAPPING.md','ALGORITHM_VARIANTS.md']
for name in roadmap_names:
    text=(D/name).read_text(encoding='utf-8')
    for version in ['B10','B10.75','B10.50','B10.25','B11','B12','B13','B14','B15','B16']:assert '**'+version+'**' in text
    for phrase in ['Compatibility-Guided Neighbor Selection active','Stochastic Pairwise MIS','ReSTIR LoD','ReSTIR BDPT with LW version','ReSTIR PG','Multi-Layer Reservoir Splatting']:assert phrase in text
    assert '0.75 spp' in text and '0.50 spp' in text and '0.25 spp' in text
assert by_id['B11']['depends_on']==['B10'] and by_id['B16']['depends_on']==['B15']
assert by_id['B10']['planned_full_unification']['planned']
assert 'one PT reservoir' in (D/'B10_UNIFIED_LIGHTING.md').read_text() and 'all indirect' in (D/'ROADMAP.md').read_text()
checks.append(dict(name='User B10–B16 cumulative roadmap and native B10 sampling branches consistent across registry and three owning docs; definitions separate from activation',status='passed'))

receipt=dict(updated_on='2026-10-29',project='Basix Pathtracing',product='RTXPT Next',repository='BasixMaster/RTXPT_Next',checks=checks,passed=not errors,limits=['Source audit is not algorithm correctness proof.','One GPU. Legacy migration:two original scenes/five process pairs. New native DI:two original scenes/three processes per configuration; registered room:four configurations/three timing processes.','PresentMon GPU active duration is not exclusive DI/GI or complete critical-path latency.','Native controls have display metrics; modern room captures include raw HDR/HDR-FLIP and explicit seeds. Motion, reconstruction and equal-time/error convergence remain pending.','Canonical B1/B4 native controls and B6/B7 registered-room measurements are scoped evidence. Original Convergence/Kitchen PT gates remain. Legacy limited PT++ maps to B7 ablations. B8 initial-GI development, limited PT++ and B10 Gaussian pair/vector development execute; one-neighbor spatial replay queues have scoped snapshot oracles; general directional GI, broader moving/reset queue histories and timing, temporal/multi-neighbor queues, remaining mechanisms and canonical acceptance remain pending.'])
(D/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
if errors:raise SystemExit(json.dumps(errors))
print(json.dumps(dict(passed=True,checks=len(checks),scenes=len(scenes),math_expressions=page.count('<math '))))
