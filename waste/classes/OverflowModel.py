import logging

import numpy as np
from scipy import sparse

from .Container import Container

logger = logging.getLogger(__name__)


class OverflowModel:
    """
    A class implementing a self-adjusting CDF of the overflow probability.
    Estimation is based on censored overflow data, with a CDF fitted using the
    Turnbull procedure. Additionally, some linear interpolation is used between
    observations to ensure some smoothing.

    Parameters
    ----------
    container
        Container whose arrival behaviour we are trying to model here.
    deposit_volume
        Estimated volume of a single deposit. Used to determine initial
        parameters when no data is yet available.
    """

    def __init__(self, container: Container, deposit_volume: float):
        self.container = container
        self.deposit_volume = deposit_volume

        self.data = np.empty((0, 2))

    def prob(self, num_arrivals: float) -> float:
        if len(self.data) >= 5:
            # Once we have at least five observations, we switch to a
            # non-parametric estimate of the CDF based on the Turnbull
            # procedure.
            xp, fp = turnbull(self.data)
        else:
            # Initially we just use a simple rule of thumb.
            xp = [0, self.container.capacity / self.deposit_volume]
            fp = [0, 1]

        # Linearly interpolate between given observations. Outside known
        # observations, we return 0 for values below the smallest observed
        # x (probably not full), and 1 for values above the largest observed
        # x (probably full).
        return np.interp(num_arrivals, xp, fp, left=0, right=1)

    def observe(self, x: int, y: bool):
        logger.debug(f"{self.container.name}: observing ({x}, {y}).")

        # We store the censoring interval of the given observation. If we
        # observe an overflow (y is True), then that overflow happened between
        # [0, x] (right censored). If y is False, then overflow would have
        # happened between [x, inf] (right censored).
        row = [0 if y else x, x if y else np.inf]
        self.data = np.vstack([self.data, row])


# The Turnbull code below is adapted slightly from that of the SurPyval package
# (commit hash 84bf5a1), released under the following MIT license.
#
# Copyright (c) 2020 Derryn Knife
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


def turnbull(x):
    # Find all unique bounding points in sorted order
    bounds = np.sort(np.unique(x))

    # Unpack x array
    xl = x[:, 0]
    xr = x[:, 1]

    # Find the count of intervals (M) and unique observation windows (N)
    M = bounds.size
    N = xl.size

    alpha = sparse.dok_matrix((N, M), dtype="int32")

    for i in range(0, N):
        x1, x2 = xl[i], xr[i]
        if x2 == np.inf:
            alpha[i, :] = ((bounds > x1) & (bounds <= x2)).astype(int)
        else:
            alpha[i, :] = ((bounds >= x1) & (bounds < x2)).astype(int)

    d = np.zeros(M)
    p = np.ones(M) / M

    iters = 0
    p_prev = np.zeros_like(p)

    old_err_state = np.seterr(all="ignore")
    expected = sparse.dok_matrix(alpha.shape, dtype="float64")

    while iters < 100 and not np.allclose(p, p_prev, rtol=1e-4, atol=1e-4):
        p_prev = p
        iters += 1
        # TODO: Change this so that it does row iterations on sparse matrices
        # Row wise should, in the majority of cases, be more memory efficient
        denominator = np.zeros(N)

        for (i, j), v in zip(alpha.keys(), alpha.values()):
            denominator[i] += v * p[j]
            expected[i, j] = v**2 * p[j]

        d_observed = np.array(
            expected.multiply(1 / denominator[:, np.newaxis]).sum(0)
        ).ravel()

        d_ghosts = np.zeros(M)

        # Deaths/Failures/Events
        d = d_ghosts + d_observed
        # total observed and unobserved failures.
        total_events = (d_ghosts + d_observed).sum()
        # Risk set, i.e the number of items at risk at immediately before x
        r = total_events - d.cumsum() + d
        # Find the survival function values (R) using the deaths and risk set
        # The 'official' way to do it, which is equivalent to using KM,
        # is to do p = (nu + mu).sum(axis=0)/(nu + mu).sum()
        R = fh(r, d)
        # Calculate the probability mass in each interval
        p = np.abs(np.diff(np.hstack([[1], R])))
        expected.clear()

    np.seterr(**old_err_state)

    # The survival function estimate is not unique: any estimate between the
    # upper and lower bounds satisfies the optimal log-likelihood. We take the
    # middle between these bounds, and return the CDF.
    upper = R[0:-2]
    lower = R[1:-1]
    return bounds[1:-1], 1 - np.mean([lower, upper], axis=0)


def fh_h(r_i, d_i):
    out = 0
    while d_i > 1:
        out += 1.0 / r_i
        r_i -= 1
        d_i -= 1
    out += d_i / r_i
    return out


def fh(r, d):
    Y = np.array([fh_h(r_i, d_i) for r_i, d_i in zip(r, d)])
    H = Y.cumsum()
    H[np.isnan(H)] = np.inf
    return np.exp(-H)
