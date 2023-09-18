import logging

import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm, poisson

from .Container import Container

logger = logging.getLogger(__name__)


class OverflowModel:
    """
    A class implementing a self-adjusting CDF of the overflow probability.
    Estimation is based on (# arrivals, overflow yes/no) data points. We
    fit a function to this data, which in turn is used to estimate the
    overflow probability.

    Parameters
    ----------
    container
        Container whose arrival behaviour we are trying to model here.
    deposit_volume
        Estimated volume of a single deposit. Used to determine initial
        parameters when no data is yet available.
    """

    def __init__(
        self,
        container: Container,
        deposit_volume: float,
        bounds: tuple[tuple[float, float], ...] = ((1, 100), (1, 30)),
    ):
        self.container = container
        self.deposit_volume = deposit_volume
        self.bounds = bounds

        self.data = np.empty((0, 2))
        self.x = np.mean(self.bounds, axis=1)

    def prob(
        self, num_arrivals: float, rate: float = 0.0, tol: float = 1e-3
    ) -> float:
        """
        Estimates the probability of overflow given a known number of arrivals
        and an arrival rate for future arrivals.

        Parameters
        ----------
        num_arrivals
            Known number of arrivals since last service.
        rate
            Poisson arrival rate of future arrivals. Defaults to zero, in which
            case there is no evaluation of future arrivals, and only the
            probability of overflow at the current number of known arrivals is
            evaluated.
        tol
            Used to cut-off the future arrivals. We evaluate arrivals in {0,
            ..., k}, where k is determined as ppf(1 - tol) of the appropriate
            Poisson distribution. Default 0.001.
        """
        cap = self.container.capacity
        N = self.data[:, 0]
        Y = self.data[:, 1]

        def p(n, mu, sigma):
            # Returns the probability that the container has *not* overflowed
            # after n arrivals, given mean mu and stddev sigma.
            return norm.cdf((cap - n * mu) / (sigma * np.sqrt(n) + tol))

        def loglik(x):
            # Evaluates -loglikelihood of parameters x given the data N and Y.
            # We impose some clipping on the probabilities to avoid numerical
            # issues evaluating the logarithms.
            prob = np.clip(p(N, *x), tol, 1 - tol)
            return -np.sum(Y * np.log(prob) + (1 - Y) * np.log(1 - prob))

        res = minimize(loglik, self.x, bounds=self.bounds)
        self.x = res.x

        return sum(
            # Expected overflow probability based on estimates (p) and the
            # arrival of additional deposits.
            (1 - p(num_arrivals + cnt, *self.x)) * poisson.pmf(cnt, mu=rate)
            for cnt in range(int(poisson.ppf(1 - tol, mu=rate) + 1))
        )

    def observe(self, x: int, y: bool):
        logger.debug(f"{self.container.name}: observing ({x}, {y}).")
        self.data = np.vstack([self.data, [x, y]])
