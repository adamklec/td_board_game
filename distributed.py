from agents.nn_agent import NeuralNetworkAgent
from game import Chess
from multiprocessing import Process
import time
import tensorflow as tf
from network import ChessNeuralNetwork


def work(job_name, task_index, ps_hosts, tester_hosts, trainer_hosts, checkpoint_dir):

    cluster = tf.train.ClusterSpec({"ps": ps_hosts, "tester": tester_hosts, "trainer": trainer_hosts})

    server = tf.train.Server(cluster,
                             job_name=job_name,
                             task_index=task_index)

    if job_name == "ps":
        server.join()

    else:

        with tf.device(tf.train.replica_device_setter(
                worker_device="/job:" + job_name + "/task:%d" % task_index,
                cluster=cluster)):
            network = ChessNeuralNetwork()
            global_episode_count = tf.contrib.framework.get_or_create_global_step()

        if job_name == "tester":

            agent_name = 'tester_' + str(task_index)
            agent = NeuralNetworkAgent(agent_name,
                                       network,
                                       global_episode_count=global_episode_count,
                                       verbose=True,
                                       load_tests=True,
                                       load_pgn=False)
        else:
            agent_name = 'trainer_' + str(task_index)
            agent = NeuralNetworkAgent(agent_name,
                                       network,
                                       global_episode_count=global_episode_count,
                                       verbose=True,
                                       load_tests=False,
                                       load_pgn=True)

        summary_op = tf.summary.merge_all()

        hooks = [tf.train.StopAtStepHook(last_step=10000)]

        with tf.train.MonitoredTrainingSession(master=server.target,
                                               is_chief=(task_index == 0 and job_name == 'trainer'),
                                               checkpoint_dir=checkpoint_dir,
                                               hooks=hooks,
                                               save_summaries_steps=1,
                                               scaffold=tf.train.Scaffold(summary_op=summary_op)) as mon_sess:
            if job_name == "trainer":
                while not mon_sess.should_stop():
                    agent.train(mon_sess, depth=1)

            elif job_name == "tester":
                while not mon_sess.should_stop():
                    agent.test(mon_sess, test_idxs=range(13)[task_idx::2], depth=1)

if __name__ == "__main__":
    ps_host_list = ['localhost:2222']
    tester_host_list = ['localhost:2223', 'localhost:2224']
    trainer_host_list = ['localhost:2225', 'localhost:2226']
    ckpt_dir = "log/" + str(int(time.time()))

    processes = []

    for task_idx, _ in enumerate(ps_host_list):
        p = Process(target=work, args=('ps', task_idx, ps_host_list, tester_host_list, trainer_host_list, ckpt_dir,))
        processes.append(p)
        p.start()
        time.sleep(2)

    for task_idx, _ in enumerate(tester_host_list):
        p = Process(target=work, args=('tester', task_idx, ps_host_list, tester_host_list, trainer_host_list, ckpt_dir,))
        processes.append(p)
        p.start()

    for task_idx, _ in enumerate(trainer_host_list):
        p = Process(target=work, args=('trainer', task_idx, ps_host_list, tester_host_list, trainer_host_list, ckpt_dir,))
        processes.append(p)
        p.start()

    for process in processes:
        process.join()