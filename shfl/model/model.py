import abc


class TrainableModel(abc.ABC):
    """
    Interface of the models that can be trained. If you want to use a model that is not implemented
    in the framework you have to implement a class with this interface.
    """

    @abc.abstractmethod
    def train(self, data, labels):
        """
        Method that train the model

        # Arguments:
            data: Data to train the model
            labels: Label for each train element
        """

    @abc.abstractmethod
    def predict(self, data):
        """
        Predict labels for data

        # Arguments:
            data: data for predictions

        # Returns:
            predictions : matrix with predictions for data
        """

    @abc.abstractmethod
    def get_model_params(self):
        """
        Gets the params that define the model

        # Returns:
            params : parameters defining the model
        """

    @abc.abstractmethod
    def set_model_params(self, params):
        """
        Update the params that define the model

        # Arguments:
            params : parameters defining the model
        """
