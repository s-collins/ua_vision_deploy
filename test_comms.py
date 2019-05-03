from Robot import Robot
from Obstacle import Obstacle

import time

if __name__ == '__main__':
	robot = Robot()
	while True:
		robot.add_obstacle(Obstacle(1, 1))
		robot.add_obstacle(Obstacle(2, 2))
		robot.add_obstacle(Obstacle(3, 3))
		robot.send_obstacles()
		time.sleep(0.2)


