import numpy as np


def main():
    """
    This is sample code for linear regression, which demonstrates how to use the
    Graph class.

    Once you have answered Questions 2 and 3, you can run `python nn.py` to
    execute this code.
    """

    # This is our data, where x is a 4x2 matrix and y is a 4x1 matrix
    x = np.array([[0., 0.],
                  [0., 1.],
                  [1., 0.],
                  [1., 1.]])
    y = np.dot(x, np.array([[7.],
                            [8.]])) + 3

    # Let's construct a simple model to approximate a function from 2D
    # points to numbers, f(x) = x_0 * m_0 + x_1 * m_1 + b
    # Here m and b are variables (trainable parameters):
    m = Variable(2, 1)
    b = Variable(1)

    # We train our network using batch gradient descent on our data
    for iteration in range(10000):
        # At each iteration, we first calculate a loss that measures how
        # good our network is. The graph keeps track of all operations used
        graph = Graph([m, b])
        input_x = Input(graph, x)
        input_y = Input(graph, y)
        xm = MatrixMultiply(graph, input_x, m)
        xm_plus_b = MatrixVectorAdd(graph, xm, b)
        loss = SquareLoss(graph, xm_plus_b, input_y)
        # Then we use the graph to perform backprop and update our variables
        graph.backprop()
        graph.step(0.01)

    # After training, we should have recovered m=[[7],[8]] and b=[3]
    print("Final values are: {}".format([m.data[0, 0], m.data[1, 0], b.data[0]]))
    assert np.isclose(m.data[0, 0], 7)
    assert np.isclose(m.data[1, 0], 8)
    assert np.isclose(b.data[0], 3)
    print("Success!")


class Graph(object):
    """
    A graph that keeps track of the computations performed by a neural network
    in order to implement back-propagation.

    Each evaluation of the neural network (during both training and test-time)
    will create a new Graph. The computation will add nodes to the graph, where
    each node is either a DataNode or a FunctionNode.

    A DataNode represents a trainable parameter or an input to the computation.
    A FunctionNode represents doing a computation based on two previous nodes in
    the graph.

    The Graph is responsible for keeping track of all nodes and the order they
    are added to the graph, for computing gradients using back-propagation, and
    for performing updates to the trainable parameters.

    For an example of how the Graph can be used, see the function `main` above.
    """

    def __init__(self, variables):
        """
        Initializes a new computation graph.

        variables: a list of Variable objects that store the trainable parameters
            for the neural network.

        Hint: each Variable is also a node that needs to be added to the graph,
        so don't forget to call `self.add` on each of the variables.
        """
        "*** YOUR CODE HERE ***"
        self.backprop_called = False

        self.nodes = []  # [node1, node2, ...]
        self.index_output = {}  # {indexOfNode1: outputOfNode1} :index = 0 means LossNode
        self.index_gradient = {}  # {indexOnode1: gradientOfNode1} :gradient at index 0 is 1.0

        self.variables = variables  # since we do the update for each Variable node
        for variable in self.variables:
            self.add(variable)

    def get_nodes(self):
        """
        Returns a list of all nodes that have been added to this Graph, in the
        order they were added. This list should include all of the Variable
        nodes that were passed to `Graph.__init__`.

        Returns: a list of nodes
        """
        "*** YOUR CODE HERE ***"
        return self.nodes

    def get_inputs(self, node):
        """
        Retrieves the inputs to a node in the graph. Assume the `node` has
        already been added to the graph.

        Returns: a list of numpy arrays

        Hint: every node has a `.get_parents()` method
        """
        "*** YOUR CODE HERE ***"
        if len(node.get_parents()) == 0:
            return []

        else:
            lst = node.get_parents()
            parent1 = lst[0]
            parent2 = lst[1]
            input1 = self.get_output(parent1)
            input2 = self.get_output(parent2)
            return np.array([input1, input2])


    def get_output(self, node):
        """
        Retrieves the output to a node in the graph. Assume the `node` has
        already been added to the graph.

        Returns: a numpy array or a scalar
        """
        "*** YOUR CODE HERE ***"
        index = self.get_index(node)
        output = self.index_output[index]
        return output


    def get_gradient(self, node):
        """
        Retrieves the gradient for a node in the graph. Assume the `node` has
        already been added to the graph.

        If `Graph.backprop` has already been called, this should return the
        gradient of the loss with respect to the output of the node. If
        `Graph.backprop` has not been called, it should instead return a numpy
        array with correct shape to hold the gradient, but with all entries set
        to zero.

        Returns: a numpy array
        """
        "*** YOUR CODE HERE ***"
        index = self.get_index(node)
        # if np.all(self.index_gradient[0]): # this means if the back_prop is already called,
        if self.backprop_called:
            return np.array(self.index_gradient[index])
        else:
            output = self.index_output[index]
            return np.zeros_like(output)

    def add(self, node):
        """
        Adds a node to the graph.

        This method should calculate and remember the output of the node in the
        forwards pass (which can later be retrieved by calling `get_output`)
        We compute the output here because we only want to compute it once,
        whereas we may wish to call `get_output` multiple times.

        Additionally, this method should initialize an all-zero gradient
        accumulator for the node, with correct shape.
        """
        "*** YOUR CODE HERE ***"
        index = len(self.nodes)
        self.nodes.append(node)

        parent_nodes = node.get_parents()
        if len(parent_nodes) == 0:
            output = node.forward([])
            self.index_output[index] = output
            gradient = np.zeros_like(output)
            self.index_gradient[index] = gradient

        else:

            index1 = self.get_index(parent_nodes[0])
            a = self.index_output[index1]
            index2 = self.get_index(parent_nodes[1])
            b = self.index_output[index2]

            output = node.forward([a, b])

            self.index_output[index] = output
            gradient = np.zeros_like(output)
            self.index_gradient[index] = gradient

    def get_index(self, node):
        index = 0
        for n in self.nodes:
            if np.all(n == node):
                return index
            index += 1

    def backprop(self):
        """
        Runs back-propagation. Assume that the very last node added to the graph
        represents the loss.

        After back-propagation completes, `get_gradient(node)` should return the
        gradient of the loss with respect to the `node`.

        Hint: the gradient of the loss with respect to itself is 1.0, and
        back-propagation should process nodes in the exact opposite of the order
        in which they were added to the graph.
        """
        loss_node = self.get_nodes()[-1]
        assert np.asarray(self.get_output(loss_node)).ndim == 0

        "*** YOUR CODE HERE ***"
        self.backprop_called = True
        index = len(self.nodes) - 1 # index of the loss_node is the last one
        self.index_gradient[index] = 1.0
        length = len(self.variables)
        while index > length - 1:
            output_gradient = self.index_gradient[index]
            node = self.nodes[index]
            inputs = self.get_inputs(node)
            gradient = node.backward(inputs, output_gradient)

            if len(gradient) == 0:
                self.index_gradient[index] = []
            else:
                grad1 = gradient[0]
                input1 = node.get_parents()[0]
                index1 = self.get_index(input1)
                self.index_gradient[index1] += grad1

                grad2 = gradient[1]
                input2 = node.get_parents()[1]
                index2 = self.get_index(input2)
                self.index_gradient[index2] += grad2

            index -= 1

    def step(self, step_size):
        """
        Updates the values of all variables based on computed gradients.
        Assume that `backprop()` has already been called, and that gradients
        have already been computed.

        Hint: each Variable has a `.data` attribute
        """
        "*** YOUR CODE HERE ***"
        for variable in self.variables:
            index = self.get_index(variable)
            variable.data = variable.data - np.array(self.index_gradient[index]) * step_size


class DataNode(object):
    """
    DataNode is the parent class for Variable and Input nodes.

    Each DataNode must define a `.data` attribute, which represents the data
    stored at the node.
    """

    @staticmethod
    def get_parents():
        # A DataNode has no parent nodes, only a `.data` attribute
        return []

    def forward(self, inputs):
        # The forwards pass for a data node simply returns its data
        return self.data

    @staticmethod
    def backward(inputs, gradient):
        # A DataNode has no parents or inputs, so there are no gradients to
        # compute in the backwards pass
        return []


class Variable(DataNode):
    """
    A Variable stores parameters used in a neural network.

    Variables should be created once and then passed to all future Graph
    constructors. Use `.data` to access or modify the numpy array of parameters.
    """

    def __init__(self, *shape):
        """
        Initializes a Variable with a given shape.

        For example, Variable(5) will create 5-dimensional vector variable,
        while Variable(10, 10) will create a 10x10 matrix variable.

        The initial value of the variable before training starts can have a big
        effect on how long the network takes to train. The provided initializer
        works well across a wide range of applications.
        """
        assert shape
        limit = np.sqrt(3.0 / np.mean(shape))
        self.data = np.random.uniform(low=-limit, high=limit, size=shape)


class Input(DataNode):
    """
    An Input node packages a numpy array into a node in a computation graph.
    Use this node for inputs to your neural network.

    For trainable parameters, use Variable instead.
    """

    def __init__(self, graph, data):
        """
        Initializes a new Input and adds it to a graph.
        """
        assert isinstance(data, np.ndarray), "data must be a numpy array"
        assert data.dtype.kind == "f", "data must have floating-point entries"
        self.data = data
        graph.add(self)


class FunctionNode(object):
    """
    A FunctionNode represents a value that is computed based on other nodes in
    the graph. Each function must implement both a forward and backward pass.
    """

    def __init__(self, graph, *parents):
        self.parents = parents
        graph.add(self)

    def get_parents(self):
        return self.parents

    @staticmethod
    def forward(inputs):
        raise NotImplementedError

    @staticmethod
    def backward(inputs, gradient):
        raise NotImplementedError


class Add(FunctionNode):
    """
    Adds two vectors or matrices, element-wise

    Inputs: [x, y]
        x may represent either a vector or a matrix
        y must have the same shape as x
    Output: x + y
    """

    @staticmethod
    def forward(inputs):
        "*** YOUR CODE HERE ***"
        s = np.sum([inputs[0], inputs[1]], axis=0)
        return s

    @staticmethod
    def backward(inputs, gradient):
        "*** YOUR CODE HERE ***"
        return [gradient, gradient]


class MatrixMultiply(FunctionNode):
    """
    Represents matrix multiplication.

    Inputs: [A, B]
        A represents a matrix of shape (n x m)
        B represents a matrix of shape (m x k)
    Output: a matrix of shape (n x k)
    """

    @staticmethod
    def forward(inputs):
        "*** YOUR CODE HERE ***"
        return np.matmul(inputs[0], inputs[1])

    @staticmethod
    def backward(inputs, gradient):
        "*** YOUR CODE HERE ***"
        "*** YOUR CODE HERE ***"
        A = inputs[0]
        B = inputs[1]
        gradient = np.asarray(gradient)
        if (len(gradient.shape) == 1):
            gradient = np.reshape(gradient, (gradient.shape[0], 1))
        result = [np.dot(gradient, np.transpose(B)), np.dot(np.transpose(A), gradient)]
        return result

    """

        A = inputs[0]
        B = inputs[1]

        result = [np.matmul(gradient2, np.transpose(B)), np.matmul( np.transpose(A),gradient2 )]
        return result
"""


class MatrixVectorAdd(FunctionNode):
    """
    Adds a vector to each row of a matrix.

    Inputs: [A, x]
        A represents a matrix of shape (n x m)
        x represents a vector (m)
    Output: a matrix of shape (n x m)
    """

    @staticmethod
    def forward(inputs):
        "*** YOUR CODE HERE ***"

        s = inputs[0] + inputs[1]
        return s

    @staticmethod
    def backward(inputs, gradient):
        "*** YOUR CODE HERE ***"

        k = np.sum(gradient, axis=0)

        return [gradient, k]


class ReLU(FunctionNode):
    """
    An element-wise Rectified Linear Unit nonlinearity: max(x, 0).
    This nonlinearity replaces all negative entries in its input with zeros.

    Input: [x]
        x represents either a vector or matrix
    Output: same shape as x, with no negative entries
    """

    @staticmethod
    def forward(inputs):
        "*** YOUR CODE HERE ***"
        kk = inputs[0].copy()
        kk[kk < 0] = 0
        return (np.array(kk, ))

    @staticmethod
    def backward(inputs, gradient):
        "*** YOUR CODE HERE ***"
        kk = inputs[0].copy()
        kk[kk < 0] = 0
        kk2 = kk.copy()
        kk2[kk2 > 0] = 1
        return [kk2 * gradient]


class SquareLoss(FunctionNode):
    """
    Inputs: [a, b]
        a represents a matrix of size (batch_size x dim)
        b must have the same shape as a
    Output: a number

    This node first computes 0.5 * (a[i,j] - b[i,j])**2 at all positions (i,j)
    in the inputs, which creates a (batch_size x dim) matrix. It then calculates
    and returns the mean of all elements in this matrix.
    """

    @staticmethod
    def forward(inputs):
        "*** YOUR CODE HERE ***"
        diff = inputs[0] - inputs[1]
        multi = diff * diff
        m = np.multiply(multi, 0.5)
        # if m == []: # this two lines are written because I saw a run time warning
        #     return 0
        return m.mean()

    @staticmethod
    def backward(inputs, gradient):
        "*** YOUR CODE HERE ***"
        x = inputs[0]
        y = inputs[1]
        N = x.shape[0] * x.shape[1]
        matrix1 = x - y
        matrix2 = y - x
        return [matrix1 * gradient / N, matrix2 * gradient / N]


class SoftmaxLoss(FunctionNode):
    """
    A batched softmax loss, used for classification problems.

    IMPORTANT: do not swap the order of the inputs to this node!

    Inputs: [logits, labels]
        logits: a (batch_size x num_classes) matrix of scores, that is typically
            calculated based on previous layers. Each score can be an arbitrary
            real number.
        labels: a (batch_size x num_classes) matrix that encodes the correct
            labels for the examples. All entries must be non-negative and the
            sum of values along each row should be 1.
    Output: a number

    We have provided the complete implementation for your convenience.
    """

    @staticmethod
    def softmax(input):
        exp = np.exp(input - np.max(input, axis=1, keepdims=True))
        return exp / np.sum(exp, axis=1, keepdims=True)

    @staticmethod
    def forward(inputs):
        softmax = SoftmaxLoss.softmax(inputs[0])
        labels = inputs[1]
        assert np.all(labels >= 0), \
            "Labels input to SoftmaxLoss must be non-negative. (Did you pass the inputs in the right order?)"
        assert np.allclose(np.sum(labels, axis=1), np.ones(labels.shape[0])), \
            "Labels input to SoftmaxLoss do not sum to 1 along each row. (Did you pass the inputs in the right order?)"

        return np.mean(-np.sum(labels * np.log(softmax), axis=1))

    @staticmethod
    def backward(inputs, gradient):
        softmax = SoftmaxLoss.softmax(inputs[0])
        return [
            gradient * (softmax - inputs[1]) / inputs[0].shape[0],
            gradient * (-np.log(softmax)) / inputs[0].shape[0]
        ]


if __name__ == '__main__':
    main()
