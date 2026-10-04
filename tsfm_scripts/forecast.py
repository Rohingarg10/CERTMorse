"""Stage 1 TimesFM file boundary and smoke test; no trajectory experiments."""
import argparse
import json
import os
from pathlib import Path
import time
import numpy as np

CHECKPOINT = 'google/timesfm-3.0-pytorch'


def validate(context, covariates, mode):
    context = np.asarray(context, dtype=np.float32)
    if context.ndim != 1 or not len(context) or not np.all(np.isfinite(context)):
        raise ValueError('context must be a finite nonempty vector')
    if mode not in ('exact', 'shots'):
        raise ValueError('mode must be exact or shots')
    if covariates is not None:
        covariates = np.asarray(covariates, dtype=np.float32)
        shape = (3 if mode == 'exact' else 2, len(context))
        if covariates.shape != shape or not np.all(np.isfinite(covariates)):
            raise ValueError(f'{mode} covariates must have shape {shape}')
    return context, covariates


def load_model():
    import torch
    from timesfm3 import TimesFM3Evaluator, ModelConfig
    torch.set_num_threads(8)
    return TimesFM3Evaluator(ModelConfig(
        checkpoint_path=CHECKPOINT, per_core_batch_size=32, device='cpu',
        local_files_only=True, cache_dir=str(Path(os.environ['HF_HOME'])/'hub')))


def predict(model, contexts, covariates, horizon, mode):
    if horizon < 1 or len(contexts) != len(covariates):
        raise ValueError('positive horizon and one covariate array per context required')
    checked = [validate(c, cov, mode) for c, cov in zip(contexts, covariates)]
    outputs = list(model.predict_batch(
        contexts=[c for c, _ in checked], horizon=horizon,
        past_only_covariates=[cov for _, cov in checked], return_quantiles=True,
        use_symmetric_averaging=False, make_positive=False))
    for out in outputs:
        if out.forecast.shape != (horizon,) or out.quantiles.shape != (horizon, 9):
            raise RuntimeError('unexpected TimesFM output shape')
        if not np.all(np.isfinite(out.quantiles)):
            raise RuntimeError('nonfinite TimesFM output')
    return np.stack([o.forecast for o in outputs]), np.stack([o.quantiles for o in outputs])


def smoke(output):
    started = time.perf_counter()
    model = load_model()
    load_s = time.perf_counter() - started
    ctx = np.exp(-np.arange(40, dtype=np.float32)/12) + .1
    cov = np.vstack((ctx*.3, np.linspace(0, 1, 40), np.ones(40))).astype(np.float32)
    first = predict(model, [ctx], [cov], 80, 'exact')
    second = predict(model, [ctx], [cov], 80, 'exact')
    assert all(np.array_equal(a, b) for a, b in zip(first, second))
    predict(model, [ctx], [cov[:2]], 80, 'shots')
    for mode, bad in [('exact', cov[:2]), ('shots', cov), ('exact', cov[:, :-1])]:
        try:
            validate(ctx, bad, mode)
        except ValueError:
            continue
        raise AssertionError('invalid covariate shape accepted')
    times = []
    for _ in range(3):
        started = time.perf_counter()
        predict(model, [ctx]*64, [cov]*64, 80, 'exact')
        times.append(time.perf_counter()-started)
    report = dict(checkpoint=CHECKPOINT, device='cpu', threads=8, T17='passed',
                  model_load_s=load_s, batch64_k40_h80_s=times,
                  batch64_median_s=float(np.median(times)))
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps(report))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--in', dest='input')
    parser.add_argument('--out', required=True)
    parser.add_argument('--mode', choices=['exact', 'shots'], default='exact')
    parser.add_argument('--horizon', type=int, default=80)
    parser.add_argument('--smoke', action='store_true')
    args = parser.parse_args()
    if args.smoke:
        smoke(args.out)
    else:
        with np.load(args.input, allow_pickle=False) as data:
            contexts = data['context']
            contexts = contexts[None, :] if contexts.ndim == 1 else contexts
            covs = data['covariates'] if 'covariates' in data else None
            if covs is not None and covs.ndim == 2:
                covs = covs[None, :, :]
            point, quantiles = predict(load_model(), list(contexts),
                [None]*len(contexts) if covs is None else list(covs), args.horizon, args.mode)
        np.savez_compressed(args.out, forecast=point, quantiles=quantiles, checkpoint=CHECKPOINT)
