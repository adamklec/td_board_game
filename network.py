import tensorflow as tf


class ValueNeuralNetwork(object):
    def __init__(self, env):
        # We are passing the environment in to the network so that when we are training on a chess environment
        # we can initialize the network to know about piece values

        fv_size = env.get_feature_vector_size()

        with tf.variable_scope('neural_network'):
            self.feature_vector_ = tf.placeholder(tf.float32, shape=[None, fv_size], name='feature_vector_')
            with tf.variable_scope('simple_value'):
                simple_value_weights = tf.get_variable('simple_value_weights',
                                                       initializer=tf.constant(env.get_simple_value_weights(),
                                                                               dtype=tf.float32),
                                                       trainable=False)
                self.simple_value = tf.matmul(self.feature_vector_, simple_value_weights)

            with tf.variable_scope('layer_1'):
                W_1 = tf.get_variable('W_1', initializer=tf.truncated_normal([fv_size, 100], stddev=0.01))
                self.simple_learned = tf.matmul(self.feature_vector_, W_1)
                hidden = tf.nn.relu(tf.matmul(self.feature_vector_, W_1), name='hidden')
            with tf.variable_scope('layer_2'):
                W_2 = tf.get_variable('W_2', initializer=tf.truncated_normal([100, 1], stddev=0.01))
                self.learned_value = tf.matmul(hidden, W_2)

            self.combined_score = self.simple_value + self.learned_value
            self.value = tf.tanh(self.combined_score/5.0)
            self.trainable_variables = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope=tf.get_variable_scope().name)

    def value_function(self, sess):
        def f(fv):
            value = sess.run(self.value,
                             feed_dict={self.feature_vector_: fv})
            return value
        return f

