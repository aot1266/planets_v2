import gym
from Game_core_v1 import game 
from gym import spaces
import pygame as pg

class GameEnv(gym.Env):
  """Custom Environment that follows gym interface"""
  metadata = {'render.modes': ['human']}

  def __init__(self, arg1, arg2, ...):
    super(CustomEnv, self).__init__()
    # Define the game class
    player_main = player(np.array([0.0,0.0]), np.array([0.0,0.0]), 2.0, [np.array([0.0,0.1])], [], [1,1,1])
    self.game_main = game(player_main, "input_data_demo.json", "stars_data.json", screen)
    #game load step
    self.game_main.load_step()
    
    # Define action and observation space
    # They must be gym.spaces objects
    # Example when using discrete actions:
    # move actions vector len 4 + action keys len 4 and aim keys len 4 
    N_DISCRETE_ACTIONS = 12
    self.action_space = spaces.Discrete(N_DISCRETE_ACTIONS,)
    # Example for using image as input:
    self.observation_space = spaces.Box(low=0, high=255,
                                        shape=(HEIGHT, WIDTH, N_CHANNELS), dtype=np.uint8)

  def step(self, action):
    self.game_main.step()
    return observation, reward, done, info

  def reset(self):
    self.game_main.screen.fill((0, 0, 0))
    self.game_main.load_step()
    return observation  # reward, done, info can't be included

  def render(self, mode='human'):
    self.game_main.screen.fill((0, 0, 0))
    self.game_main.screen_step()
    pg.display.flip()
    
  def close (self):
    pass