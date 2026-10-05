"""Exact reproduction must succeed before new v1.8.4 columns are written."""
from certmorse.legacy_scores import verify_T38


def test_T38_every_saved_optimum_and_sample_is_reproduced_exactly():
    result = verify_T38()
    assert result['status'] == 'PASS' and result['exact_equality']
    assert result['primary_folders'] == 80
    assert result['optimal_bands'] == 73
    assert result['sidecar_folders'] == 6
