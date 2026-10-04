"""Export a scientific figure from the saved first R8a optimal solve."""
import json
from pathlib import Path
import sys
import os
os.environ.setdefault('MPLCONFIGDIR',str(Path(__file__).resolve().parents[1]/'.tools'/'matplotlib'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from certmorse.complex import TorusComplex,basins

paths=sorted(Path('results/stage1-r8a').glob('*/measurement.json'))
records=[json.loads(path.read_text()) for path in paths]
index=min(range(len(records)),key=lambda i:records[i]['seed'])
path=paths[index].parent
data=np.load(path/'matching.npz')
cx=TorusComplex(16)
ve,_=cx.split_matching(data['y'])
labels=basins(ve,cx).reshape(16,16)
fig,axes=plt.subplots(1,3,figsize=(12,3.6),constrained_layout=True)
for ax,array,title in zip(axes,[data['truth'],data['mean'],labels],['Exact R8a field','Shot mean, N = 1000','Basins of one optimal matching']):
    image=ax.imshow(array,origin='lower',extent=[0,2*np.pi,0,np.pi],aspect='auto',cmap='viridis' if ax!=axes[2] else 'tab20')
    ax.set(title=title,xlabel='gamma',ylabel='beta')
    if ax!=axes[2]: fig.colorbar(image,ax=ax,label='negative expected cut')
fig.suptitle('Stage 1: a proven critical count; basin locations are predictions',fontsize=12)
output=Path('docs/figures');output.mkdir(parents=True,exist_ok=True)
fig.savefig(output/'r8a-stage1.png',dpi=180);fig.savefig(output/'r8a-stage1.svg');plt.close(fig)
sampled=[r for r in records if r['n_opt_found']>0]
sampled.sort(key=lambda r:r['seed'])
fig,ax=plt.subplots(figsize=(7,3.8),constrained_layout=True)
seeds=[r['seed'] for r in sampled]
mid=np.array([r['P_med'] for r in sampled])
ax.errorbar(seeds,mid,yerr=[mid-np.array([r['P_lo'] for r in sampled]),np.array([r['P_hi'] for r in sampled])-mid],fmt='o',capsize=5)
ax.set(xlabel='Band seed',ylabel='Predicted union basin area',ylim=(0,1.03),title='Observed spread across 20 optimal matchings per band')
ax.grid(alpha=.2)
fig.savefig(output/'basin-spread.png',dpi=180);fig.savefig(output/'basin-spread.svg')
