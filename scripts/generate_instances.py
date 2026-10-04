"""One-off generation of the committed D1/D12 instance data."""
from pathlib import Path
import numpy as np
import networkx as nx
import yaml

definitions=[('R6a',6,1001,'regular',False),('R6b',6,1002,'regular',False),('R8a',8,1003,'regular',False),('R8b',8,1004,'regular',False),('R8c',8,1005,'regular',False),('R10a',10,1006,'regular',False),('E8a',8,1007,'er',False),('E8b',8,1008,'er',False),('W8a',8,1009,'regular',True),('W8b',8,1010,'regular',True),('C8',8,1011,'cycle',False),('K5',5,1012,'complete',False)]
data={}
for name,n,seed,kind,weighted in definitions:
    current=seed
    while True:
        graph=nx.random_regular_graph(3,n,current) if kind=='regular' else nx.gnp_random_graph(n,.5,current) if kind=='er' else nx.cycle_graph(n) if kind=='cycle' else nx.complete_graph(n)
        if nx.is_connected(graph): break
        current+=1000
    edges=sorted(tuple(sorted(e)) for e in graph.edges())
    data[name]={'n':n,'seed':seed,'edges':[list(e) for e in edges], 'weights':np.random.default_rng(seed).integers(1,4,len(edges)).tolist() if weighted else [1]*len(edges), 'offsets':np.random.default_rng(seed+2000).uniform(-.1,.1,len(edges)).tolist()}
isomorphic=nx.is_isomorphic(nx.Graph(data['R6a']['edges']),nx.Graph(data['R6b']['edges']))
Path('configs').mkdir(exist_ok=True)
Path('configs/instances.yaml').write_text(f'# R6a/R6b isomorphic: {isomorphic}; retained per section 6.1.\n'+yaml.safe_dump(data,sort_keys=False),encoding='utf8')
