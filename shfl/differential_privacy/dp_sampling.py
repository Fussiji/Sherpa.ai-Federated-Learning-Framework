import abc
import numpy as np
from math import log
from math import exp
from scipy.special import comb
from functools import reduce
from operator import mul

from shfl.private.data import DPDataAccessDefinition


def prod(iterable):
    """
    This is a multiplicational equivalent of python sum function
    """
    return reduce(mul, iterable, 1)


array_sampler = np.random.default_rng()


class Sampler(DPDataAccessDefinition):
    """
    This class implements sampling methods which helps to reduce
    the epsilon-delta budget spent by a dp-mechanism

    # Arguments:
        sample_size: size of the sample to be taken
    """

    def __init__(self, dp_mechanism):
        self._dp_mechanism = dp_mechanism

    def apply(self, data):
        sampled_data = self.sample(data)
        return self._dp_mechanism.apply(sampled_data)

    @property
    def epsilon_delta(self):
        return self.epsilon_delta_reduction(self._dp_mechanism.epsilon_delta)

    @abc.abstractmethod
    def epsilon_delta_reduction(self, epsilon_delta):
        """
        It receives epsilon_delta parameters from a dp-mechanism
        and computes the new hopefully reduced epsilon_delta

        # Arguments:
            epsilon_delta: privacy budget provided by a dp-mechanism

        # Returns
            new_epsilon_delta: new hopefully reduced epsilon_delta
        """

    @abc.abstractmethod
    def sample(self, data):
        """
        It receives some data and returns a sample of it

        # Arguments:
            data: Raw data that are going to be sampled

        # Returns
            sampled_data: sample of size self._sample_size
        """


class SampleWithReplacement(Sampler):
    """
        It implements the sample with replacement technique (Theorem 10 from the reference) which reduces
        the epsilon-delta bugdet spent specified

        Note that it only can sample the first dimension of a ndarray.

        # Arguments:
            sample_size: one dimentional size of the sample
            data_size: shape of the input data

        # References:
            - [Privacy Amplification by Subsampling: Tight Analyses via Couplings and Divergences](https://arxiv.org/abs/1807.01647)
    """

    def __init__(self, dp_mechanism, sample_size, data_size):
        super().__init__(dp_mechanism)
        check_sample_size(sample_size, data_size)
        self._dp_mechanism = dp_mechanism
        self._data_size = data_size
        self._sample_size = sample_size
        if len(self._data_size) > 1:
            # Data with more than one dimension
            self._actual_sample_size = self._sample_size * \
                prod(self._data_size[1:])
            self._data_size = prod(self._data_size)
        else:
            # One dimensional data
            self._actual_sample_size = self._sample_size
            self._data_size = self._data_size[0]

    def sample(self, data):
        return array_sampler.choice(data, size=self._sample_size, replace=True)

    def epsilon_delta_reduction(self, epsilon_delta):
        proportion = 1 - (1 - 1 / self._data_size) ** self._actual_sample_size
        epsilon, delta = epsilon_delta

        new_epsilon = log(1 + proportion * (exp(epsilon) - 1))
        n = self._data_size
        m = self._actual_sample_size
        new_delta = 0
        for k in range(1, m + 1):
            # WARNING: comb(m, k) may overflow for realtively small m and k, such as 2500 and 500
            new_delta += comb(m, k) * \
                ((1 / n) ** k) * ((1 - 1 / n) ** (m - k))
        new_delta *= delta

        return new_epsilon, new_delta


class SampleWithoutReplacement(Sampler):
    """
        It implements the sample with replacement technique (Theorem 9 from the reference) which reduces
        the epsilon-delta bugdet spent specified.

        Note that it only can sample the first dimension of a ndarray.

        # Arguments:
            sample_size: one dimentional size of the sample
            data_size: shape of the input data

        # References:
            - [Privacy Amplification by Subsampling: Tight Analyses via Couplings and Divergences](https://arxiv.org/abs/1807.01647)
    """

    def __init__(self, dp_mechanism, sample_size, data_size):
        super().__init__(dp_mechanism)
        check_sample_size(sample_size, data_size)
        self._dp_mechanism = dp_mechanism
        self._data_size = data_size
        self._sample_size = sample_size
        if len(self._data_size) > 1:
            # Data with more than one dimension
            self._actual_sample_size = self._sample_size * \
                prod(self._data_size[1:])
            self._data_size = prod(self._data_size)
        else:
            # One dimensional data
            self._actual_sample_size = self._sample_size
            self._data_size = self._data_size[0]

    def sample(self, data):
        return array_sampler.choice(data, size=self._sample_size, replace=False)

    def epsilon_delta_reduction(self, epsilon_delta):
        proportion = self._actual_sample_size / self._data_size
        epsilon, delta = epsilon_delta

        new_epsilon = log(1 + proportion * (exp(epsilon) - 1))
        new_delta = proportion * delta

        return new_epsilon, new_delta


def check_sample_size(sample_size, data_size):
    if sample_size > data_size[0]:
        raise ValueError("Sample size {} must be less than data size: {}".format(
            sample_size, data_size))
