"""Sole parameter/index conversions for QAOA grids (v1.8.3 section 5)."""
import numpy as np

GRID_OFFSET = 0.25  # v1.8 section 4.2; synthetic callers cancel it per v1.8.3 section 3.
GAMMA_PERIOD = 2*np.pi  # D2


def grid_point(i, j, m, beta_period):
    """Map vertex indices to parameters; arrays and fractional indices are accepted."""
    if m < 3 or beta_period <= 0:
        raise ValueError('invalid grid or beta period')
    return (GAMMA_PERIOD*(np.asarray(i)+GRID_OFFSET)/m,
            beta_period*(np.asarray(j)+GRID_OFFSET)/m)


def grid_coords(gamma, beta, m, beta_period):
    """Inverse coordinates, unwrapped so callers can identify periodic grid cells."""
    if m < 3 or beta_period <= 0:
        raise ValueError('invalid grid or beta period')
    return (m*np.asarray(gamma)/GAMMA_PERIOD-GRID_OFFSET,
            m*np.asarray(beta)/beta_period-GRID_OFFSET)
