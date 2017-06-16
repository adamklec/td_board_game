from agents.nn_agent import NeuralNetworkAgent
from game import Chess
from multiprocessing import Process
import time
import tensorflow as tf


def work(job_name, task_index, ps_hosts, worker_hosts, checkpoint_dir):
    cluster = tf.train.ClusterSpec({"ps": ps_hosts, "worker": worker_hosts})

    server = tf.train.Server(cluster,
                             job_name=job_name,
                             task_index=task_index)

    if job_name == "ps":
        server.join()

    elif job_name == "worker":

        with tf.device(tf.train.replica_device_setter(
                worker_device="/job:worker/task:%d" % task_index,
                cluster=cluster)):
            global_episode_count = tf.contrib.framework.get_or_create_global_step()
            agent = NeuralNetworkAgent('agent_' + str(task_index), global_episode_count, verbose=True)

        hooks = [tf.train.StopAtStepHook(last_step=1000)]
        with tf.train.MonitoredTrainingSession(master=server.target,
                                               is_chief=(task_index == 0),
                                               checkpoint_dir=checkpoint_dir,
                                               hooks=hooks) as mon_sess:

            while not mon_sess.should_stop():
                agent.train(mon_sess, Chess(), 100, 0.05, pretrain=False)

if __name__ == "__main__":
    ps_hosts = ['localhost:2222', 'localhost:2223']
    worker_hosts = ['localhost:2224', 'localhost:2225', 'localhost:2226', 'localhost:2227']
    checkpoint_dir = "log/" + str(int(time.time()))

    processes = []

    for task_idx, ps_host in enumerate(ps_hosts):
        p = Process(target=work, args=('ps', task_idx, ps_hosts, worker_hosts, checkpoint_dir,))
        processes.append(p)
        p.start()

    for task_idx, worker_host in enumerate(worker_hosts):
        p = Process(target=work, args=('worker', task_idx, ps_hosts, worker_hosts, checkpoint_dir,))
        processes.append(p)
        p.start()
        time.sleep(2)

    for process in processes:
        process.join()
