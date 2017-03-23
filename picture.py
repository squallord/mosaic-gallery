import utils, math
import constants as ct
from PIL import ExifTags

class Picture:
	def __init__(self, path, image, number):
		self._path = path
		self._image = utils.changeAR(image)
		self._ar = float(image.size[0])/image.size[1]
		self._chunkType = (0, 0)
		self._position = (0, 0)
		self._id = number
		
	def getImage(self):
		return self._image

	def getPath(self):
		return self._path

	def getAR(self):
		return self._ar

	def getChunkType(self):
		return self._chunkType

	def getPosition(self):
		return self._position

	def getID(self):
		return self._id

	# Adds internal padding to the image.
	#
	def addPadding(self, padding = ct.DEF_PADDING):
		self._image = utils.addPaddingIn(self._image, padding)

	# Print photo ID in the upper-left corner of the image.
	# Just for debugging reasons...
	#
	def addID(self):
		self._image = utils.drawText(self._image, "ID: " + str(self._id))

	def setPosition(self, position):
		self._position = position

	# This method was not used, but could be useful in the future.
	#
	def _fetchExifData(self, image):
		ret = {}
		info = image._getexif()
		if info is not None:
			for tag, value in info.items():
				decoded = ExifTags.TAGS.get(tag, tag)
				ret[decoded] = value
			return ret

	# A quick way to fix orientation issues based on image EXIF data.
	# Another method that wasn't used.
	#
	def _correctImageOrientation(self, image, number):
		data = self._fetchExifData(image)
		if data is not None and 'Orientation' in data:
			if not data['Orientation']:
				return image.rotate(90, expand = True)
		return image

	def isDowngradable(self):
			if self._chunkType == ct.CHUNK_TYPE_2x4 or self._chunkType == ct.CHUNK_TYPE_2x2:
				return True
			else:
				return False

	def reshape(self, n):
		self._chunkType = (self._chunkType[0]/n, self._chunkType[1]/n)
		self._image = self._image.resize((self._image.size[0]/n, self._image.size[1]/n))

	# Print all picture data.
	# Just for debugging reasons...
	#
	def printData(self):
		print ""
		print "id: " + str(self._id)
		print "path: " + self._path
		print "size: " + str(self._image.size)
		print "chunkType: " + str(self._chunkType)
		print "AR: " + str(round(self._ar, 2))

	def amPortrait(self):
		if self._ar <= 1:
			return True
		else:
			return False

	def isPortrait(self, imageSize):
		if float(imageSize[0])/imageSize[1] <= 1:
			return True
		else:
			return False

	# Compares the picture with the corresponding chunk.
	# Expects a corrected chunk so that the chunk is given by the tuple
	# (width, height) instead of (row, col) and it needs to be in pixels
	# units instead of cluster units.
	#
	def _isGreater(self, correctedChunk):
		width, height = self._image.size
		if width > correctedChunk[0] and height > correctedChunk[1]:
			return True
		else:
			return False

	# 
	# 
	def _findDistance(self, p):
		return math.sqrt((p[0] - self._image.size[0]) ** 2 + (p[1] - self._image.size[1]) ** 2)

	def _findClosestResolution(self, distances):
		closest = distances[0]
		for d in distances:
			if d[0] < closest[0]:
				closest = d
		return (closest[1], closest[2])

	# Remember that chunk width and height are swapped in the tuple
	# just to fit in ImageCanvas row/col cluster convention.
	# The same goes for smallestChunk.
	#
	def resizeToClosestChunk(self, chunks, smallestChunk):
		distances = []
		for chunk in chunks:
			c = (chunk[1], chunk[0])
			if self.amPortrait() and self.isPortrait(c) or not self.amPortrait() and not self.isPortrait(c):
				if self._isGreater(c):
					distances.append((self._findDistance(c), c[0], c[1]))
		
		try:
			closestResolution = self._findClosestResolution(distances)
		except ValueError:
			print "There's no closest chunck to image at " + self._path
		
		chunkClusterWidth = closestResolution[0]/smallestChunk[1]
		chunkClusterHeight = closestResolution[1]/smallestChunk[0]
		self._chunkType = (chunkClusterHeight, chunkClusterWidth)
		self._image = self._image.resize(closestResolution)
		self._ar = float(closestResolution[0])/closestResolution[1]