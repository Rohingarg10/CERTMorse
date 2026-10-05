"""T33 compares all three formulations on all 120 fixed bands."""
from scripts.agreement import run,passed


def test_T33_valid_rows_preserve_all_120_agreement_optima():
    rows=run([3,4,8],resume=True)
    assert len(rows)==120
    assert all(passed(row) and row['rows_preserve_optimum'] for row in rows)
