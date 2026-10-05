from dataclasses import dataclass
from pathlib import Path
import numpy as np
import networkx as nx
import yaml


@dataclass
class Instance:
    id: str
    n: int
    edges: list[tuple[int,int]]
    weights: list[int]
    W: int
    offsets: list[float]
    gamma_symmetry: str
    copies: int


def load_instance(instance_id,path='configs/instances.yaml'):
    data=yaml.safe_load(Path(path).read_text(encoding='utf8'))[instance_id]
    edges=[tuple(e) for e in data['edges']]
    weights=list(data['weights'])
    return Instance(instance_id,int(data['n']),edges,weights,sum(weights),list(data['offsets']),
                    data['gamma_symmetry'],int(data['copies']))


def cost_values(inst):
    idx=np.arange(2**inst.n,dtype=np.int64)
    return sum((w*(((idx>>a)^(idx>>b))&1) for (a,b),w in zip(inst.edges,inst.weights)),np.zeros(len(idx),dtype=float))


def maxcut_closed_form(inst,gammas,betas):
    if any(w!=1 for w in inst.weights): raise ValueError('closed form requires unit weights')
    gamma,beta=np.meshgrid(np.asarray(gammas),np.asarray(betas),indexing='xy')
    graph=nx.Graph(inst.edges)
    result=np.zeros_like(gamma)
    for u,v in inst.edges:
        d,e=graph.degree(u)-1,graph.degree(v)-1
        f=len(set(graph[u])&set(graph[v]))
        result-=.5+.25*np.sin(4*beta)*np.sin(gamma)*(np.cos(gamma)**d+np.cos(gamma)**e)-.25*np.sin(2*beta)**2*np.cos(gamma)**(d+e-2*f)*(1-np.cos(2*gamma)**f)
    return result


def independent_landscape(inst,gamma,beta,channel='a'):
    """Independent NumPy diagonal phase and bitwise tensor mixer (T2b)."""
    cost=cost_values(inst)
    idx=np.arange(len(cost))
    phase=-gamma*cost
    if channel in ('d','d0'):
        offsets=inst.offsets if channel=='d' else [.05]*len(inst.edges)
        for (u,v),offset in zip(inst.edges,offsets):
            phase-=offset*(1-2*(((idx>>u)^(idx>>v))&1))/2
    psi=np.exp(1j*phase)/np.sqrt(len(cost))
    c,s=np.cos(beta),-1j*np.sin(beta)
    for q in range(inst.n):
        zero=idx[((idx>>q)&1)==0];one=zero|(1<<q)
        a,b=psi[zero].copy(),psi[one].copy()
        psi[zero],psi[one]=c*a+s*b,s*a+c*b
    return -float(np.abs(psi)**2@cost)
