"""Summarize one PresentMon 2.x process/swapchain stream without inferring GPU FPS."""
from __future__ import annotations
import argparse
import csv
import json
import math
from pathlib import Path
import statistics

from analyze_captures import bootstrap_run_median_ci, digest, stats

ALIASES = {
    'CPUFrameTime': ('CPUFrameTime', 'FrameTime'),
    'CPUBusy': ('CPUBusy', 'MsCPUBusy'),
    'CPUWait': ('CPUWait', 'MsCPUWait'),
    'GPUTime': ('GPUTime', 'MsGPUTime'),
    'GPUBusy': ('GPUBusy', 'MsGPUBusy'),
    'GPUWait': ('GPUWait', 'MsGPUWait'),
    'GPULatency': ('GPULatency', 'MsGPULatency'),
    'DisplayedTime': ('DisplayedTime',),
    'DisplayLatency': ('DisplayLatency',),
}
MEANINGS = {
    'CPUFrameTime': 'CPU frame-start cadence, including CPU busy/wait. Not GPU work duration or display duration.',
    'CPUBusy': 'CPU work interval before present; not accumulated CPU core time.',
    'CPUWait': 'CPU waiting before starting the next frame.',
    'GPUTime': 'GPU frame interval including GPU wait; distinct from GPU active-engine duration.',
    'GPUBusy': 'Time with at least one target-process GPU engine active. Not utilization percent, exclusive feature cost or total GPU frame latency.',
    'GPUWait': 'GPU idle time inside the frame GPU interval.',
    'GPULatency': 'CPU frame start until GPU work begins; not GPU execution time.',
    'DisplayedTime': 'Display residence time; unavailable for frames not displayed. Not renderer execution time.',
    'DisplayLatency': 'CPU frame start until display; not GPU execution time.',
}
MISSING = {'', 'na', 'n/a', 'null', 'none'}


def _basename(name):
    return name.replace('\\', '/').rsplit('/', 1)[-1].casefold()


def _number(raw, path, line, field):
    if raw.strip().casefold() in MISSING:
        return None
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f'{path}:{line}: invalid {field}') from exc
    if not math.isfinite(value) or value < 0:
        raise ValueError(f'{path}:{line}: non-finite/negative {field}')
    return value


def read_presentmon(path, process_name, last_n, drop_tail, process_id=None, swapchain=None,
                    allowed_frame_types=('Original', 'NotSet')):
    if last_n <= 0 or drop_tail < 0:
        raise ValueError('last-n must be positive; drop-tail must be nonnegative')
    allowed = {x.casefold() for x in allowed_frame_types}
    if not allowed:
        raise ValueError('At least one allowed FrameType must be declared')
    with Path(path).open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        for required in ['Application', 'ProcessID', 'SwapChainAddress']:
            if required not in fields:
                raise ValueError(f'{path}: required PresentMon identity column missing: {required}')
        mapped = {}
        for canonical, aliases in ALIASES.items():
            found = [x for x in aliases if x in fields]
            if len(found) > 1:
                raise ValueError(f'{path}: ambiguous metric columns for {canonical}: {found}')
            mapped[canonical] = found[0] if found else None
        if mapped['CPUFrameTime'] is None:
            raise ValueError(f'{path}: expects PresentMon 2.x CPUFrameTime/FrameTime column')
        rows, excluded_other_identity = [], 0
        for line, row in enumerate(reader, 2):
            if None in row or any(v is None for v in row.values()):
                raise ValueError(f'{path}:{line}: wrong CSV column count')
            if _basename(row['Application']) != _basename(process_name):
                excluded_other_identity += 1; continue
            if process_id is not None and row['ProcessID'] != str(process_id):
                excluded_other_identity += 1; continue
            if swapchain is not None and row['SwapChainAddress'].casefold() != swapchain.casefold():
                excluded_other_identity += 1; continue
            rows.append((line, row))
    if not rows:
        raise ValueError(f'{path}: no matching process/swapchain rows')
    pids = {r['ProcessID'] for _, r in rows}
    chains = {r['SwapChainAddress'] for _, r in rows}
    if len(pids) != 1:
        raise ValueError(f'{path}: multiple matching process IDs; specify --process-id')
    if len(chains) != 1:
        raise ValueError(f'{path}: multiple matching swapchains; specify --swapchain')
    frame_types = {}
    eligible = []
    has_frame_type = 'FrameType' in fields
    for line, row in rows:
        value = row.get('FrameType', 'column_unavailable')
        frame_types[value] = frame_types.get(value, 0) + 1
        if not has_frame_type or value.casefold() in allowed:
            eligible.append((line, row))
    if len(eligible) < last_n + drop_tail:
        raise ValueError(f'{path}: {len(eligible)} eligible frames; need {last_n + drop_tail} for requested window')
    end = len(eligible) - drop_tail if drop_tail else len(eligible)
    selected = eligible[end-last_n:end]
    metrics = {}
    for canonical, field in mapped.items():
        values = [] if field is None else [v for line, row in selected
                                         if (v := _number(row[field], path, line, field)) is not None]
        metrics[canonical] = dict(status='measured' if values else 'unavailable', source_column=field,
                                  units='ms', meaning=MEANINGS[canonical], valid_frames=len(values),
                                  missing_frames=len(selected)-len(values), statistics=stats(values))
    if metrics['CPUFrameTime']['valid_frames'] == 0:
        raise ValueError(f'{path}: selected window has no measured CPU frame cadence')
    metadata = {key: sorted({row[key] for _, row in selected}) for key in
                ['PresentRuntime', 'SyncInterval', 'PresentFlags', 'AllowsTearing', 'PresentMode'] if key in fields}
    time_field = next((x for x in ['CPUStartTime', 'CPUStartQPCTime', 'CPUStartQPC', 'CPUStartDateTime'] if x in fields), None)
    return dict(file=Path(path).name, sha256=digest(path), source_columns=fields,
                identity=dict(application=process_name, process_id=next(iter(pids)), swapchain=next(iter(chains))),
                selection=dict(target_process_frames=len(rows), excluded_other_identity_frames=excluded_other_identity,
                               frame_type_column_present=has_frame_type, frame_type_counts=frame_types,
                               allowed_frame_types=sorted(allowed_frame_types), eligible_frames=len(eligible),
                               excluded_frame_type_frames=len(rows)-len(eligible), drop_tail_frames=drop_tail,
                               retained_last_frames=last_n, selected_first_csv_line=selected[0][0],
                               selected_last_csv_line=selected[-1][0], cpu_start_column=time_field,
                               selected_first_cpu_start=selected[0][1].get(time_field) if time_field else None,
                               selected_last_cpu_start=selected[-1][1].get(time_field) if time_field else None),
                present_metadata=metadata, metrics=metrics,
                limitations=['Frame-row selection does not prove no image writes or steady state; verify the capture manifest and timing boundary.',
                             'If FrameType is unavailable, generated-frame exclusion is not established by this CSV. Disable frame generation in the renderer and record that setting.',
                             'No explicit trace-loss event count is inferred from frame data.',
                             'PresentMon metrics have different scopes; GPUTime, GPUBusy and CPUFrameTime are not interchangeable.'])


def presentmon_group(paths, label, process_name, last_n, drop_tail, process_id=None, swapchain=None,
                     allowed_frame_types=('Original', 'NotSet')):
    paths = [Path(p) for p in paths]
    if len({p.resolve() for p in paths}) != len(paths):
        raise ValueError('Each process-run CSV may be supplied once only')
    runs = [read_presentmon(p, process_name, last_n, drop_tail, process_id, swapchain, allowed_frame_types) for p in paths]
    summary = {}
    for metric in ALIASES:
        measured = [r['metrics'][metric]['statistics'] for r in runs if r['metrics'][metric]['status'] == 'measured']
        medians = [m['median_ms'] for m in measured]
        summary[metric] = dict(status='measured' if measured else 'unavailable', units='ms',
                               meaning=MEANINGS[metric], measured_process_runs=len(measured),
                               median_of_run_medians_ms=statistics.median(medians) if medians else None,
                               median_of_run_p95s_ms=statistics.median(m['p95_ms'] for m in measured) if measured else None,
                               run_median_ci95=bootstrap_run_median_ci(medians))
    present_configuration = {key: sorted({v for run in runs for v in run['present_metadata'].get(key, [])})
                             for key in ['PresentRuntime', 'SyncInterval', 'AllowsTearing', 'PresentMode']
                             if any(key in run['present_metadata'] for run in runs)}
    return dict(schema_version=1, kind='presentmon_group', label=label,
                tool='PresentMon 2.x CSV; exact executable/version/checksum belong in run manifest',
                selection_policy=dict(process_name=process_name, last_n=last_n, drop_tail=drop_tail,
                                      allowed_frame_types=sorted(allowed_frame_types)),
                process_runs=len(runs), present_configuration=present_configuration, runs=runs, summary=summary,
                limitations=['Each supplied CSV must represent one independent process invocation. Cross-run source/scene/configuration identity needs manifests.',
                             'Fewer than five process repetitions is exploratory under the project protocol.',
                             'This tool emits no total GPU FPS or generated-frame throughput inference.'])


def compare_presentmon(baseline, candidate):
    if any(x.get('kind') != 'presentmon_group' for x in (baseline, candidate)):
        raise ValueError('Expected presentmon_group JSON summaries')
    if baseline['selection_policy'] != candidate['selection_policy']:
        raise ValueError('PresentMon selection policies differ')
    if baseline['present_configuration'] != candidate['present_configuration']:
        raise ValueError('PresentMon observed presentation configuration differs; investigate before comparing')
    comparisons = {}
    for metric in ALIASES:
        b, c = baseline['summary'][metric], candidate['summary'][metric]
        if b['status'] != 'measured' or c['status'] != 'measured':
            comparisons[metric] = dict(status='unavailable', reason='Metric missing in at least one group'); continue
        bv, cv = b['median_of_run_medians_ms'], c['median_of_run_medians_ms']
        comparisons[metric] = dict(status='measured', baseline_ms=bv, candidate_ms=cv,
                                   candidate_change_percent=100*(cv/bv-1) if bv else None,
                                   baseline_over_candidate_ratio=bv/cv if cv else None,
                                   meaning=MEANINGS[metric])
    return dict(schema_version=1, kind='presentmon_comparison', baseline=baseline['label'], candidate=candidate['label'],
                comparisons=comparisons, inference='Descriptive per-metric changes only; compare matching source/configuration and run uncertainty before claiming improvement.',
                limitations=['Ratios are specific to each metric. Do not present inverse GPUBusy/GPUTime as complete renderer FPS.',
                             'Matching CSV selection policies do not establish matching resolution, scene, reconstruction, clocks or presentation state.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('summarize'); p.add_argument('csv', nargs='+'); p.add_argument('--label', required=True)
    p.add_argument('--process-name', required=True); p.add_argument('--process-id', type=int); p.add_argument('--swapchain')
    p.add_argument('--last-n', type=int, required=True); p.add_argument('--drop-tail', type=int, default=16)
    p.add_argument('--allow-frame-type', action='append'); p.add_argument('--output')
    p = sub.add_parser('compare'); p.add_argument('baseline'); p.add_argument('candidate'); p.add_argument('--output')
    args = parser.parse_args()
    try:
        if args.command == 'summarize':
            result = presentmon_group(args.csv, args.label, args.process_name, args.last_n, args.drop_tail,
                                      args.process_id, args.swapchain, args.allow_frame_type or ['Original','NotSet'])
        else:
            result = compare_presentmon(json.loads(Path(args.baseline).read_text(encoding='utf-8')),
                                        json.loads(Path(args.candidate).read_text(encoding='utf-8')))
        text = json.dumps(result, indent=2, allow_nan=False) + '\n'
        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True); Path(args.output).write_text(text,encoding='utf-8')
        else:
            print(text,end='')
    except (ValueError,OSError,KeyError,json.JSONDecodeError) as exc:
        parser.exit(2, f'PresentMon analysis failed: {exc}\n')


if __name__ == '__main__':
    main()
