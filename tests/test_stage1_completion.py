"""Independently verify completed scientific evidence without repeating solves."""
from certmorse.completion_checks import completion_checks, probe_checks


def test_section_6_2_saved_oracles_and_multiplicity():
    report = completion_checks()
    assert report['status'] == 'PASS'
    assert sum(row['oracle_bands'] for row in report['instances'].values()) == 60
    assert sum(row['sampled_bands'] for row in report['instances'].values()) == 30


def test_section_6_3_saved_timeout_probes():
    report = probe_checks()
    assert report['status'] == 'PASS' and report['bands'] == 7
