import logging

import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm

from .Cluster import Cluster

logger = logging.getLogger(__name__)


class OverflowModel:
    """
    A class implementing a self-adjusting CDF of the overflow probability.
    Estimation is based on (# arrivals, overflow yes/no) data points. We
    fit a function to this data, which in turn is used to estimate the
    overflow probability.

    Parameters
    ----------
    cluster
        Cluster whose arrival behaviour we are trying to model here.
    bounds
        Bounds on the mean and standard deviation.
    """

    def __init__(
        self,
        cluster: Cluster,
        bounds: tuple[tuple[float, float], ...] = ((1, 100), (1, 50)),
    ):
        self.cluster = cluster
        self.bounds = bounds

        self.data = np.empty((0, 2))
        self.x = np.mean(self.bounds, axis=1)

    def prob_arrivals(
        self,
        num_arrivals: float,
        rate: float = 0.0,
        tol: float = 1e-3,
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
            Used to clip probabilities to (tol, 1 - tol). This is needed to
            avoid numerical issues when evaluating the log-likelihood. Default
            0.001.
        """
        self._update_estimates(tol)  # update x

        # Expected overflow probability based on estimates (p) and the arrival
        # of additional deposits.
        mean = (num_arrivals + rate) * self.x[0]
        var = (num_arrivals + rate) * self.x[1] ** 2 + rate * self.x[0] ** 2
        return norm.sf(
            self.cluster.capacity,
            loc=mean,
            scale=np.sqrt(var + tol),
        )

    def prob_volume(
        self,
        known_volume: float = 0.0,
        rate: float = 0.0,
        tol: float = 1e-3,
    ) -> float:
        """
        Estimates the probability of overflow given a known volume and an
        arrival rate for future arrivals.

        Parameters
        ----------
        known_volume
            Known volume in the cluster.
        rate
            Poisson arrival rate of future arrivals. Defaults to zero, in which
            case there is no evaluation of future arrivals, and only the
            probability of overflow at the current number of known arrivals is
            evaluated.
        tol
            Used to clip probabilities to (tol, 1 - tol). This is needed to
            avoid numerical issues when evaluating the log-likelihood. Default
            0.001.
        """
        if self.cluster.capacity <= known_volume:
            # Then the cluster is guaranteed to be full and should be serviced.
            return 1.0

        self._update_estimates(tol)  # update x

        # When we have a known volume that is non-zero, there is no uncertainty
        # due to the known number of arrivals any more. Hence, we only need to
        # know the probability that the cluster will overflow due to the
        # arrival of additional deposits.
        mean = rate * self.x[0]
        var = rate * self.x[1] ** 2 + rate * self.x[0] ** 2
        return norm.sf(
            self.cluster.capacity - known_volume,
            loc=mean,
            scale=np.sqrt(var + tol),
        )

    def observe(self, x: int, y: bool):
        logger.debug(f"{self.cluster.name}: observing ({x}, {y}).")
        self.data = np.vstack([self.data, [x, y]])

    def _update_estimates(self, tol: float):
        N = self.data[:, 0]
        Y = self.data[:, 1]

        def overflow_prob(n, mu, sigma):
            # Returns the probability that the cluster has overflowed after n
            # arrivals, given mean mu and stddev sigma.
            return norm.sf(
                self.cluster.capacity,
                loc=n * mu,
                scale=sigma * np.sqrt(n) + tol,
            )

        def loss(x):
            # Evaluates -loglikelihood of parameters x given the data N and Y.
            # We impose some clipping on the probabilities to avoid numerical
            # issues evaluating the logarithms.
            prob = np.clip(overflow_prob(N, *x), tol, 1 - tol)
            return -np.sum(Y * np.log(prob) + (1 - Y) * np.log(1 - prob))

        res = minimize(loss, self.x, bounds=self.bounds)
        self.x = res.x
