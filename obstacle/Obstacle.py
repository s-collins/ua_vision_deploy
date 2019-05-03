import struct

class Obstacle:
	def __init__(self, x_coord, y_coord):
		self.x_coord = bytearray(struct.pack(">H", x_coord))
		self.y_coord = bytearray(struct.pack(">H", y_coord))

	def first_x_byte(self):
		return self.x_coord[0]

	def second_x_byte(self):
		return self.x_coord[1]

	def first_y_byte(self):
		return self.y_coord[0]

	def second_y_byte(self):
		return self.y_coord[1]
