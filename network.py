import tensorflow as tf
from game import Chess


class ChessNeuralNetwork(object):
    def __init__(self):
        with tf.variable_scope('neural_network'):
            self.feature_vector_ = tf.placeholder(tf.float32, shape=[None, 1025], name='feature_vector_')

            with tf.variable_scope('simple_value'):
                simple_value_weights = tf.get_variable('simple_value_weights',
                                                       initializer=tf.constant(Chess.get_simple_value_weights(),
                                                                               dtype=tf.float32),
                                                       trainable=False)
                self.simple_value = tf.matmul(self.feature_vector_, simple_value_weights)

            with tf.variable_scope('layer_1'):
                W_1 = tf.get_variable('W_1', initializer=tf.truncated_normal([1025, 100], stddev=0.1))
                hidden = tf.nn.relu(tf.matmul(self.feature_vector_, W_1), name='hidden')

            with tf.variable_scope('layer_2'):
                W_2 = tf.get_variable('W_2', initializer=tf.truncated_normal([100, 1], stddev=0.01))
                self.learned_value = tf.matmul(hidden, W_2)

            self.value = tf.tanh((self.simple_value + self.learned_value)/5)

            self.trainable_variables = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope=tf.get_variable_scope().name)

    def get_value(self, board, sess):
        value = sess.run(self.value,
                         feed_dict={self.feature_vector_: Chess.make_feature_vector(board)})
        return value

    def value_function(self, sess):
        def f(board):
            value = sess.run(self.value,
                             feed_dict={self.feature_vector_: Chess.make_feature_vector(board)})
            return value
        return f
