"""Build compact research figures from preserved evidence; launches no rendering."""
from pathlib import Path
import argparse, hashlib, json, sys

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[2])
    p.add_argument('--plot-module-dir',type=Path)
    p.add_argument('--preview-dir',type=Path)
    a=p.parse_args()
    if a.plot_module_dir:sys.path.insert(0,str(a.plot_module_dir.resolve()))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    r=a.repo.resolve();e=r/'Benchmarks/development';out=r/'Docs/Research/assets/research-summary';out.mkdir(parents=True,exist_ok=True)
    inputs={}
    def read(rel):
        f=e/rel;inputs[rel]=hashlib.sha256(f.read_bytes()).hexdigest();return json.loads(f.read_text())
    experiments=[('B9 vs B8','2026-10-30-b9-on-b8','B8','B9'),('B10 duplication on vs off','2026-10-30-duplication-history','off','on')]
    rows=[]
    for label,folder,control,candidate in experiments:
        q=read(folder+'/quality-summary.json')['rows'];timing=read(folder+'/timing-summary.json')['rows']
        for scene in ['opaque-room','convergence','kitchen']:
            field='policy' if control=='off' else 'variant'
            before=next(x for x in q if x['scene']==scene and x[field]==control)
            after=next(x for x in q if x['scene']==scene and x[field]==candidate)
            t=next(x for x in timing if x['scene']==scene)
            assert before['runs']==after['runs']==3
            rows.append(dict(experiment=label,scene=scene,gpu_busy_change_percent=t['gpu_busy_change_percent'],mean_image_mse_change_percent=100*(after['mean_image_mse']/before['mean_image_mse']-1),hdr_flip_change_percent=100*(after['hdr_flip']/before['hdr_flip']-1)))
    plt.rcParams.update({'svg.fonttype':'none','svg.hashsalt':'basix-research-summary','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,3,figsize=(12.8,4.6),layout='constrained',sharey=True)
    labels=['B9 / Room','B9 / Convergence','B9 / Kitchen','Duplication / Room','Duplication / Convergence','Duplication / Kitchen']
    for ax,(field,title) in zip(axes,[('gpu_busy_change_percent','Process GPU busy'),('mean_image_mse_change_percent','MSE of 64-frame mean'),('hdr_flip_change_percent','Frame 64 HDR-FLIP')]):
        vals=[x[field] for x in rows]
        ax.barh(range(6),vals,color=['#197c75' if x<0 else '#ae593d' for x in vals],height=.6)
        ax.axvline(0,color='#4e5863',linewidth=.8);ax.axhline(2.5,color='#8c969e',linewidth=.8,linestyle=':')
        pad=max(abs(x) for x in vals)*.18
        for i,x in enumerate(vals):ax.text(x+pad*.12 if x>=0 else x-pad*.12,i,f'{x:+.2f}%',va='center',ha='left' if x>=0 else 'right',fontsize=9)
        ax.set_xlim(min(0,min(vals))-pad*2.8,max(0,max(vals))+pad*1.8);ax.set_title(title,fontsize=11);ax.set_xlabel('Change from that experiment’s control (%)')
        ax.grid(axis='x',alpha=.18);ax.set_axisbelow(True)
    axes[0].set_yticks(range(6),labels);axes[0].invert_yaxis()
    fig.suptitle('Local measured tradeoffs — lower is better',fontsize=14)
    fig.supxlabel('Separate studies and controls • 3 seeds / 64 static frames; timing: 3 uncapped processes • point estimates, not confidence intervals',fontsize=9)
    fig.savefig(out/'measured-tradeoffs.svg',metadata={'Date':'2026-10-30','Creator':'Matplotlib'})
    if a.preview_dir:a.preview_dir.mkdir(parents=True,exist_ok=True);fig.savefig(a.preview_dir/'measured-tradeoffs.png',dpi=140)
    plt.close(fig)
    oracle=read('2026-10-30-unified-ris-oracle/results.json')
    case=next(x for x in oracle['rows'] if x['candidates']==2)
    def value(key):return case[key]['numerator']/case[key]['denominator']
    keys=['combined','stale_bsdf_mis','missing_conversion'];values=[value(k) for k in keys]
    assert values[0]==value('reference')==20 and values[1]!=20 and values[2]!=20
    fig,ax=plt.subplots(figsize=(8.8,2.8),layout='constrained')
    ax.barh(range(3),values,color=['#197c75','#ae593d','#ae593d'],height=.55)
    ax.axvline(20,color='#394958',linestyle='--',linewidth=1,label='Exact reference = 20')
    ax.set_yticks(range(3),['Consistent MIS + PSS conversion','Stale BSDF companion weight','Missing PSS conversion factor']);ax.invert_yaxis()
    for i,x in enumerate(values):ax.text(x+.7,i,f'{x:.2f}',va='center')
    ax.set_xlim(0,max(values)*1.14);ax.set_xlabel('Exact expected estimate (arbitrary units)');ax.set_title('Calculated prerequisite: two NEE candidates, three-element domain',fontsize=12);ax.legend(loc='upper right',fontsize=8)
    fig.savefig(out/'exact-estimator-check.svg',metadata={'Date':'2026-10-30','Creator':'Matplotlib'})
    if a.preview_dir:fig.savefig(a.preview_dir/'exact-estimator-check.png',dpi=140)
    plt.close(fig)
    # Vector schematic: conceptual ownership, not measured performance.
    svg='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 365" role="img" aria-labelledby="t d">
<title id="t">Current split ownership and full PT++ target</title><desc id="d">B8 assigns direct lighting to DI, short indirect paths to GI and long indirect paths to ReSTIR PT. Full B10 targets one PT reservoir over all these paths. The B10 target remains unimplemented.</desc>
<defs><marker id="arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0 0 L7 3.5 L0 7" fill="#526a7c"/></marker></defs>
<rect width="1000" height="365" rx="14" fill="#f7fafc"/>
<g font-family="system-ui,sans-serif" fill="#20354b"><text x="30" y="34" font-size="22" font-weight="650">Lighting ownership: reuse must count each path once</text>
<rect x="25" y="55" width="460" height="265" rx="12" fill="#e7f1f3" stroke="#a3bdc4"/><rect x="515" y="55" width="460" height="265" rx="12" fill="#fff0dc" stroke="#c7ac87"/>
<text x="45" y="86" font-size="19" font-weight="650">B8 control · scoped GPU implementation</text><text x="535" y="86" font-size="19" font-weight="650">Full B10 target · not yet implemented</text>
<g fill="white" stroke="#91a9b4"><rect x="45" y="110" width="270" height="44" rx="7"/><rect x="45" y="173" width="270" height="44" rx="7"/><rect x="45" y="236" width="270" height="44" rx="7"/><rect x="365" y="173" width="95" height="44" rx="7"/>
<rect x="535" y="112" width="420" height="44" rx="7"/><rect x="535" y="181" width="420" height="44" rx="7"/><rect x="535" y="250" width="420" height="44" rx="7"/></g>
<g font-size="17" text-anchor="middle"><text x="180" y="138">DI → direct lighting</text><text x="180" y="201">GI → short indirect paths</text><text x="180" y="264">ReSTIR PT → long indirect paths</text><text x="412" y="201">Pixel sum</text>
<text x="745" y="140">NEE + BSDF proposals · all path lengths</text><text x="745" y="209">One PT reservoir · temporal + spatial reuse</text><text x="745" y="278">Unified shading · standalone DI/GI replaced</text></g>
<g stroke="#526a7c" fill="none" stroke-width="2" marker-end="url(#arrow)"><path d="M315 132 H340 V185 H364"/><path d="M315 195 H364"/><path d="M315 258 H340 V207 H364"/><path d="M745 157 V179"/><path d="M745 226 V248"/></g>
<text x="30" y="345" font-size="16">Conceptual diagram • split support / MIS on the left; paper §6.1 and supplement §§1/5 on the right.</text></g></svg>'''
    (out/'lighting-ownership.svg').write_text(svg,encoding='utf-8')
    receipt=dict(date='2026-10-30',scope='Existing measured evidence and exact finite-domain calculation; no new simulation or GPU acquisition',inputs=inputs,measured_rows=rows,oracle=dict(candidates=2,reference=20,values=dict(zip(keys,values))),outputs={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.glob('*.svg'))})
    (out/'figure-data.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(figures=3,measured_rows=len(rows),new_gpu_runs=0)))

if __name__=='__main__':main()
