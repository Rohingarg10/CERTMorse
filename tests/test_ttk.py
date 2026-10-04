import csv
import os
import numpy as np
import pytest
from certmorse.complex import TorusComplex, lower_star_gradient
from certmorse.export_vtk import export_complex
from certmorse.ttk import execute, read_diagram, read_mandatory
from certmorse.persistence import persistence, lower_star_values, bottleneck
from certmorse.scaling import choose_scale, model_band, cell_band
from certmorse.mip import build_A, solve

pytestmark = [pytest.mark.ttk, pytest.mark.skipif(not os.environ.get('CERTMORSE_PVPYTHON'), reason='source scripts/env.ps1 to configure TTK')]


def smooth(cx, rng):
    v = np.arange(cx.nv)
    gamma, beta = 2*np.pi*(v%cx.m)/cx.m, 2*np.pi*(v//cx.m)/cx.m
    return sum(rng.normal()*np.cos(a*gamma+b*beta+rng.uniform(0,2*np.pi)) for a,b in [(1,0),(0,1),(1,1),(2,0),(0,2),(2,1)])


def test_T6_T24_twenty_smooth_fields(tmp_path):
    cx = TorusComplex(16)
    rng = np.random.default_rng(1024)
    for seed in range(20):
        g = smooth(cx, rng)
        vtu = tmp_path/f'{seed}.vtu'
        export_complex(cx, vtu, {'Scalar':g,'Lower':g-.01,'Upper':g+.01})
        csv_path = tmp_path/f'{seed}-critical.csv'
        execute('critical_points',vtu,csv_path)
        with open(csv_path,newline='') as stream:
            dims = [int(row['dim']) for row in csv.DictReader(stream)]
        a,b = lower_star_gradient(g,cx)
        y = np.concatenate((a,b))
        matched = np.bincount(cx.pairs[y.astype(bool)].ravel(),minlength=cx.nc)>0
        assert [dims.count(q) for q in (0,1,2)] == [int(np.sum(~matched[cx.dim==q])) for q in (0,1,2)]
        csv_path = tmp_path/f'{seed}-diagram.csv'
        execute('persistence',vtu,csv_path)
        exact = persistence(lower_star_values(g,cx),cx,1)
        ttk = read_diagram(csv_path)
        assert bottleneck(exact,ttk)<1e-9
        assert [np.sum(np.isinf(ttk[q][:,1])) for q in (0,1,2)]==[1,2,1]
        scale,_ = choose_scale(g-.01,g+.01)
        lo,hi = cell_band(*model_band(g-.01,g+.01,scale),cx)
        result = solve(build_A(lo,hi,cx),'cpsat',60,8,None,str(tmp_path/f'{seed}.log'))
        assert result.status=='OPTIMAL'
        certified = persistence(result.x,cx,scale)
        essential = sum(int(np.sum(np.isinf(d[:,1]))) for d in certified.values())
        finite = sum(int(np.sum(np.isfinite(d[:,1]))) for d in certified.values())
        assert essential==4
        assert 2*finite+essential<=result.kappa_opt


def test_T7_mandatory_near_zero(tmp_path):
    cx=TorusComplex(16)
    g=smooth(cx,np.random.default_rng(1007))
    vtu=tmp_path/'mandatory.vtu'
    export_complex(cx,vtu,{'Scalar':g,'Lower':g-1e-9,'Upper':g+1e-9})
    output=tmp_path/'mandatory.csv'
    execute('mandatory',vtu,output)
    counts,labels=read_mandatory(output)
    a,_=lower_star_gradient(g,cx)
    matched_vertices=cx.pairs_ve[a.astype(bool),0]
    assert counts['MinimumComponents']==cx.nv-len(matched_vertices)
    assert all(len(values)==cx.nv for values in labels.values())
