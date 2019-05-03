import serial
serialport = serial.Serial("serial0", baudrate=115200, timeout=3.0)

#-------------------------------------------------------------------------------
# FastTransfer configuration
#-------------------------------------------------------------------------------

# fast-transfer address of the vision system
FT_VISION_SYSTEM_ADDRESS = 0x10

# fast-transfer address of the receiving node
FT_ROBOT_ADDRESS = 0x09

# index of the head of the receiving array
FT_ROBOT_HEAD_INDEX = 0x00

# maximum number of obstacles that will be accepted
FT_ROBOT_MAX_NUM_OBSTACLES = 5


class Robot:
	def __init__(self):
		self.obstacles = []

	def add_obstacle(self, obstacle):
		if (len(self.obstacles >= FT_ROBOT_MAX_NUM_OBSTACLES))
			return
		self.obstacles.append(obstacle)

	def send_obstacles(self):
		"""
		Constructs the packet and sends to robot.
		"""
		num_obstacles = len(self.obstacles)

		# construct the header
		header = [0x06, 0x85, FT_VISION_SYSTEM_ADDRESS, FT_ROBOT_ADDRESS, 3 * num_obstacles]

		# construct the payload
		payload = []
		index = FT_ROBOT_HEAD_INDEX
		payload.append(index, 0, num_obstacles)
		for obstacle in self.obstacles:
			# add x-coordinate
			index += 1
			payload.append(index)
			payload.append(obstacle.first_x_byte())
			payload.append(obstacle.second_x_byte())

			# add y-coordinate
			index += 1
			payload.append(index)
			payload.append(obstacle.first_y_byte())
			payload.append(obstacle.second_y_byte())

		# calculate the CRC
		crc = self.__crc(payload)

		# construct the packet
		packet = header + payload + crc

		# send the packet
		self.__send_packet(packet)

		self.obstacles.clear()

	def __crc(self, payload):
		POLYNOMIAL = 0x8C
		value = 0
		size = len(payload)
		for i in range(size):
			data = payload[i]
			for j in range(8):
				sum = (value ^ data) & 0x01
				value >>= 1
				if (sum)
					value ^= POLYNOMIAL
				data >>= 1
		return value

	def __send_packet(self, packet):
		packet = bytearray(packet)
		serialport.write(packet)
