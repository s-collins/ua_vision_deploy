import math
import numpy
import yaml


class Grid:
	def __init__(self, filename):
		self.grid = None
		self.col_step = None
		self.row_step = None
		self.num_cols = None
		self.num_rows = None

		# open the input file and populate grid
		with open(filename) as input_file:
			data = yaml.load(input_file)
			self.col_step = data['col_step']
			self.row_step = data['row_step']
			self.num_cols = data['num_cols']
			self.num_rows = data['num_rows']

			self.grid = [[0 for row in range(self.num_rows)] for col in range(self.num_cols)]
			for point in data['points']:
				col_index = math.ceil(point['col_pixel'] / self.col_step)
				row_index = math.ceil(point['row_pixel'] / self.row_step)
				self.grid[col_index][row_index] = {
					'col_pixel': point['col_pixel'],
					'row_pixel': point['row_pixel'],
					'x': point['x_cm'],
					'y': point['y_cm']
				}

	def interpolate(self, col_pixel, row_pixel):
		"""
		Interpolates the world coordinates for given pixel coordinates.

		Inputs:
		  - u:  column pixel
		  - v:  row pixel
		"""
		u = col_pixel
		v = row_pixel

		# determine bounding box
		col_1 = int(u / self.col_step)
		col_2 = int(u / self.col_step + 1)
		row_1 = int(v / self.row_step)
		row_2 = int(v / self.row_step + 1)

		u1 = self.grid[col_1][row_1]['col_pixel']
		u2 = self.grid[col_2][row_1]['col_pixel']
		v1 = self.grid[col_1][row_1]['row_pixel']
		v2 = self.grid[col_1][row_2]['row_pixel']

		# interpolate the world x coordinate
		x11 = self.grid[col_1][row_1]['x']
		x21 = self.grid[col_2][row_1]['x']
		x12 = self.grid[col_1][row_2]['x']
		x22 = self.grid[col_2][row_2]['x']

		x_u_v1 = (u2 - u) / (u2 - u1) * x11 + (u - u1) / (u2 - u1) * x21
		x_u_v2 = (u2 - u) / (u2 - u1) * x12 + (u - u1) / (u2 - u1) * x22
		x_u_v = (v2 - v) / (v2 - v1) * x_u_v1 + (v - v1) / (v2 - v1) * x_u_v2

		# interpolate the world y coordinate
		y11 = self.grid[col_1][row_1]['y']
		y21 = self.grid[col_2][row_1]['y']
		y12 = self.grid[col_1][row_2]['y']
		y22 = self.grid[col_2][row_2]['y']

		y_u_v1 = (u2 - u) / (u2 - u1) * y11 + (u - u1) / (u2 - u1) * y21
		y_u_v2 = (u2 - u) / (u2 - u1) * y12 + (u - u1) / (u2 - u1) * y22
		y_u_v = (v2 - v) / (v2 - v1) * y_u_v1 + (v - v1) / (v2 - v1) * y_u_v2	

		return (int(x_u_v), int(y_u_v))

