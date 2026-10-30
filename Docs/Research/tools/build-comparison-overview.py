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
            if v in ['B8','B9','B10']:
                row['report']='B8_STAGED_IMPLEMENTATION.md'
                row['algorithm']={'B8':'B8 development: DI + approximate GI-short reuse + PT-long','B9':'B9 development: initial-GI split + footprint/roulette','B10':'B10 development: initial-GI split + Gaussian pair/vector pilot'}[v]
                if v=='B8':
                    row['image']='assets/b8-nvidia-gi/'+('room' if scene=='opaque-room' else scene)+'-gi3.png'
                    row['note']='NVIDIA non-directional GI reuse: '+('640x360 cap4/4' if scene=='opaque-room' else '1280x720 cap14/2')+',64-frame static quality measured; mixed results. Scoped timing is shown separately when available; no canonical promotion.'
                elif v=='B10':
                    row['report']='B10_UNIFIED_LIGHTING.md'
                    row['algorithm']='B10: Full PT++ (partial integration)'
                    row['image']=None
                    row['note']='Full B10 comparison pending. Component diagnostics, captures and ablations are available in the detailed B10 reports; no eligible full-version picture or performance/quality result yet.'
                elif v=='B9' and scene=='opaque-room':
                    row['image']='assets/b8-staged/limited-ptpp.png'
                    row['note']+=' Image is a176x90 development illustration, not a matched comparison.'
            if v=='B9':
                row['report']='B9_RESULTS.md'
                row['image']='assets/b9-on-b8/'+('room' if scene=='opaque-room' else scene)+'-B9.png'
                row['algorithm']='B9 on B8: GI reuse + '+('footprint/roulette' if scene=='opaque-room' else 'full-prefix roulette-only ablation')
                row['note']='Eight GPU diagnostics passed; '+('640x360 cap4/4' if scene=='opaque-room' else '1280x720 cap14/2')+' snapshot shown. Three-seed64-frame quality and uncapped timing in progress. Original-scene footprint remains unsupported; no promotion.'
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

    finite=dev/'2026-10-29-finite-shift-guard/overview-input.json'
    if finite.exists():
        update=load(finite)
        if update['status']!='quality_measured_timing_pending':raise ValueError('Unexpected finite-shift evidence status')
        inputs.append(finite)
        for item in update['rows']:
            if item['gpu_busy_ms'] is not None:raise ValueError('Quality captures cannot supply throughput')
            row=next(x for x in rows if x['variant']==item['variant'] and x['scene']==item['scene'])
            row.update(item)

    assert len(rows)==len(registry['versions'])*3 and len({(x['variant'],x['scene']) for x in rows})==len(registry['versions'])*3
    for x in rows:
        if x['image'] and not (doc/x['image']).is_file():raise ValueError('Missing overview image: '+x['image'])
        if x['gpu_busy_ms'] is not None and x['gpu_busy_ms']<=0:raise ValueError('Unavailable timings cannot be zero')
    precision_path=dev/'2026-10-29-gbuffer-precision/quality-summary.json'
    precision=load(precision_path) if precision_path.exists() else None
    if precision:inputs.append(precision_path)
    di_reuse_path=dev/'2026-10-29-di-reuse-isolation/quality-summary.json'
    di_reuse=load(di_reuse_path) if di_reuse_path.exists() else None
    if di_reuse:inputs.append(di_reuse_path)
    prefix_path=dev/'2026-10-29-prefix-throughput-probe/physical-summary.json'
    prefix=load(prefix_path) if prefix_path.exists() else None
    if prefix:inputs.append(prefix_path)
    gaussian=None
    gaussian_path=dev/'2026-10-29-gaussian-pairing'
    if gaussian_path.exists():
        paths=[gaussian_path/'quality.json',gaussian_path/'flip-quality.json']
        inputs+=paths
        gq,gf=map(load,paths)
        gaussian=dict(report='B10_GAUSSIAN_PAIRING.md',scope='Separate development cohorts; not canonical acceptance or timing',rows=[])
        for label in ['adjacent-room64','gaussian-room64']:
            f=gf['room']['groups'][label]
            gaussian['rows'].append(dict(label=label,scene='opaque-room',resolution='640x360',frames=64,
                linear_mse=gq[label]['single_frame_mse_mean'],hdr_flip=f['mean_frame_hdr_flip'],ldr_flip=f['mean_frame_ldr_flip']))
        for scene in ['convergence','kitchen']:
            label='gaussian-'+scene;f=gf[scene]['groups'][label]
            gaussian['rows'].append(dict(label=label,scene=scene,resolution='1280x720',frames=1,
                linear_mse=gq[label]['metrics']['linear_rgb_mse'],hdr_flip=f['mean_frame_hdr_flip'],ldr_flip=f['mean_frame_ldr_flip']))
    data=dict(schema_version=1,numbering_scheme=registry['numbering_scheme'],updated_on='2026-10-29',
              metrics=dict(gpu_busy_ms='Median of per-process GPUBusy medians; not complete critical-path frame time/FPS',
                           ldr_flip='Official LDR-FLIP1.7, PPD67; lower is better',hdr_flip='Official HDR-FLIP1.7; scene-reference-only exposure parameters'),
              source_hashes={p.relative_to(repo).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},rows=rows)
    if precision:data['material_precision_ablation']=precision
    if di_reuse:data['di_reuse_ablation']=di_reuse
    if prefix:data['prefix_throughput_diagnostic']=prefix
    if gaussian:data['gaussian_pairing_development']=gaussian
    pairing_timing=dev/'2026-10-29-gaussian-timing/summary.json'
    if pairing_timing.exists():
        data['gaussian_pairing_timing']=load(pairing_timing)
        data['source_hashes'][pairing_timing.relative_to(repo).as_posix()]=hashlib.sha256(pairing_timing.read_bytes()).hexdigest()
    native_override=dev/'2026-10-29-fresh-b0-pt-only/overview-input.json'
    if native_override.exists():
        data['b0_pt_only_override']=load(native_override)
        data['source_hashes'][native_override.relative_to(repo).as_posix()]=hashlib.sha256(native_override.read_bytes()).hexdigest()
    # Render scoped checkpoints beside their canonical version in each scene.
    # Keep timing, quality and queue-oracle acquisitions explicitly distinct.
    checkpoints=[]
    for item in data.get('b0_pt_only_override',{}).get('rows',[]):
        checkpoints.append(dict(item,kind='native_pt_only',label='B0 · PT-only control',
            evidence='Measured override; original defaults preserved. Room4/4; originals14/2.'))
    for item in data.get('gaussian_pairing_timing',{}).get('rows',[]):
        checkpoints.append(dict(variant='B10',scene=item['scene'],kind='gaussian_timing',label='B10 · Gaussian timing',
            algorithm='DI initial + GI initial + paired/vector PT; one Gaussian neighbor',
            gpu_busy_ms=item['gaussian_gpu_busy_ms'],ldr_flip=None,hdr_flip=None,image=None,
            report='B10_GAUSSIAN_PAIRING.md',evidence='3 timed processes; quality is a separate row. Room4/4; originals14/2.'))
    for item in (gaussian or {}).get('rows',[]):
        if not item['label'].startswith('gaussian-'):continue
        scene=item['scene'];image='assets/b10-gaussian/'+('room' if scene=='opaque-room' else scene)+'.png'
        checkpoints.append(dict(item,variant='B10',kind='gaussian_quality',label='B10 · Gaussian quality',
            algorithm='One-neighbor paired/vector PT; GI initial only',gpu_busy_ms=None,image=image,
            report='B10_GAUSSIAN_PAIRING.md',evidence='Quality-only cohort: '+('64-frame sequence, cap4/4.' if scene=='opaque-room' else '1 image,8 warmup frames, cap14/2.')))
    queue_checks=dev/'2026-10-29-replay-queue/gpu-checks.json'
    if queue_checks.exists():
        data['source_hashes'][queue_checks.relative_to(repo).as_posix()]=hashlib.sha256(queue_checks.read_bytes()).hexdigest()
        queue=load(queue_checks)
        for scene,case in [('opaque-room','room-h8'),('convergence','convergence'),('kitchen','kitchen')]:
            q=next(x for x in queue['rows'] if x['case']==case)
            checkpoints.append(dict(variant='B10',scene=scene,kind='spatial_queue_oracle',label='B10 · Replay queue',
                algorithm='One-neighbor spatial replay queue; DI/GI initial',gpu_busy_ms=None,ldr_flip=None,hdr_flip=None,
                image='assets/b10-queue/'+scene+'.png',report='B10_GAUSSIAN_PAIRING.md',
                evidence=f"Exact snapshot: {q['width']}x{q['height']}, cap{'4/4' if scene=='opaque-room' else '14/2'}, {q['replay_requests']} replays,0 mismatches. Timing/quality scores pending."))
    b8_path=dev/'2026-10-29-b8-nvidia-gi/summary.json'
    if b8_path.exists():
        b8=load(b8_path)
        data['b8_nvidia_gi_development']=b8
        data['source_hashes'][b8_path.relative_to(repo).as_posix()]=hashlib.sha256(b8_path.read_bytes()).hexdigest()
        b8_quality_path=b8_path.parent/'quality.json'
        b8_quality=load(b8_quality_path) if b8_quality_path.exists() else None
        b8_timing_path=b8_path.parent/'timing-evidence/summary.json'
        b8_timing=load(b8_timing_path) if b8_timing_path.exists() else None
        for path in [b8_quality_path,b8_timing_path]:
            if path.exists():data['source_hashes'][path.relative_to(repo).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
        if b8_quality:data['b8_gi_quality']=b8_quality
        if b8_timing:data['b8_gi_timing']=b8_timing
        for scene in ['opaque-room','convergence','kitchen']:
            name='room' if scene=='opaque-room' else scene
            for mode in [-1,3]:
                g=b8_quality['groups'][name][f'{name}-gi{mode}'] if b8_quality else None
                t=next(x for x in b8_timing['rows'] if x['scene']==scene) if b8_timing else None
                final_flip=g['selected_frame_flip'][-1] if g else None
                checkpoints.append(dict(variant='B8',scene=scene,kind='b8_gi_initial' if mode<0 else 'b8_gi_reuse',
                    label='B8 · GI initial control' if mode<0 else 'B8 · NVIDIA GI reuse',
                    algorithm='DI + GI-short '+('initial' if mode<0 else 'temporal/spatial approximation')+' + PT-long',
                    gpu_busy_ms=t['initial_gpu_busy_ms' if mode<0 else 'reuse_gpu_busy_ms'] if t else None,
                    ldr_flip=final_flip['ldr_flip'] if g else None,hdr_flip=final_flip['hdr_flip']['mean'] if g else None,
                    mean_frame_linear_mse=g['mean_frame_linear_mse'] if g else None,mean_image_linear_mse=g['mean_image_metrics']['linear_rgb_mse'] if g else None,
                    mean_y_difference_percent=g['mean_y_difference_percent'] if g else None,image=f'assets/b8-nvidia-gi/{name}-gi{mode}.png',
                    report='B8_STAGED_IMPLEMENTATION.md',evidence=('64-frame static sequence, frame64 FLIP; ' if g else 'Finite full-resolution snapshot; quality pending; ')+('3 uncapped timing processes. ' if t else 'timing pending. ')+('Initial-only GI control. ' if mode<0 else 'Nondirectional GI approximation. ')+('Cap4/4. ' if scene=='opaque-room' else 'Cap14/2. ')+'Mixed quality; not canonical acceptance.'))
    b9_path=dev/'2026-10-30-b9-on-b8/quality-summary.json'
    if b9_path.exists():
        b9=load(b9_path);data['b9_on_b8_quality']=b9
        data['source_hashes'][b9_path.relative_to(repo).as_posix()]=hashlib.sha256(b9_path.read_bytes()).hexdigest()
        b9_timing_path=b9_path.parent/'timing-summary.json'
        b9_timing=load(b9_timing_path) if b9_timing_path.exists() else None
        if b9_timing:
            data['b9_on_b8_timing']=b9_timing;data['source_hashes'][b9_timing_path.relative_to(repo).as_posix()]=hashlib.sha256(b9_timing_path.read_bytes()).hexdigest()
        for item in b9['rows']:
            scene=item['scene'];version=item['variant'];t=next((x for x in b9_timing['rows'] if x['scene']==scene),None) if b9_timing else None
            checkpoints.append(dict(item,kind='b9_matched_B8' if version=='B8' else 'b9_limited',
                label='B8 · matched B9 control' if version=='B8' else 'B9 · '+('footprint + roulette' if scene=='opaque-room' else 'roulette only'),
                gpu_busy_ms=t['B8_gpu_busy_ms' if version=='B8' else 'B9_gpu_busy_ms'] if t else None,
                report='B9_RESULTS.md',evidence='Three seeds ×64static frames; frame64 FLIP. '+('Three uncapped timings. ' if t else 'Timing pending. ')+('Room cap4/4. ' if scene=='opaque-room' else 'Original cap14/2; footprint unsupported. ')+'Development, no promotion.'))
    history_path=repo/'Benchmarks/development/2026-10-30-queue-history/summary.json'
    history=load(history_path) if history_path.exists() else None
    if history:
        data['queue_history_validation']=history
        data['source_hashes'][history_path.relative_to(repo).as_posix()]=hashlib.sha256(history_path.read_bytes()).hexdigest()
    duplication=load(repo/'Benchmarks/development/2026-10-30-duplication-history/summary.json')
    data['duplication_temporal_history']=duplication
    dup_root=repo/'Benchmarks/development/2026-10-30-duplication-history'
    dq=load(dup_root/'quality-summary.json');dt=load(dup_root/'timing-summary.json')
    data['duplication_quality']=dq;data['duplication_timing']=dt
    for source in ['summary.json','quality-summary.json','timing-summary.json','quality.json','paired-quality.json']:
        path=dup_root/source;data['source_hashes'][path.relative_to(repo).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    for row in dq['rows']:
        t=next(v for v in dt['rows'] if v['scene']==row['scene'])
        checkpoints.append(dict(row,kind='duplication_'+row['policy'],label='B10 dev · duplication '+row['policy'],gpu_busy_ms=t[row['policy']+'_gpu_busy_ms'],report='B10_DUPLICATION_HISTORY.md',evidence='Three seeds ×64frames; frame64 FLIP; three separate uncapped timings. Static development ablation, not full B10.'))
    data['checkpoint_rows']=checkpoints
    for item in checkpoints:
        if item.get('image') and not (doc/item['image']).is_file():raise ValueError('Missing checkpoint picture')
    (doc/'comparison-overview.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    # User-confirmed presentation policy: only registered Bx variants in the
    # overview. Historical/acquisition metadata stays available for provenance;
    # experimental tables and images belong to their owning reports.
    data['display_policy'] = dict(registered_variants_only=True,variants=[v['id'] for v in registry['versions']],experimental_rows_inline=False)
    queue_status=doc/'replay-compaction-status.json'
    if queue_status.exists():
        data['replay_compaction_status']=load(queue_status)
        data['source_hashes'][queue_status.relative_to(repo).as_posix()]=hashlib.sha256(queue_status.read_bytes()).hexdigest()
    (doc/'comparison-overview.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    md=['# B0–B16 and sampling-variant comparison overview','',
        'One row per registered Bx version and required scene, including the B10 sampling variants. **Unavailable means not measured, never zero.** Experimental checkpoints, overrides and ablations are kept in their detailed reports. B0 remains the unchanged RTXPT1.9 reference.','',
        'GPU busy is process GPU activity in milliseconds, not complete frame latency or an FPS estimate. Lower FLIP/MSE is better. Different cohorts are descriptive; check settings and sampling policies before calculating relative gains. Accepted current timing cohorts include app/NVIDIA/RTSS cap checks; unknown external limiters and background load remain limitations.','',
        '**B10 is partial:** unified finite/environment MIS and initial-only roulette have scoped diagnostic checks, but no accepted full-B10 performance/quality comparison. [B10 implementation and evidence](B10_UNIFIED_LIGHTING.md) · [Roadmap](ROADMAP.md).','',
        '[Research summary](RESEARCH_SUMMARY.md) · [Algorithm definitions](VERSION_MAPPING.md) · [Benchmark protocol](BENCHMARK_VERSIONS.md) · [Machine-readable data](comparison-overview.json)','']
    captions={'opaque-room':('Controlled room — registered environment','Main rows use640×360,1spp,3/3 bounce limits unless the evidence status states a different development scope. Native controls retain their DI/MIS policies. Development pictures are illustrations, not accepted matched comparisons.'),
              'convergence':('Original Convergence','1280×720,1spp,14/2 bounce limits, exposure0. Original materials and camera preserved.'),
              'kitchen':('Original Kitchen','1280×720,1spp,14/2 bounce limits, exposure2. Original materials and camera preserved.')}
    def fmt(value,digits):return 'Unavailable' if value is None else f'{value:.{digits}f}'
    for scene in ['opaque-room','convergence','kitchen']:
        title,caption=captions[scene];md += ['## '+title,'',caption,'',
          '| Version | Algorithm | GPU busy ms ↓ | LDR-FLIP ↓ | HDR-FLIP ↓ | Picture | Evidence status |',
          '|---|---|---:|---:|---:|---|---|']
        for x in [r for r in rows if r['scene']==scene]:
            image=f'[![{x["variant"]} {scene} representative capture]({x["image"]})]({x["image"]})' if x['image'] else 'No eligible capture'
            status=('Guarded quality measured; timing pending †' if x.get('quality_status')=='measured_guarded_matched_filter' else 'Development, not accepted †' if x.get('quality_status')=='guarded_development_not_accepted' else x['status'].replace('_',' '))
            md.append(f'| **{x["variant"]}** | {x["algorithm"]} | {fmt(x["gpu_busy_ms"],3)} | {fmt(x["ldr_flip"],6)} | {fmt(x["hdr_flip"],6)} | {image} | [{status}]({x["report"]}) |')
        md += ['', '<details><summary>Coverage and missing-data reasons</summary>','']
        for x in [r for r in rows if r['scene']==scene]:md += [f'- **{x["variant"]}:** {x["note"]}']
        md += ['','</details>','']
    md += ['† Guarded original-scene B6/B7 quality uses five explicit seeds and matched MIP0 references. It is not unrestricted scene acceptance or a new throughput result. [Scene-support evidence](FINITE_SHIFT_GUARD.md).','',
        '## Detailed studies','',
        '[Unified lighting](B10_UNIFIED_LIGHTING.md) · [Replay queues](B10_QUEUE_HISTORY.md) · [Pairing and vector shading](B10_GAUSSIAN_PAIRING.md) · [Duplication history](B10_DUPLICATION_HISTORY.md) · [B9 ablations](B9_RESULTS.md) · [Native controls and overrides](NATIVE_MATRIX_RESULTS.md) · [DI reuse isolation](DI_REUSE_ISOLATION.md) · [Material precision](GBUFFER_PRECISION.md) · [Prefix throughput](PREFIX_THROUGHPUT.md)','']
    (doc/'COMPARISON_OVERVIEW.md').write_text('\n'.join(md),encoding='utf-8')
    print(json.dumps(dict(rows=len(rows),measured_rows=sum(x['gpu_busy_ms'] is not None for x in rows),images=sum(x['image'] is not None for x in rows))))


if __name__=='__main__':build(Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[3])
