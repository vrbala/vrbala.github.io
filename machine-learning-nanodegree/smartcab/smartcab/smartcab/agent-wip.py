import os
import random
from environment import Agent, Environment
from planner import RoutePlanner
from simulator import Simulator
from collections import defaultdict

class LearningAgent(Agent):
    """An agent that learns to drive in the smartcab world."""

    def __init__(self, env):
        super(LearningAgent, self).__init__(env)  # sets self.env = env, state = None, next_waypoint = None, and a default color
        self.color = 'red'  # override color
        self.planner = RoutePlanner(self.env, self)  # simple route planner to get next_waypoint
        # TODO: Initialize any additional variables here
        self.env = env

        # previous state, action and reward
        self.state = None
        self.action = None
        self.reward = None

        self.next_waypoint = None

        self.qTable = defaultdict(float)
        self.frequencies = defaultdict(int)
        self.real_deadline = None
        self.elapsed = 0
        self.total_reward = 0

        # global trial number. increment during reset
        self.trial_number = -1

        # when was the last mistake made
        self.trial_last_mistake = None

        # number of mistakes per trial
        self.mistakes_per_trial = 0

        # learning parameters
        self.alpha = None
        self.gamma = None

    def reset(self, destination=None):
        self.planner.route_to(destination)

        self.trial_number += 1
        # record the previous reward for analysis.
        with  open("./rl{}_{}_{}.out".format(os.getpid(), self.alpha, self.gamma), "a") as f:
            f.write("{} {} {} {} {}\n".format(self.reward, self.real_deadline, self.elapsed, self.trial_last_mistake, self.mistakes_per_trial))

        # TODO: Prepare for a new trip; reset any variables here, if required
        self.state = None
        self.action = None
        self.reward = None

        self.next_waypoint = None
        self.real_deadline = None
        self.elapsed = 0
        self.total_reward = 0
        self.mistakes_per_trial = 0

    def set_parameters(self, alpha, gamma):
        self.alpha = alpha
        self.gamma = gamma

    def choose_action1(self, state):

        # epsilon greedy algorithm
        epsilon = 0.1
        if random.random() < epsilon:
            # choosing a random action
            print "Exploration. choosing a random action."
            return random.choice(Environment.valid_actions)

        # bala --
        # using the following strategy for choosing action
        # for all the valid actions available, for a combination
        # of (state, action), if it hasn't been seen much, choose
        # a random action among those not seen much.
        # if all state-action pairs were seen already,
        # choose the one with max value of Q

        N_e = 5
        actions_explored_enough = []
        actions_not_explored_enough = []
        for a in Environment.valid_actions:
            if self.frequencies[(state, a)] > N_e:
                actions_explored_enough.append(a)
            else:
                actions_not_explored_enough.append(a)

        if len(actions_not_explored_enough) > 0:
            print "Not seen enough yet! Choosing a random action" # debug
            return random.choice(actions_not_explored_enough)

        # choose the best action possible from Q-table
        bestAV = max([(a, self.qTable[(state, a)]) for a in Environment.valid_actions], key=lambda x: x[1])
        print "Best Action Value Pair: {}".format(bestAV) # debug
        return bestAV[0]

    def choose_action(self, state):

        epsilon = 0.1
        if random.random() < epsilon:
            # choosing a random action
            print "Exploration. choosing a random action."
            return random.choice(Environment.valid_actions)
        else:
            # choose the best action possible from Q-table
            bestAV = max([(a, self.qTable[(state, a)]) for a in Environment.valid_actions], key=lambda x: x[1])
            if (bestAV[1] > 0.0):
                print "Best Action Value Pair: {} Next WP: {}".format(bestAV, self.next_waypoint) # debug
                return bestAV[0]
            else:
                print "No best action value pair yet! choosing random action."
                return random.choice(Environment.valid_actions)

    def update(self, t):
        # Gather inputs
        self.next_waypoint = self.planner.next_waypoint()  # from route planner, also displayed by simulator
        inputs = self.env.sense(self)
        deadline = self.env.get_deadline(self)

        if self.real_deadline is None:
            self.real_deadline = deadline

        self.elapsed += 1

        # TODO: Update state
        state = (self.next_waypoint, tuple(inputs.values()),)

        # TODO: Select action according to your policy
        action = self.choose_action1(state)

        # Execute action and get reward
        reward = self.env.act(self, action)

        self.total_reward += reward

        # record the last mistake
        if reward < 0:
            self.trial_last_mistake = self.trial_number
            self.mistakes_per_trial += 1

        # TODO: Learn policy based on state, action, reward
        alpha = self.alpha
        gamma = self.gamma
        if self.state is not None:
            key = (self.state, self.action)
            self.frequencies[key] += 1
            #self.qTable[key] += alpha * (self.frequencies[key]) * (self.reward + gamma * self.max_Q_for_actions(state) - self.qTable[key])
            #self.qTable[key] = reward + gamma * self.max_Q_for_actions(state)
            self.qTable[key] = (1-alpha)* self.qTable[key] + alpha * (self.reward + gamma * self.max_Q_for_actions(state))

            print "{}: freq: {} Q: {}".format(key, self.frequencies[key], self.qTable[key])

        # assign the previous values
        self.state = state
        self.action = action
        self.reward = reward

        print "LearningAgent.update(): deadline = {}, inputs = {}, action = {}, reward = {}".format(deadline, inputs, action, reward)  # [debug]

    def max_Q_for_actions(self, state):
        return max([self.qTable[(state, a)] for a in Environment.valid_actions])

def run():
    """Run the agent for a finite number of trials."""

    # Set up environment and agent
    e = Environment()  # create environment (also adds some dummy traffic)
    a = e.create_agent(LearningAgent)  # create agent
    e.set_primary_agent(a, enforce_deadline=False)  # set agent to track

    # Now simulate it
    sim = Simulator(e, update_delay=1.0)  # reduce update_delay to speed up simulation
    sim.run(n_trials=100)  # press Esc or close pygame window to quit


def run1():
    """Run the agent for a finite number of trials."""

    # Set up environment and agent
    e = Environment()  # create environment (also adds some dummy traffic)
    alphas = [1, 0.1, 0.01, 0.001]
    gammas = [float(x)/10 for x in range(1,10)]
    for x, y in [(x,y) for x in alphas for y in gammas]:
        a = e.create_agent(LearningAgent)  # create agent
        a.set_parameters(x,y)
        e.set_primary_agent(a, enforce_deadline=False)  # set agent to track

        # Now simulate it
        sim = Simulator(e, update_delay=0.01)  # reduce update_delay to speed up simulation
        sim.run(n_trials=100)  # press Esc or close pygame window to quit

if __name__ == '__main__':
    #run()
    run1()
