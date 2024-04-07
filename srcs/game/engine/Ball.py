import numpy as np
import random
import math
from time import sleep

from constants import ARENA_WIDTH, ARENA_HEIGHT, BALL_SPEED, BALL_RADIUS, PLAYER_WIDTH, PLAYER_LENGTH, CENTER_X, CENTER_Y

class Ball:
	def __init__(self, debug):
		self.reset()
		self.debug = debug

	def reset(self):
		self.position = [CENTER_X, CENTER_Y]

		random_angle = random.uniform(0, 2 * math.pi)
		self.direction = [math.cos(random_angle), math.sin(random_angle)]

		self.speed = BALL_SPEED
		self.start = True

	def render(self):
		debug_info = {}
		if self.debug:
			debug_info['has_wall_collision'] = self.has_wall_collision
			debug_info['next_positions'] = self.next_positions
			debug_info['wall_collisionned'] = self.wall_collisionned
			debug_info['collision_infos'] = self.collision_infos
		return {
			'posx': self.position[0],
			'posy': self.position[1],
			'radius': BALL_RADIUS,
			'debug': debug_info
		}

	def update(self, timestamp, players, walls):
		if self.position[0] - BALL_RADIUS <= 0 or self.position[0] + BALL_RADIUS >= ARENA_WIDTH or self.position[1] - BALL_RADIUS <= 0 or self.position[1] + BALL_RADIUS >= ARENA_HEIGHT:
			self.reset()

		if self.debug:
			self.has_wall_collision = False
			self.next_positions = []
			self.wall_collisionned = []
			self.collision_infos = []
		new_dir = self.direction
		next_position = None
		speed_factor = 1
		is_collision = False
		while new_dir is not None:
			next_position = [
				self.position[0] + new_dir[0] * self.speed * timestamp * speed_factor,
				self.position[1] + new_dir[1] * self.speed * timestamp * speed_factor
			]
			self.next_positions.append(next_position)

			new_dir = self.handle_walls_collisions(walls, next_position)

			if new_dir is None:
				new_dir = self.handle_player_collisions(players, next_position)

			if new_dir is not None:
				is_collision = True
				new_dir = new_dir / np.linalg.norm(new_dir)
				self.direction = new_dir
				speed_factor *= 1.1
		if self.speed <= 500 and is_collision:
			self.speed += 10
		self.position = next_position

	def find_distance(a,b):
		return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)

	def is_between(a,c,b):
		return Ball.find_distance(a,c) + Ball.find_distance(c,b) == Ball.find_distance(a,b)

	def handle_walls_collisions(self, walls, next_position):
		for wall in walls:
			if self.has_wall_intersection(wall, next_position):
				if self.debug:
					self.has_wall_collision = True
					self.wall_collisionned.append(wall)
				A = np.array(wall[0])
				B = np.array(wall[1])
				wall_vect = B - A
				normal_vect =  np.array([-wall_vect[1], wall_vect[0]])
				normal_vect = normal_vect / np.linalg.norm(normal_vect)
				dot_product = np.dot(self.direction, normal_vect)
				return self.direction - 2 * dot_product * normal_vect
		return None

	def has_wall_intersection(self, line_points, ball_position):
		A = np.array(line_points[0])
		B = np.array(line_points[1])
		O = np.array(ball_position)
		d = B - A
		OA = A - O

		a = np.dot(d, d)
		b = 2 * np.dot(d, OA)
		c = np.dot(OA, OA) - BALL_RADIUS**2
		delta = b**2 - 4*a*c

		if delta < 0:
			return False
		t = [(-b + math.sqrt(delta)) / (2 * a), (-b - math.sqrt(delta)) / (2 * a)]
		d_norm = np.linalg.norm(d)
		self.collision_infos.append({
			't': t,
			'd_norm': d_norm
		})
		if (t[0] > 0 and t[0] < 1) or (t[1] > 0 and t[1] < 1):
			return True
		return False

	def handle_player_collisions(self, players, next_position):
		for i in players:
			player = players[i]
			if self.has_wall_intersection(player.get_sides(), next_position):
				print("Collision with player")
				if self.debug:
					self.has_wall_collision = True
					self.wall_collisionned.append(player.get_sides())
				P = np.array(player.get_center())
				O = np.array(next_position)
				new_direction = O - P # <3
				return [new_direction[0], new_direction[1]]
		return None
