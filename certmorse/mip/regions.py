"""Proved combinatorial bound and disjoint regions, v1.8 section 4.7.

Production implementation; the prototype is neither imported nor executed.
"""
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class RegionBound:
    minimum_regions: tuple
    maximum_regions: tuple

    @property
    def LB_region(self):
        return 2*(len(self.minimum_regions)+len(self.maximum_regions))


def _regions(lower, upper, neighbours, minimum):
    components=set()
    for anchor in range(len(lower)):
        allowed=lower<=upper[anchor] if minimum else upper>=lower[anchor]
        component={anchor};queue=[anchor]
        while queue:
            v=queue.pop()
            for w in neighbours[v]:
                if allowed[w] and w not in component:
                    component.add(w);queue.append(w)
        components.add(frozenset(component))
    # In a laminar family, rejecting sets containing an already retained
    # smaller member leaves exactly the inclusion-minimal components.
    minimal=[]
    for component in sorted(components,key=lambda c:(len(c),tuple(sorted(c)))):
        if not any(other<=component for other in minimal): minimal.append(component)
    return tuple(tuple(sorted(c)) for c in minimal)


def region_bound(cell_lo,cell_hi,cx):
    lo=np.asarray(cell_lo,dtype=np.int64);hi=np.asarray(cell_hi,dtype=np.int64)
    if lo.shape!=(cx.nc,) or hi.shape!=(cx.nc,) or np.any(lo>hi):
        raise ValueError('nonempty integer cell band required')
    vertex_neighbours=[[] for _ in range(cx.nv)]
    for a,b in cx.edge_vertices:
        vertex_neighbours[a].append(int(b));vertex_neighbours[b].append(int(a))
    edge_triangles=[[] for _ in range(cx.ne)]
    for t,edges in enumerate(cx.tri_edges):
        for e in edges: edge_triangles[e].append(t)
    triangle_neighbours=[[] for _ in range(cx.nt)]
    for a,b in edge_triangles:
        triangle_neighbours[a].append(b);triangle_neighbours[b].append(a)
    start=4*cx.nv
    minima=_regions(lo[:cx.nv],hi[:cx.nv],vertex_neighbours,True)
    maxima=_regions(lo[start:],hi[start:],triangle_neighbours,False)
    return RegionBound(minima,tuple(tuple(start+t for t in region) for region in maxima))


def valid_rows(cx,regions):
    """Euler, the edge Morse inequality, and one row per minimal region.

    Vertex/triangle Morse rows are already retained from v1.7 in the emitter.
    Euler coefficients cancel identically for every matching on the D5 torus.
    """
    rows=[({},0,0),({p:1 for p in range(len(cx.pairs))},None,cx.ne-2)]
    if regions is not None:
        for family,dimension in [(regions.minimum_regions,0),(regions.maximum_regions,2)]:
            incident={int(c):[] for region in family for c in region}
            for p,(face,coface) in enumerate(cx.pairs):
                cell=int(face if dimension==0 else coface)
                if cx.dim[cell]==dimension and cell in incident: incident[cell].append(p)
            for region in family:
                rows.append(({p:1 for cell in region for p in incident[cell]},None,len(region)-1))
    return rows
