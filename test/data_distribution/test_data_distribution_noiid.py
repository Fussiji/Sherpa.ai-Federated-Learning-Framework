import pytest
import numpy as np
import random

from shfl.data_base.data_base import DataBase
from shfl.data_distribution.data_distribution_non_iid import NonIidDataDistribution,choose_labels


class TestDataBase(DataBase):
    def __init__(self):
        super(TestDataBase, self).__init__()

    def load_data(self):
        self._train_data = np.random.rand(250).reshape([50,5])
        self._test_data = np.random.rand(250).reshape([50,5])
        self._validation_data = np.random.rand(250).reshape([50,5])
        self._train_labels = np.random.randint(0,10,50)
        self._test_labels = np.random.randint(0,10,50)
        self._validation_labels = np.random.randint(0,10,50)


def test_choose_labels():
    num_nodes = 3
    total_labels = 10

    random_labels = choose_labels(num_nodes,total_labels)
    all_labels = np.concatenate(random_labels)

    for node in random_labels:
        assert len(node) <= total_labels

    assert len(random_labels) == num_nodes
    assert ((all_labels>=0) & (all_labels<total_labels)).all()


def test_make_data_federated():
    random.seed(123)
    np.random.seed(123)

    data = TestDataBase()
    data.load_data()
    data_distribution = NonIidDataDistribution(data)

    train_data, train_label = data_distribution._database.train
    validation_data, validation_label = data_distribution._database.validation

    train_data = np.concatenate((train_data, validation_data), axis=0)
    train_label = np.concatenate((train_label, validation_label), axis=0)

    num_nodes = 3
    percent = 60
    # weights = np.full(num_nodes, 1/num_nodes)
    weights = [0.5,0.25,0.25]
    federated_data, federated_label = data_distribution.make_data_federated(train_data,
                                                                            train_label,
                                                                            num_nodes,
                                                                            percent,
                                                                            weights)

    all_data = np.concatenate(federated_data)
    all_label = np.concatenate(federated_label)

    idx = []
    for data in all_data:
        idx.append(np.where((data==train_data).all(axis=1))[0][0])

    seed_weights = [6,12,5]
    for i,weight in enumerate(weights):
        assert federated_data[i].shape[0] == seed_weights[i]

    assert all_data.shape[0] == 23
    assert num_nodes == federated_data.shape[0] == federated_label.shape[0]
    assert (np.sort(all_data.ravel()) == np.sort(train_data[idx,].ravel())).all()
    assert (np.sort(all_label) == np.sort(train_label[idx])).all()


