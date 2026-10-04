"""QAOA p=1 exact distributions, pooled shot sampling, confidence bands."""
from pathlib import Path
import json
import numpy as np
from scipy.stats import norm
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import Parameter
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error, amplitude_damping_error
from .instances import load_instance, cost_values

HALF_WIDTH_FLOOR = 1e-4  # §6.1
UNIFORM_OFFSET = .05  # D12


def circuit(inst,channel):
    gamma,beta=Parameter('gamma'),Parameter('beta')
    qc=QuantumCircuit(inst.n)
    qc.h(range(inst.n))
    for e,((u,v),w) in enumerate(zip(inst.edges,inst.weights)):
        offset=inst.offsets[e] if channel in ('d','e') else UNIFORM_OFFSET if channel=='d0' else 0
        qc.rzz(-gamma*w+offset,u,v)
    qc.rx(2*beta,range(inst.n))
    return qc,gamma,beta


def noise_model(channel):
    nm=NoiseModel()
    if channel in ('b','e'):
        nm.add_all_qubit_quantum_error(depolarizing_error(1e-3,1),['sx','x'])
        nm.add_all_qubit_quantum_error(depolarizing_error(1e-2,2),['cx'])
    elif channel=='c':
        ad=amplitude_damping_error(.01)
        nm.add_all_qubit_quantum_error(ad,['sx','x'])
        nm.add_all_qubit_quantum_error(ad.tensor(ad),['cx'])
    return nm


def exact_landscape(inst,m,channel,seed):
    if m < 3: raise ValueError('grid_m must be at least 3')
    points=[(2*np.pi*i/m,np.pi*j/m) for j in range(m) for i in range(m)]
    mean,var,probs=exact_points(inst,points,channel,seed)
    return mean.reshape(m,m),var.reshape(m,m),np.ascontiguousarray(probs.reshape(m,m,-1),dtype=np.float32)


def exact_points(inst,points,channel,seed):
    if channel not in ('a','b','c','d','d0','e'): raise ValueError('unknown noise channel')
    qc,gamma,beta=circuit(inst,channel)
    tqc=transpile(qc,basis_gates=['rz','sx','x','cx'],optimization_level=1,seed_transpiler=seed)
    if channel in ('a','d','d0'):
        probs=np.array([Statevector.from_instruction(tqc.assign_parameters({gamma:g,beta:b})).probabilities() for g,b in points])
    else:
        tqc.save_density_matrix()
        simulator=AerSimulator(method='density_matrix',noise_model=noise_model(channel),max_parallel_threads=8)
        batches=[]
        for offset in range(0,len(points),32):
            batch=points[offset:offset+32]
            result=simulator.run(tqc,parameter_binds=[{gamma:[g for g,b in batch],beta:[b for g,b in batch]}],seed_simulator=seed).result()
            if not result.success: raise RuntimeError(result.status)
            batches.extend(np.real(np.diag(np.asarray(result.data(i)['density_matrix']))).copy() for i in range(len(batch)))
        probs=np.array(batches)
    normalized=np.clip(probs,0,None)
    normalized/=normalized.sum(axis=1,keepdims=True)
    if np.max(np.abs(normalized-probs).sum(axis=1))>=1e-9: raise RuntimeError('distribution renormalization exceeds tolerance')
    c=cost_values(inst)
    mean=normalized@c
    var=np.maximum(normalized@(c*c)-mean*mean,0)
    return -mean,var,normalized


def sample_landscape(F_probs_or_inst,shots,rng):
    # Explicit pair keeps the cost convention attached to saved distributions.
    probs,cost=F_probs_or_inst
    probs=np.asarray(probs,dtype=float)
    m=probs.shape[0]
    ns=np.broadcast_to(np.asarray(shots,dtype=np.int64),(m,m))
    if np.any(ns<=0): raise ValueError('shots must be positive')
    mean,var=np.empty((m,m)),np.empty((m,m))
    for j in range(m):
        for i in range(m):
            p=probs[j,i].copy();p/=p.sum()
            counts=rng.multinomial(int(ns[j,i]),p)
            mu=float(counts@cost/ns[j,i])
            mean[j,i]=-mu
            var[j,i]=max(float(counts@(cost*cost)/ns[j,i])-mu*mu,0)
    return mean,var


def make_band(mean,var_exact,var_sample,shots,W,alpha,mode,rounds_budget=1):
    mean=np.asarray(mean,dtype=float)
    ns=np.broadcast_to(np.asarray(shots,dtype=float),mean.shape)
    if np.any(ns<=0) or W<=0 or not 0<alpha<1 or rounds_budget<1: raise ValueError('invalid band parameters')
    effective=alpha/rounds_budget
    hoeffding=W*np.sqrt(np.log(2*mean.size/effective)/(2*ns))
    if mode=='hoeffding': h=hoeffding
    elif mode in ('oracle','empirical'):
        variance=np.asarray(var_exact if mode=='oracle' else var_sample)
        h=norm.ppf(1-effective/(2*mean.size))*np.sqrt(np.maximum(variance,0)/ns)
        if mode=='empirical': h=np.where((variance==0)|(ns<30),hoeffding,h)
    else: raise ValueError('unknown band mode')
    h=np.maximum(h,HALF_WIDTH_FLOOR*W)
    return np.maximum(mean-h,-W),np.minimum(mean+h,0)


def run(cfg,out_dir):
    from .rng import streams
    inst=load_instance(cfg['instance'])
    m=cfg['grid_m']
    exact,var,probs=exact_landscape(inst,m,cfg['noise'],cfg['seed'])
    mean,sample_var=sample_landscape((probs,cost_values(inst)),cfg['shots'],streams(cfg['seed'])['land'])
    lo,hi=make_band(mean,var,sample_var,cfg['shots'],inst.W,cfg['alpha'],cfg['band_mode'])
    output=Path(out_dir);output.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(output/'landscape.npz',exact=exact,mean=mean,var_exact=var,var_sample=sample_var,lower=lo,upper=hi,probs=probs,shots=np.full((m,m),cfg['shots'],dtype=np.int64),meta=json.dumps(dict(instance=inst.id,channel=cfg['noise'],W=inst.W,F_min=float(exact.min()),seed=cfg['seed'])))


def execute_run(cfg,root='results',resume=False):
    from .runid import prepare_run,default_config
    cfg=default_config(cfg)
    output,needed=prepare_run(cfg,root,resume)
    if needed:
        run(cfg,output)
        (output/'status.json').write_text(json.dumps({'complete':True,'task':'landscape'}),encoding='utf8')
    return output
