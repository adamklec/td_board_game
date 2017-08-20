import tensorflow as tf
from agents.epsilon_greedy_agent import EpsilonGreedyAgent
from agents.td_leaf_agent import TDLeafAgent
from envs.tic_tac_toe import TicTacToeEnv
from value_model import ValueModel
import time


def main():
    env = TicTacToeEnv()
    network = ValueModel(env.get_feature_vector_size())
    # agent = EpsilonGreedyAgent('agent_0', network, env, verbose=True)
    agent = TDLeafAgent('agent_0', network, env, verbose=True)
    summary_op = tf.summary.merge_all()
    log_dir = "./log/" + str(int(time.time()))

    with tf.variable_scope('episode_count'):
        global_episode_count = tf.train.get_or_create_global_step()
        increment_global_episode_count_op = global_episode_count.assign_add(1)

    with tf.train.MonitoredTrainingSession(checkpoint_dir=log_dir,
                                           scaffold=tf.train.Scaffold(summary_op=summary_op)) as sess:
        agent.sess = sess

        for i in range(10000000):
            sess.run(increment_global_episode_count_op)
            if i % 100 == 0:
                agent.random_agent_test(depth=1)
            agent.train(depth=1)

if __name__ == "__main__":
    main()
