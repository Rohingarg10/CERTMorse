"""A three-band restart integration driver; ordinary Stage 1 uses the same units."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np

from certmorse.instances import load_instance, cost_values
from certmorse.landscape import exact_landscape, sample_landscape, make_band
from certmorse.raw import solve_band, sample_band, write_json, save_arrays
from certmorse.rng import streams
from certmorse.units import Unit


def run(root, grid_m=4, bands=3):
    instance = load_instance('R8a')
    field = Unit('landscape', dict(instance='R8a', grid_m=grid_m, noise='a', field_seed=1003), root=root)
    def generate(work):
        truth, variance, probs = exact_landscape(instance, grid_m, 'a', 1003)
        save_arrays(work/'field.npz', -1, truth=truth, variance=variance, probs=probs)
    field_folder = field.run(generate)
    with np.load(field_folder/'field.npz') as data:
        truth, variance, probs = data['truth'], data['variance'], data['probs']
    for seed in range(bands):
        band = Unit('landscape', dict(instance='R8a', grid_m=grid_m, noise='a', seed=seed, shots=1000,
                                     alpha=.05, band_mode='oracle'), {'field': field_folder/'field.npz'}, root=root)
        def generate_band(work):
            mean, sample_variance = sample_landscape((probs, cost_values(instance)), 1000, streams(seed)['land'])
            lower, upper = make_band(mean, variance, sample_variance, 1000, instance.W, .05, 'oracle')
            save_arrays(work/'band.npz', -1, truth=truth, mean=mean, lower=lower, upper=upper)
        band_folder = band.run(generate_band)
        solved = solve_band(band_folder/'band.npz', dict(grid_m=grid_m, seed=seed, instance='R8a', band_mode='oracle', warm_start=False), root=root)
        sampled = sample_band(solved, dict(grid_m=grid_m, seed=seed), root=root)
        print(f'seed={seed} solve={solved.name} sample={sampled.name}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--grid-m', type=int, default=4)
    parser.add_argument('--bands', type=int, default=3)
    args = parser.parse_args()
    run(args.root, args.grid_m, args.bands)
