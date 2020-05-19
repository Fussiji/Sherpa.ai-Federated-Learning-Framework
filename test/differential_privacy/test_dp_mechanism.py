import numpy as np
import pytest

import shfl
from shfl.private import DataNode
from shfl.private.data import UnprotectedAccess
from shfl.differential_privacy.dp_mechanism import RandomizedResponseBinary
from shfl.differential_privacy.dp_mechanism import RandomizedResponseCoins
from shfl.differential_privacy.dp_mechanism import LaplaceMechanism
from shfl.differential_privacy.dp_mechanism import ExponentialMechanism
from shfl.differential_privacy.dp_mechanism import GaussianMechanism
from shfl.differential_privacy.dp_mechanism import ExceededPrivacyBudgetError
from shfl.differential_privacy.dp_mechanism import AdaptiveDifferentialPrivacy
from shfl.differential_privacy.probability_distribution import NormalDistribution


def test_exception__budget():
    exception = ExceededPrivacyBudgetError(epsilon_delta=1)
    assert str(exception) is not None


def test_exception_exceeded_privacy_budget_error():
    scalar = 175

    data_access_definition = AdaptiveDifferentialPrivacy(epsilon_delta=(1, 0),
                                                         default_access_definition=GaussianMechanism(1,
                                                                                                     epsilon_delta=(0.1,
                                                                                                                    1)))
    node = DataNode()
    node.set_private_data("scalar", scalar)
    node.configure_data_access("scalar", data_access_definition)

    with pytest.raises(ExceededPrivacyBudgetError):
        node.query("scalar")


def test_constructor_bad_params():
    with pytest.raises(ValueError):
        AdaptiveDifferentialPrivacy(epsilon_delta=(1, 2, 3))

    with pytest.raises(ValueError):
        AdaptiveDifferentialPrivacy(epsilon_delta=(-1, 2))

    with pytest.raises(ValueError):
        AdaptiveDifferentialPrivacy(epsilon_delta=(1, -2))

    with pytest.raises(ValueError):
        AdaptiveDifferentialPrivacy(epsilon_delta=(1, 1), default_access_definition=UnprotectedAccess())


def test_get_epsilon_delta():
    e_d = (1, 1)
    data_access_definition = AdaptiveDifferentialPrivacy(epsilon_delta=e_d)

    assert data_access_definition.epsilon_delta == e_d


def test_configure_data_access():
    data_access_definition = AdaptiveDifferentialPrivacy(epsilon_delta=(1, 1))
    data_node = DataNode()
    data_node.set_private_data("test", np.array(range(10)))
    with pytest.raises(ValueError):
        data_node.configure_data_access("test", data_access_definition)
        data_node.query("test")


def test_data_access():
    data_access_definition = AdaptiveDifferentialPrivacy(epsilon_delta=(1, 1))
    data_node = DataNode()
    array = np.array(range(10))
    data_node.set_private_data("test", array)

    data_node.configure_data_access("test", data_access_definition)
    query_result = data_node.query("test", data_access_definition=GaussianMechanism(1, epsilon_delta=(0.1, 1)))

    assert query_result is not None


def test_exception_no_access_definition():
    data_access_definition = AdaptiveDifferentialPrivacy(epsilon_delta=(1, 1))
    data_node = DataNode()
    array = np.array(range(10))
    data_node.set_private_data("test", array)

    data_node.configure_data_access("test", data_access_definition)
    with pytest.raises(ValueError):
        data_node.query("test")


def test_exception_budget():
    data_access_definition = AdaptiveDifferentialPrivacy(epsilon_delta=(1, 1),
                                                         default_access_definition=GaussianMechanism(1, epsilon_delta=(0.1, 1)))
    data_node = DataNode()
    array = np.array(range(10))
    data_node.set_private_data("test", array)

    data_node.configure_data_access("test", data_access_definition)
    with pytest.raises(ExceededPrivacyBudgetError):
        for i in range(1, 1000):
            data_node.query("test")


def test_exception_budget_2():
    data_access_definition = AdaptiveDifferentialPrivacy(epsilon_delta=(1, 0.001))
    data_node = DataNode()
    array = np.array(range(10))
    data_node.set_private_data("test", array)

    data_node.configure_data_access("test", data_access_definition)
    with pytest.raises(ExceededPrivacyBudgetError):
        for i in range(1, 1000):
            data_node.query("test", data_access_definition=GaussianMechanism(1, epsilon_delta=(0.1, 1)))


def test_randomize_binary_mechanism_coins():
    data_size = 100
    array = np.ones(data_size)
    federated_array = shfl.private.federated_operation.federate_array(array, data_size)

    federated_array.configure_data_access(RandomizedResponseCoins())

    result = federated_array.query()
    differences = 0
    for i in range(data_size):
        if result[i] != array[i]:
            differences = differences + 1

    assert 0 < differences < data_size
    assert np.mean(result) < 1


def test_randomized_response_coins_epsilon_delta():
    randomized_response_coins = RandomizedResponseCoins()

    assert randomized_response_coins.epsilon_delta is not None


def test_randomized_response_binary_epsilon_delta():
    randomized_response_binary = RandomizedResponseBinary(f0=0.1, f1=0.9, epsilon=1)

    assert randomized_response_binary.epsilon_delta is not None


def test_laplace_epsilon_delta():
    laplace_mechanism = LaplaceMechanism(sensitivity=0.1, epsilon=1)

    assert laplace_mechanism.epsilon_delta is not None


def test_exponential_epsilon_delta():
    def u(x, r):
        output = np.zeros(len(r))
        for i in range(len(r)):
            output[i] = r[i] * sum(np.greater_equal(x, r[i]))
        return output

    r = np.arange(0, 3.5, 0.001)
    delta_u = r.max()
    epsilon = 5
    exponential_mechanism = ExponentialMechanism(u, r, delta_u, epsilon)

    assert exponential_mechanism.epsilon_delta is not None


def test_randomize_binary_mechanism_array_coins():
    array = np.ones(100)
    node_single = DataNode()
    node_single.set_private_data(name="array", data=array)

    node_single.configure_data_access("array", RandomizedResponseCoins())

    result = node_single.query("array")
    differences = 0
    for i in range(100):
        if result[i] != array[i]:
            differences = differences + 1

    assert not np.isscalar(result)
    assert 0 < differences < 100
    assert np.mean(result) < 1


def test_randomize_binary_mechanism_array_almost_always_true_values_coins():
    array = np.ones(1000)
    node_single = DataNode()
    node_single.set_private_data(name="array", data=array)

    # Very low heads probability in the first attempt, mean should be near true value
    data_access_definition = RandomizedResponseCoins(prob_head_first=0.01, prob_head_second=0.9)
    node_single.configure_data_access("array", data_access_definition)

    result = node_single.query("array")

    assert 1 - np.mean(result) < 0.05


def test_randomize_binary_mechanism_array_almost_always_random_values_coins():
    array = np.ones(1000)
    node_single = DataNode()
    node_single.set_private_data(name="array", data=array)

    # Very high heads probability in the first attempt, mean should be near prob_head_second
    data_access_definition = RandomizedResponseCoins(prob_head_first=0.99, prob_head_second=0.1)
    node_single.configure_data_access("array", data_access_definition)

    result = node_single.query("array")

    assert np.abs(0.1 - np.mean(result)) < 0.05


def test_randomize_binary_mechanism_scalar_coins():
    scalar = 1
    node_single = DataNode()
    node_single.set_private_data(name="scalar", data=scalar)

    node_single.configure_data_access("scalar", RandomizedResponseCoins())

    result = node_single.query(private_property="scalar")

    assert np.isscalar(result)
    assert result == 0 or result == 1


def test_randomize_binary_mechanism_no_binary_coins():
    data_size = 100
    array = np.random.rand(data_size)
    federated_array = shfl.private.federated_operation.federate_array(array, data_size)

    federated_array.configure_data_access(RandomizedResponseCoins())

    with pytest.raises(ValueError):
        federated_array.query()


def test_randomize_binary_deterministic():
    array = np.array([0, 1])
    node_single = DataNode()
    node_single.set_private_data(name="A", data=array)
    with pytest.raises(ValueError):
        RandomizedResponseBinary(f0=1, f1=1, epsilon=1)


def test_randomize_binary_random():
    data_size = 100
    array = np.ones(data_size)
    node_single = DataNode()
    node_single.set_private_data(name="A", data=array)
    data_access_definition = RandomizedResponseBinary(f0=0.5, f1=0.5, epsilon=1)
    node_single.configure_data_access("A", data_access_definition)

    result = node_single.query(private_property="A")

    differences = 0
    for i in range(data_size):
        if result[i] != array[i]:
            differences = differences + 1

    assert 0 < differences < data_size
    assert np.mean(result) < 1


def test_randomize_binary_random_scalar_1():
    scalar = 1
    node_single = DataNode()
    node_single.set_private_data(name="scalar", data=scalar)
    data_access_definition = RandomizedResponseBinary(f0=0.5, f1=0.5, epsilon=1)
    node_single.configure_data_access("scalar", data_access_definition)

    result = node_single.query(private_property="scalar")

    assert np.isscalar(result)
    assert result == 0 or result == 1


def test_randomize_binary_random_scalar_0():
    scalar = 0
    node_single = DataNode()
    node_single.set_private_data(name="scalar", data=scalar)
    data_access_definition = RandomizedResponseBinary(f0=0.5, f1=0.5, epsilon=1)
    node_single.configure_data_access("scalar", data_access_definition)

    result = node_single.query(private_property="scalar")

    assert np.isscalar(result)
    assert result == 0 or result == 1


def test_randomize_binary_mechanism_array_almost_always_true_values_ones():
    array = np.ones(1000)
    node_single = DataNode()
    node_single.set_private_data(name="array", data=array)

    # Prob of one given 1 very high, mean should be near 1
    data_access_definition = RandomizedResponseBinary(f0=0.5, f1=0.99, epsilon=5)
    node_single.configure_data_access("array", data_access_definition)

    result = node_single.query("array")

    assert 1 - np.mean(result) < 0.05


def test_randomize_binary_mechanism_array_almost_always_true_values_zeros():
    array = np.zeros(1000)
    node_single = DataNode()
    node_single.set_private_data(name="array", data=array)

    # Prob of one given 1 very high, mean should be near 1
    data_access_definition = RandomizedResponseBinary(f0=0.99, f1=0.5, epsilon=5)
    node_single.configure_data_access("array", data_access_definition)

    result = node_single.query("array")

    assert np.abs(0 - np.mean(result)) < 0.05


def test_randomize_binary_mechanism_array_almost_always_false_values():
    array = np.ones(1000)
    node_single = DataNode()
    node_single.set_private_data(name="array", data=array)

    # Prob of one given 1 very low, mean should be near 0
    data_access_definition = RandomizedResponseBinary(f0=0.5, f1=0.01, epsilon=1)
    node_single.configure_data_access("array", data_access_definition)

    result = node_single.query("array")

    assert np.abs(0 - np.mean(result)) < 0.05


def test_randomize_binary_mechanism_array_almost_always_false_values_zeros():
    array = np.zeros(1000)
    node_single = DataNode()
    node_single.set_private_data(name="array", data=array)

    # Prob of one given 1 very low, mean should be near 0
    data_access_definition = RandomizedResponseBinary(f0=0.01, f1=0.5, epsilon=1)
    node_single.configure_data_access("array", data_access_definition)

    result = node_single.query("array")

    assert np.abs(1 - np.mean(result)) < 0.05


def test_randomize_binary_mechanism_no_binary():
    array = np.random.rand(1000)
    federated_array = shfl.private.federated_operation.federate_array(array, 100)

    federated_array.configure_data_access(RandomizedResponseBinary(f0=0.5, f1=0.5, epsilon=1))

    with pytest.raises(ValueError):
        federated_array.query()


def test_randomize_binary_mechanism_no_binary_scalar():
    scalar = 0.1
    node_single = DataNode()
    node_single.set_private_data(name="scalar", data=scalar)
    data_access_definition = RandomizedResponseBinary(f0=0.5, f1=0.5, epsilon=1)
    node_single.configure_data_access("scalar", data_access_definition)

    with pytest.raises(ValueError):
        node_single.query("scalar")


def test_laplace_mechanism():
    data_size = 1000
    array = NormalDistribution(175, 7).sample(data_size)
    federated_array = shfl.private.federated_operation.federate_array(array, data_size)

    federated_array.configure_data_access(LaplaceMechanism(1, 1))
    result = federated_array.query()

    differences = 0
    for i in range(data_size):
        if result[i] != array[i]:
            differences = differences + 1

    assert differences == data_size
    assert np.mean(array) - np.mean(result) < 5


def test_laplace_scalar_mechanism():
    scalar = 175

    node = DataNode()
    node.set_private_data("scalar", scalar)
    node.configure_data_access("scalar", LaplaceMechanism(1, 1))

    result = node.query("scalar")

    assert scalar != result
    assert np.abs(scalar - result) < 100


def test_gaussian_mechanism():
    data_size = 1000
    array = NormalDistribution(175, 7).sample(data_size)
    federated_array = shfl.private.federated_operation.federate_array(array, data_size)

    federated_array.configure_data_access(GaussianMechanism(1, epsilon_delta=(0.1, 1)))
    result = federated_array.query()

    differences = 0
    for i in range(data_size):
        if result[i] != array[i]:
            differences = differences + 1

    assert differences == data_size
    assert np.mean(array) - np.mean(result) < 5


def test_gaussian_scalar_mechanism():
    scalar = 175

    node = DataNode()
    node.set_private_data("scalar", scalar)
    node.configure_data_access("scalar", GaussianMechanism(1, epsilon_delta=(0.1, 1)))

    result = node.query("scalar")

    assert scalar != result
    assert np.abs(scalar - result) < 100


def test_exponential_mechanism_pricing():
    
    def u(x, r):
        output = np.zeros(len(r))
        for i in range(len(r)): 
            output[i] = r[i] * sum(np.greater_equal(x, r[i]))
        return output
    
    x = [1.00, 1.00, 1.00, 3.01]    # Input dataset: the true bids
    r = np.arange(0, 3.5, 0.001)    # Set the interval of possible outputs r
    delta_u = r.max()               # In this specific case, Delta u = max(r)
    epsilon = 5                     # Set a value for epsilon
    size = 10000                    # We want to repeat the query this many times

    node = DataNode()
    node.set_private_data(name="bids", data=np.array(x)) 
    data_access_definition = ExponentialMechanism(u, r, delta_u, epsilon, size)
    node.configure_data_access("bids", data_access_definition)
    result = node.query("bids")
    y_bin, x_bin = np.histogram(a=result, bins=int(round(np.sqrt(len(result)))), density=True)
    
    max_price = x_bin[np.where(y_bin == y_bin.max())]
    min_price = x_bin[np.where(y_bin == y_bin.min())]
    bin_size = x_bin[1] - x_bin[0]
    assert (1.00 - x_bin[np.where(y_bin == max_price)] > bin_size).all()       # Check the best price is close to 1.00
    assert ((x_bin[np.where(y_bin == min_price)] > (3.01 - bin_size)).all()    # Check the no-revenue price is either greater than 3.01
            or x_bin[np.where(y_bin == min_price)][0] < bin_size )             # or close to 0.00                 
     
    
def test_exponential_mechanism_obtain_laplace():
    
    def u_laplacian(x, r):
        output = -np.absolute(x - r)
        return output

    r = np.arange(-20, 20, 0.001)   # Set the interval of possible outputs r
    x = 3.5                         # Set a value for the dataset
    delta_u = 1                     # We simply set it to one
    epsilon = 1                     # Set a value for epsilon
    size = 100000                   # We want to repeat the query this many times

    node = DataNode()
    node.set_private_data(name="identity", data=np.array(x))

    data_access_definition = ExponentialMechanism(u_laplacian, r, delta_u, epsilon, size)
    node.configure_data_access("identity", data_access_definition)
    result = node.query("identity")

    assert (result > r.min()).all() and (result < r.max()).all()    # Check all outputs are within range
    assert np.absolute(np.mean(result) - x) < (delta_u/epsilon)     # Check the mean output is close to true value


def test_mechanism_safery_checks():
    with pytest.raises(ValueError):
        GaussianMechanism(1, epsilon_delta=(1, 1, 1))
        
    with pytest.raises(ValueError):
        GaussianMechanism(1, epsilon_delta=(-0.5, 1))
        
    with pytest.raises(ValueError):
        GaussianMechanism(1, epsilon_delta=(0.5, -1))


def test_gaussian_mechanism_correctness():
    with pytest.raises(ValueError):
        GaussianMechanism(1, epsilon_delta=(1, 1))


def test_randomized_response_correctness():
    with pytest.raises(ValueError):
        RandomizedResponseBinary(0.1, 2, epsilon = 20)
    
    with pytest.raises(ValueError):
        RandomizedResponseBinary(0.8, 0.8, epsilon=0.1)