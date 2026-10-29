from pathlib import Path
import sys,json,argparse
ap=argparse.ArgumentParser(description='Plot B8 chronological accumulated-mean error; not equal-time convergence.')
ap.add_argument('--quality',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--preview',type=Path);ap.add_argument('--plot-module-dir',type=Path);a=ap.parse_args()
if a.plot_module_dir:sys.path.insert(0,str(a.plot_module_dir.resolve()))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
q=json.loads(a.quality.read_text())
fig,axes=plt.subplots(1,3,figsize=(13,3.8),layout='constrained')
for ax,(scene,groups) in zip(axes,q['groups'].items()):
 for label,g in groups.items():
  ax.plot([v['frame'] for v in g['curve']],[v['mean_image_mse'] for v in g['curve']],label='Initial GI' if g['gi_mode']<0 else 'NVIDIA GI reuse',color='#2166ac' if g['gi_mode']<0 else '#c65d16',linewidth=1.8)
 ax.set_title(scene.capitalize());ax.set_yscale('log');ax.set_xlabel('Frames averaged');ax.set_xlim(1,64);ax.grid(alpha=.22)
axes[0].set_ylabel('Linear RGB MSE of accumulated mean');axes[-1].legend(fontsize=8)
fig.suptitle('B8: error of the accumulated mean — one static sequence, seed47',fontsize=12)
plt.rcParams['svg.fonttype']='none'
out=a.output;out.parent.mkdir(parents=True,exist_ok=True);fig.savefig(out,metadata=dict(Date='2026-10-29',Creator='Matplotlib'));
if a.preview:fig.savefig(a.preview,dpi=150)
plt.close(fig)
print('B8 convergence figure created.')
