from pathlib import Path
import argparse,json,sys,numpy as np
ap=argparse.ArgumentParser(description='B9/B8 accumulated-mean error: mean and range across three static sequences, not equal-time convergence.');ap.add_argument('--quality',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--preview',type=Path);ap.add_argument('--plot-module-dir',type=Path);a=ap.parse_args()
if a.plot_module_dir:sys.path.insert(0,str(a.plot_module_dir.resolve()))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
q=json.loads(a.quality.read_text());plt.rcParams['svg.fonttype']='none';plt.rcParams['svg.hashsalt']='b9-on-b8'
fig,axes=plt.subplots(1,3,figsize=(13,3.8),layout='constrained')
for ax,(scene,item) in zip(axes,q['scenes'].items()):
 for version,color in [('B8','#2166ac'),('B9','#c65d16')]:
  curves=np.asarray([[x['mean_image_mse'] for x in g['curve']] for g in item['groups'].values() if g['version']==version]);assert curves.shape==(3,64) and np.isfinite(curves).all() and (curves>0).all()
  x=np.arange(1,65);ax.plot(x,curves.mean(0),label=version,color=color,linewidth=1.8);ax.fill_between(x,curves.min(0),curves.max(0),color=color,alpha=.12)
 ax.set_title(scene.capitalize()+(': footprint + RR' if scene=='room' else ': RR only'));ax.set_yscale('log');ax.set_xlabel('Frames averaged');ax.set_xlim(1,64);ax.grid(alpha=.22)
axes[0].set_ylabel('Linear RGB MSE of accumulated mean');axes[-1].legend(fontsize=9);fig.suptitle('B9 on B8: mean and range over three static sequences',fontsize=12)
a.output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(a.output,metadata=dict(Date='2026-10-30',Creator='Matplotlib'))
if a.preview:fig.savefig(a.preview,dpi=150)
plt.close(fig);print('B9 convergence figure generated.')
