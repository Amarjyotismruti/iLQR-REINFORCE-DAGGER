"""Functions for imitation learning."""
from __future__ import division, absolute_import
from __future__ import print_function, unicode_literals
import gym
from keras.models import model_from_yaml
from keras.optimizers import adam
import numpy as np
import time


def load_model(model_config_path, model_weights_path=None):
    """Load a saved model.

    Parameters
    ----------
    model_config_path: str
      The path to the model configuration yaml file. We have provided
      you this file for problems 2 and 3.
    model_weights_path: str, optional
      If specified, will load keras weights from hdf5 file.

    Returns
    -------
    keras.models.Model
    """
    with open(model_config_path, 'r') as f:
        model = model_from_yaml(f.read())

    if model_weights_path is not None:
        model.load_weights(model_weights_path)

    model.summary()

    return model


def generate_expert_training_data(expert, env, num_episodes=100, render=True):
    """Generate training dataset.

    Parameters
    ----------
    expert: keras.models.Model
      Model with expert weights.
    env: gym.core.Env
      The gym environment associated with this expert.
    num_episodes: int, optional
      How many expert episodes should be run.
    render: bool, optional
      If present, render the environment, and put a slight pause after
      each action.

    Returns
    -------
    expert_dataset: ndarray(states), ndarray(actions)
      Returns two lists. The first contains all of the states. The
      second contains a one-hot encoding of all of the actions chosen
      by the expert for those states.
    """

    obs=env.reset()
    obs_net=np.expand_dims(obs,axis=0)
    states=np.zeros([1,4])
    actions=np.zeros([1,2])
    episode_no=0
    step=1
    total_reward=0
    while episode_no < num_episodes:

        act=np.zeros(2,)
        act_idx=np.argmax(expert.predict(obs_net,batch_size=1))
        act[act_idx]=1
        states=np.append(states,obs_net,axis=0)
        act_net=np.expand_dims(act,axis=0)
        actions=np.append(actions,act_net,axis=0)
        obs,reward,terminal,_=env.step(act_idx)
        obs_net=np.expand_dims(obs,axis=0)
        # env.render()
        # time.sleep(0.1)

        if terminal:
            print ("Terminal")
            obs=env.reset()
            obs_net=np.expand_dims(obs,axis=0)
            episode_no+=1
            print ("Episode number %d" % (episode_no))

        step+=1
        total_reward+=reward


    return states, actions

def main1():
    
    model=load_model("./CartPole-v0_config.yaml","./CartPole-v0_weights.h5f")
    env=gym.make("CartPole-v0")
    states,actions=generate_expert_training_data(model,env,num_episodes=100)
    imitating_model=load_model("./CartPole-v0_config.yaml")
    optimizer=adam(lr=0.001, beta_1=0.9, beta_2=0.999, epsilon=1e-08, decay=0.0)
    imitating_model.compile(optimizer,loss='mean_squared_error')
    imitating_model.fit(states,actions,batch_size=1,verbose=1)
    print("Model trained")
    # env=wrap_cartpole(env)
    # test_cloned_policy(env,model,render=False)
    # test_cloned_policy(env,imitating_model,render=False)
    dagger_generate_data(imitating_model, model,env)

def main2():

    model=load_model("./CartPole-v0_config.yaml","./CartPole-v0_weights.h5f")
    env=gym.make("CartPole-v0")
    states,actions=generate_expert_training_data(model,env,num_episodes=100)
    imitating_model=load_model("./CartPole-v0_config.yaml")
    optimizer=adam(lr=0.001, beta_1=0.9, beta_2=0.999, epsilon=1e-08, decay=0.0)
    imitating_model.compile(optimizer,loss='mean_squared_error')
    
    env0=wrap_cartpole(env)
    # test_cloned_policy(env,model,render=False)
    # test_cloned_policy(env,imitating_model,render=False)

    for i in range(10):

        imitating_model.fit(states,actions,batch_size=1,epochs=5,verbose=1)
        print("Model trained")
        dag_states, dag_actions=dagger_generate_data(imitating_model, model, env)
        states=np.append(states, dag_states,axis=0)
        actions=np.append(actions, dag_actions,axis=0)
        test_cloned_policy(env0,imitating_model,render=False)





def dagger_generate_data(train_model,expert_model,env,no_episodes=20):

    obs=env.reset()
    obs_net=np.expand_dims(obs,axis=0)
    states=np.zeros([1,4])
    actions=np.zeros([1,2])
    episode_no=0

    while episode_no<no_episodes:

        act=np.zeros(2)
        act_idx=np.argmax(train_model.predict(obs_net,batch_size=1))
        states=np.append(states,obs_net,axis=0)
        act_idx_exp=np.argmax(expert_model.predict(obs_net,batch_size=1))
        act[act_idx_exp]=1
        # if act_idx!=act_idx_exp:
        #     print ("Train action:%d, Expert action:%d" % (act_idx,act_idx_exp))
        act_net=np.expand_dims(act,axis=0)
        actions=np.append(actions,act_net,axis=0)
        obs,_,terminal,_=env.step(act_idx)
        obs_net=np.expand_dims(obs,axis=0)

        if terminal:
            obs=env.reset()
            obs_net=np.expand_dims(obs,axis=0)
            episode_no+=1


    return (states,actions)






def test_cloned_policy(env, cloned_policy, num_episodes=50, render=True):
    """Run cloned policy and collect statistics on performance.

    Will print the rewards for each episode and the mean/std of all
    the episode rewards.

    Parameters
    ----------
    env: gym.core.Env
      The CartPole-v0 instance.
    cloned_policy: keras.models.Model
      The model to run on the environment.
    num_episodes: int, optional
      Number of test episodes to average over.
    render: bool, optional
      If true, render the test episodes. This will add a small delay
      after each action.
    """
    total_rewards = []

    for i in range(num_episodes):
        print('Starting episode {}'.format(i))
        total_reward = 0
        state = env.reset()
        if render:
            env.render()
            time.sleep(.1)
        is_done = False
        while not is_done:
            action = np.argmax(
                cloned_policy.predict_on_batch(state[np.newaxis, ...])[0])
            state, reward, is_done, _ = env.step(action)
            total_reward += reward
            if render:
                env.render()
                time.sleep(.1)
        print(
            'Total reward: {}'.format(total_reward))
        total_rewards.append(total_reward)

    print('Average total reward: {} (std: {})'.format(
        np.mean(total_rewards), np.std(total_rewards)))


def wrap_cartpole(env):
    """Start CartPole-v0 in a hard to recover state.

    The basic CartPole-v0 starts in easy to recover states. This means
    that the cloned model actually can execute perfectly. To see that
    the expert policy is actually better than the cloned policy, this
    function returns a modified CartPole-v0 environment. The
    environment will start closer to a failure state.

    You should see that the expert policy performs better on average
    (and with less variance) than the cloned model.

    Parameters
    ----------
    env: gym.core.Env
      The environment to modify.

    Returns
    -------
    gym.core.Env
    """
    unwrapped_env = env.unwrapped
    unwrapped_env.orig_reset = unwrapped_env._reset

    def harder_reset():
        unwrapped_env.orig_reset()
        unwrapped_env.state[0] = np.random.choice([-1.5, 1.5])
        unwrapped_env.state[1] = np.random.choice([-2., 2.])
        unwrapped_env.state[2] = np.random.choice([-.17, .17])
        return unwrapped_env.state.copy()

    unwrapped_env._reset = harder_reset

    return env


if __name__ == "__main__":

    main2()
