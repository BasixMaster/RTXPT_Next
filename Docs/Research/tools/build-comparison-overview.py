"""Build the complete canonical overview from preserved benchmark evidence.

Run with Python 3.10+: python build-comparison-overview.py [repository-root]
No network or third-party dependencies; missing measurements stay null.
"""
from pathlib import Path
import hashlib
import json
import statistics
import sys


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def build(repo):
    doc=repo/'Docs/Research'; b=repo/'Benchmarks'; dev=b/'development'
    registry=load(b/'versions.json'); matrix=load(b/'comparison-matrix.json')
    inputs=[b/'versions.json',b/'comparison-matrix.json']
    nativeq=dev/'2026-10-29-canonical-native-di/display-quality-summary.json'
    nativet=dev/'2026-10-29-canonical-native-di-timing/comparison.json'
    roomq=dev/'2026-10-29-registered-room/quality-summary.json'
    roomt=dev/'2026-10-29-registered-room/comparison.json'
    inputs += [nativeq,nativet,roomq,roomt]
    nq,nt,rq,rt=map(load,[nativeq,nativet,roomq,roomt])
    rows=[]
    for scene in matrix['required_scenes']:
        for variant in registry['versions']:
            v=variant['id']; coverage=next(x for x in matrix['rows'] if x['variant']==v and x['scene']==scene)
            row=dict(variant=v,scene=scene,algorithm=variant['algorithm_overview'],status=coverage['status'],
                     note=coverage['reason'],gpu_busy_ms=None,cpu_cadence_ms=None,ldr_flip=None,hdr_flip=None,
                     display_mse=None,linear_mse=None,image=None,report='VERSION_MAPPING.md',cohort=None,
                     history_frames=None,quality_replication=None)
            if scene!='opaque-room' and v in ['B1','B4']:
                q=nq[scene]['groups'][v];t=nt[scene]['groups'][v]['summary']
                row.update(gpu_busy_ms=t['GPUBusy']['median_of_run_medians_ms'],cpu_cadence_ms=t['CPUFrameTime']['median_of_run_medians_ms'],
                           ldr_flip=q['ldr_flip_median'],display_mse=statistics.median(x['metrics']['mse_srgb_encoded_rgb'] for x in q['metrics']),
                           image=f'assets/canonical-native-di/{scene}-{v}.png',report='CANONICAL_NATIVE_DI_RESULTS.md',
                           cohort='native-di-2026-10-29',quality_replication='3 process restarts; independent seeds unavailable',history_frames=64)
            elif scene=='opaque-room' and v in ['B1','B4','B6','B7']:
                q=next(x for x in rq['groups'] if x['variant']==v and x['history_frames']==64);t=rt['groups'][v]['summary']
                row.update(gpu_busy_ms=t['GPUBusy']['median_of_run_medians_ms'],cpu_cadence_ms=t['CPUFrameTime']['median_of_run_medians_ms'],
                           ldr_flip=q['median_ldr_flip'],display_mse=q['median_display_mse'],hdr_flip=q.get('median_hdr_flip'),linear_mse=q.get('median_linear_rgb_mse'),
                           image=f'assets/registered-room/{v}.png',report='REGISTERED_ROOM_RESULTS.md',cohort='registered-room-2026-10-29',
                           quality_replication=q['quality_replication'],history_frames=64)
            rows.append(row)

    # Newly completed cohorts are optional until all their acceptance checks pass.
    extra=dev/'2026-10-29-native-matrix-completion/overview-input.json'
    if extra.exists():
        completion=load(extra)
        if completion.get('status')!='accepted':raise ValueError('Incomplete cohort must not enter the overview')
        inputs.append(extra)
        for item in completion['rows']:
            row=next(x for x in rows if x['variant']==item['variant'] and x['scene']==item['scene'])
            row.update(item)

    development=dev/'2026-10-29-original-scene-pt-development/overview-input.json'
    if development.exists():
        candidate=load(development)
        if candidate.get('status')!='development_not_accepted':raise ValueError('Development cohort needs an explicit non-acceptance label')
        inputs.append(development)
        for item in candidate['rows']:
            if item['variant'] not in ['B6','B7'] or item['scene'] not in ['convergence','kitchen'] or item['gpu_busy_ms'] is not None:
                raise ValueError('Guarded original-scene pictures cannot supply accepted throughput')
            row=next(x for x in rows if x['variant']==item['variant'] and x['scene']==item['scene'])
            row.update(item)

    assert len(rows)==33 and len({(x['variant'],x['scene']) for x in rows})==33
    for x in rows:
        if x['image'] and not (doc/x['image']).is_file():raise ValueError('Missing overview image: '+x['image'])
        if x['gpu_busy_ms'] is not None and x['gpu_busy_ms']<=0:raise ValueError('Unavailable timings cannot be zero')
    data=dict(schema_version=1,numbering_scheme=registry['numbering_scheme'],updated_on='2026-10-29',
              metrics=dict(gpu_busy_ms='Median of per-process GPUBusy medians; not complete critical-path frame time/FPS',
                           ldr_flip='Official LDR-FLIP1.7, PPD67; lower is better',hdr_flip='Official HDR-FLIP1.7; scene-reference-only exposure parameters'),
              source_hashes={p.relative_to(repo).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},rows=rows)
    (doc/'comparison-overview.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    md=['# B0–B10 comparison overview','',
        'All eleven canonical versions appear below for each required scene. Performance, quality and representative pictures share the same row. **Not measured means unavailable, never zero.** B0 remains the unchanged RTXPT1.9 reference; a raw native-control preset does not replace its original defaults.','',
        'GPU busy is process GPU activity in milliseconds, not complete frame latency or an FPS estimate. Lower FLIP/MSE is better. Rows from different cohorts are descriptive: settings and sampling policies must be checked before computing a relative gain. Known app/NVIDIA/RTSS cap boundaries were verified for accepted current timing cohorts; unknown external limiters and background load remain limitations.','',
        '[Machine-readable overview](comparison-overview.json) · [Algorithm definitions and identities](VERSION_MAPPING.md) · [Benchmark protocol](BENCHMARK_VERSIONS.md)','']
    captions={'opaque-room':('Controlled room — registered environment','640×360,1spp,3/3 bounce limits; opaque-room-registered-env.scene.json. This is a distinct fixture from the legacy no-environment room. Native controls retain their DI/MIS policies; B6/B7 use their documented PT/strict-DI policies.'),
              'convergence':('Original Convergence','1280×720,1spp,14/2 bounce limits, exposure0. Original materials and camera preserved.'),
              'kitchen':('Original Kitchen','1280×720,1spp,14/2 bounce limits, exposure2. Original materials and camera preserved.')}
    def fmt(value,digits):return 'Unavailable' if value is None else f'{value:.{digits}f}'
    for scene in ['opaque-room','convergence','kitchen']:
        title,caption=captions[scene];md += ['## '+title,'',caption,'',
          '| Version | Algorithm | GPU busy ms ↓ | LDR-FLIP ↓ | HDR-FLIP ↓ | Picture | Evidence status |',
          '|---|---|---:|---:|---:|---|---|']
        for x in [r for r in rows if r['scene']==scene]:
            image=f'[![{x["variant"]} {scene} representative capture]({x["image"]})]({x["image"]})' if x['image'] else 'No eligible capture'
            status='Development, not accepted †' if x.get('quality_status')=='guarded_development_not_accepted' else x['status'].replace('_',' ')
            md.append(f'| **{x["variant"]}** | {x["algorithm"]} | {fmt(x["gpu_busy_ms"],3)} | {fmt(x["ldr_flip"],6)} | {fmt(x["hdr_flip"],6)} | {image} | [{status}]({x["report"]}) |')
        md += ['', '<details><summary>Coverage and missing-data reasons</summary>','']
        for x in [r for r in rows if r['scene']==scene]:md += [f'- **{x["variant"]}:** {x["note"]}']
        md += ['','</details>','']
    md += ['† Original-scene B6/B7 pictures and LDR-FLIP are guarded development captures: one explicit seed, active reuse and finite raw output. Reduced-resolution multi-seed tests retain an unresolved brightness deficit. Their timing remains unavailable and the pictures do not establish accepted support. See the [scene-fix report](PT_EXTENDED_SCENES.md).','', '## Historical observations — different cohorts','',
      'These retained measurements remain useful context, but are excluded from the current tables’ numeric columns. Their settings, scene identity or cap evidence differ. Historical images are available through the linked reports; they are not substitutes for missing current captures.','',
      '| Canonical interpretation | Scene | GPU busy ms | LDR-FLIP | Scope and pictures |',
      '|---|---|---:|---:|---|',
      '| B2: native PT + DI/GI3.0 | Convergence | 4.4584 | 0.24355 | [Legacy migration cohort; caps unverified](B1_RESULTS.md) |',
      '| B5: native PT + DI/GI3.1 | Convergence | 4.4530 | 0.24338 | [Legacy migration cohort; caps unverified](B1_RESULTS.md) |',
      '| B2: native PT + DI/GI3.0 | Kitchen | 5.3398 | 0.35210 | [Legacy migration cohort; caps unverified](B1_RESULTS.md) |',
      '| B5: native PT + DI/GI3.1 | Kitchen | 5.3591 | 0.35226 | [Legacy migration cohort; caps unverified](B1_RESULTS.md) |',
      '| B0/raw-native-control, not original defaults | Legacy room, no registered environment | 0.803 | See report | [DI/GI off; different fixture](B2_RESULTS.md) |',
      '| B3: native PT, DI/GI off | Legacy room, no registered environment | 0.806 | See report | [Different fixture](B2_RESULTS.md) |',
      '| B7: ReSTIR PT + DI3.1 | Legacy room, no registered environment | 1.519 | See report | [Earlier checkpoint](B2_RESULTS.md) |','',
      '## Quality detail and convergence coverage','',
      'The JSON includes display MSE, available linear MSE and CPU cadence alongside each current result. [Registered-room history curves and finite-reference checks](REGISTERED_ROOM_RESULTS.md) cover B6/B7 at1,8,32,64 warm-up frames and three explicit seeds. These are separate1spp history-settling snapshots, not accumulated-spp convergence or time-to-equal-quality. Native captures use three process restarts without verified independent seeds. Original-scene native quality uses finite4096spp references; the room uses a separate finite8192spp native reference with discrepancy checks. HDR-FLIP is unavailable for native original-shader controls.','',
      '## Summary and lessons learned','',
      'The current registered-room comparison shows B7 costing19.4%more process GPU busy than B4 while lowering LDR-FLIP by45.1%. Original Convergence/Kitchen B1/B4 timing changes are below1%; they do not demonstrate a general speedup. B6/B7 now have guarded original-scene development captures, with quality acceptance still pending because of a brightness deficit. B8 GPU sharing and B9/B10 PT++ configurations remain pending; their rows stay visible until eligible measurements exist.','',
      '## Changes','', '- 2026-10-29: Added one generated overview with all33 version/scene rows, explicit missing coverage, representative images and retained historical cohort links.','']
    (doc/'COMPARISON_OVERVIEW.md').write_text('\n'.join(md),encoding='utf-8')
    print(json.dumps(dict(rows=len(rows),measured_rows=sum(x['gpu_busy_ms'] is not None for x in rows),images=sum(x['image'] is not None for x in rows))))


if __name__=='__main__':build(Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[3])
