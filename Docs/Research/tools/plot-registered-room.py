from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
repo=Path(__file__).resolve().parents[3];base=repo/'Benchmarks/development/2026-10-29-registered-room';q=json.loads((base/'quality-summary.json').read_text());t=json.loads((base/'comparison.json').read_text())
out=repo/'Docs/Research/assets/registered-room';out.mkdir(exist_ok=True)
colors={'B1':'#64748b','B4':'#1d9ab0','B6':'#b168c1','B7':'#de7d26'}
labels={'B1':'B1 · native PT + DI 3.0','B4':'B4 · native PT + DI 3.1','B6':'B6 · ReSTIR PT; DI off','B7':'B7 · ReSTIR PT + DI 3.1'}
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
fig,ax=plt.subplots(figsize=(9,5.8));offsets={'B1':(-24,12),'B4':(-24,-18),'B6':(8,10),'B7':(8,-18)}
for v in ['B1','B4','B6','B7']:
 g=next(g for g in q['groups'] if g['variant']==v and g['history_frames']==64);timing=t['groups'][v]
 xs=[run['metrics']['GPUBusy']['statistics']['median_ms'] for run in timing['runs']];x=timing['summary']['GPUBusy']['median_of_run_medians_ms'];y=g['median_ldr_flip'];lo,hi=g['ldr_flip_range']
 ax.errorbar(x,y,xerr=[[x-min(xs)],[max(xs)-x]],yerr=[[y-lo],[hi-y]],fmt='o',capsize=3,color=colors[v],label=labels[v],markersize=7)
 ax.annotate(v,(x,y),xytext=offsets[v],textcoords='offset points',fontsize=10,fontweight='bold')
ax.set_xlabel('Process GPU busy per frame (ms) ↓');ax.set_ylabel('LDR-FLIP versus finite 8192 spp reference ↓');ax.set_title('Registered zero-radiance room · configured-renderer comparison\n640×360, 1 spp, 3/3 bounces; actual DI settings recorded',pad=12)
ax.grid(alpha=.2);ax.margins(x=.18,y=.2);ax.legend(loc='upper center',bbox_to_anchor=(.5,-.2),ncol=2,frameon=False,fontsize=9)
fig.subplots_adjust(bottom=.28,top=.84,left=.12,right=.96)
fig.text(.12,.015,'Three runs/captures per point; ranges are min–max, not confidence intervals. Separate quality/timing episodes.\nNative: process restarts; modern: explicit seeds. GPU busy is not complete-frame critical-path latency.',fontsize=8,color='#475569')
fig.savefig(out/'cost-quality.png',dpi=160);fig.savefig(out/'cost-quality.svg');plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(10,4.5))
for v in ['B6','B7']:
 rows=sorted([g for g in q['groups'] if g['variant']==v],key=lambda g:g['history_frames']);h=[g['history_frames'] for g in rows]
 for ax,key in zip(axes,['median_linear_rgb_mse','median_hdr_flip']):
  ax.plot(h,[g[key] for g in rows],'o-',label=labels[v],color=colors[v]);ax.set_xscale('log',base=2);ax.set_xticks(h,[str(n) for n in h]);ax.set_xlabel('Requested history warm-up frames');ax.grid(alpha=.2)
axes[0].set_ylabel('Median linear RGB MSE ↓');axes[0].set_yscale('log');axes[0].set_yticks([.004,.01,.02,.04]);axes[0].yaxis.set_major_formatter(ticker.FormatStrFormatter('%.3f'));axes[0].yaxis.set_minor_formatter(ticker.NullFormatter());axes[1].set_ylabel('Median HDR-FLIP ↓');axes[1].legend(frameon=False,fontsize=9)
fig.suptitle('ReSTIR PT history settling · three-seed medians',fontsize=13);fig.subplots_adjust(left=.09,right=.98,bottom=.24,top=.83,wspace=.32)
fig.text(.09,.05,'Each point is a separate 1 spp snapshot after the stated history; no frame averaging.\nThese curves are not accumulated-spp convergence or time-to-equal-quality results. Native history curves remain unavailable.',fontsize=9,color='#475569')
fig.savefig(out/'history-settling.png',dpi=160);fig.savefig(out/'history-settling.svg');plt.close(fig)
for p in out.glob('*.svg'):p.write_text('\n'.join(line.rstrip() for line in p.read_text().splitlines())+'\n')
print('Created scientific cost/quality and history plots')
