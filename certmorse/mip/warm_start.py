"""TTK simplified candidate; feasibility is decided by the integer witness."""
import numpy as np
from ..ttk import execute
from ..complex import lower_star_gradient
from ..forman import witness, NegativeCycle


def simplified_hint(input_vtu,output_csv,threshold,cell_lo,cell_hi,cx):
    execute('simplify',input_vtu,output_csv,'--threshold',threshold)
    data=np.loadtxt(output_csv,delimiter=',',skiprows=1)
    if data.shape!=(cx.nv,2) or not np.all(np.isfinite(data)):
        raise ValueError('expected finite Scalar and Scalar_Order for every vertex')
    field,offset=data.T
    if len(np.unique(offset))!=cx.nv: raise ValueError('TTK ordering must be a total order')
    # Core ties stay (value,index). A unique rank surrogate realizes the
    # TTK lexicographic scalar/offset order; only ordering drives lower stars.
    ordered=np.lexsort((offset,field))
    rank=np.empty(cx.nv,dtype=np.int64);rank[ordered]=np.arange(cx.nv)
    ve,et=lower_star_gradient(rank,cx)
    values=witness(ve,et,cell_lo,cell_hi,cx)
    if isinstance(values,NegativeCycle): return None,'rejected_infeasible'
    return dict(x=values,y=np.concatenate((ve,et)),ordering='TTK Scalar,Scalar_Order'),'accepted'
