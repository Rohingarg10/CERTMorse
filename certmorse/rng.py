import numpy as np


def streams(seed):
    return {name:np.random.default_rng(child) for name,child in zip(('land','opt','fc','alloc'),np.random.SeedSequence(seed).spawn(4))}


def restart_streams(seed,R):
    child=np.random.SeedSequence(seed).spawn(4)[1]
    return [np.random.default_rng(c) for c in child.spawn(R)]
