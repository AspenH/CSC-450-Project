"""
	Programmed by: Slate Hayes
"""

import math
import cv2
import numpy as np

def get_fingers(roi, inv=False):
	"""
		Programmed by: Slate Hayes
	"""

	# Resize the frame we're given from the server so that detection is more precise
	try:
		roi = cv2.resize(roi, (200, 200))
	except:
		return -1

	# We need to get a thresholded image of the region of interest in order to find the contours and defects
	processed_roi = process_roi(roi, inv)

	hand_contour = get_hand_contour(processed_roi)

	# Finding the palm is useful for distinguishing between no hand, a fist, and one finger being held up
	palm = get_palm_coords(hand_contour)

	hand_hull = cv2.convexHull(hand_contour, returnPoints=False)

	# We'll be using the width and height of the bounding rectangle around the hand contour to aid in defect-validation
	hand_bx, hand_by, hand_bw, hand_bh = cv2.boundingRect(hand_contour)

	defects = cv2.convexityDefects(hand_contour, hand_hull)

	# 'Candidates' is a list of potential lines that indicate that one finger is being held up, we filter this list when doing the one finger check
	candidates = []

	# If we get an error when figuring out how many fingers are being held up, it is fine to just return that no hand was found
	try:
		num_defects = filter_defects(hand_contour, defects, candidates, palm, hand_bw)

		# Upon finding more than one finger, we know that the number of fingers being held up is the number of defects found + 1.
		# Also, we are checking that the bounding rectangle of the hand contour doesn't have the same area as the region of interest.
		# This is so that we enforce that the hand is contained completely within the region of interest.
		if num_defects > 0 and hand_bw*hand_bh != 40000:
			return num_defects + 1
		else:
			return one_finger_check(candidates, palm, hand_bw, hand_bh)
	except AttributeError:
		return -1

def process_roi(roi, inv=False):
	"""
		Programmed by: Slate Hayes
	"""

	gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

	# All arguments except for the first can be played around with to get a better filter (10, 75, 75 are just what I've found to work well)
	bilat = cv2.bilateralFilter(gray, 10, 75, 75)

	# If the hand is darker than the background (e.g. you have a white backdrop), we should invert the binary threshold we use
	if inv == False:
		ret, thresh = cv2.threshold(bilat, 70, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
	else:
		ret, thresh = cv2.threshold(bilat, 70, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

	return thresh

def get_hand_contour(processed_frame):
	"""
		Programmed by: Slate Hayes
	"""

	ret, contours, hierarchy = cv2.findContours(processed_frame, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

	# In our case, the hand held up inside the region of interest should have the largest area out of all the found contours
	max_contour = max(contours, key = lambda c: cv2.contourArea(c))

	return max_contour

def get_palm_coords(hand_contour):
	"""
		Programmed by: Slate Hayes
	"""
	
	# No idea what 'moments' means, but this gives us the (x, y) coordinates of the palm
	moments = cv2.moments(hand_contour)
	if moments['m00'] != 0:
		cx = int(moments['m10']/moments['m00'])
		cy = int(moments['m01']/moments['m00'])
		
	return (cx, cy,)

def filter_defects(hand_contour, defects, candidates, palm, h_bw):
	"""
		Programmed by: Slate Hayes
	"""
	
	num_defects = 0

	for index in range(defects.shape[0]):
		s, e, f, d = defects[index, 0]

		# 'Start' and 'end' are the tips of the fingers that the defect is between
		start = tuple(hand_contour[s][0])
		end = tuple(hand_contour[e][0])

		# 'Far' is the valley between those fingers
		far = tuple(hand_contour[f][0])

		# These are the sides of the triangle that make up the area between the fingers being considered for the defect
		side_a = get_distance(end[0], end[1], start[0], start[1])
		side_b = get_distance(far[0], far[1], start[0], start[1])
		side_c = get_distance(end[0], end[1], far[0], far[1])

		angle = angle_between_fingers(side_a, side_b, side_c)

		# The angle between the fingers should be less than (or equal to) 90 degrees and the lengths of the fingers should be proportional to some coefficient (can be experimented with)
		if angle <= 90 and palm[1] - start[1] > 0 and side_b > h_bw/10000 and side_c > h_bw/10000:
			num_defects += 1
		else:
			# If the length between the palm and the tip of the finger is > 0, it might be just one raised finger
			if palm[1] - start[1] > 0:
				candidates.append(((start[0], start[1],),(far[0], far[1],),))

	return num_defects

def one_finger_check(candidates, palm, h_bw, h_bh):
	"""
		Programmed by: Slate Hayes
	"""

	# If we have some possibilities for a single raised finger and it's within the region of interest, get the one that is furthest from the palm
	if len(candidates) > 0 and h_bw != 200 and h_bh != 200:
		furthest_len = max(candidates, key=lambda p: get_distance(palm[0], palm[1], p[0][0], p[0][1]))
	else:
		# If the bounding rectangle is the same area as the region of interest, we say that no hand was found
		if h_bw == 200 or h_bh == 200:
			return -1
		# Otherwise, the hand is probably just a closed fist
		else:
			return 0

	# Now we want to see what the angle between the raised finger and the x axis (starting at the palm) is
	furthest_angle = math.atan((palm[1]-furthest_len[0][1])/(palm[0]-furthest_len[0][0])) * 180 / math.pi

	# If the angle is between 50 and 90 degrees and the distance is within some threshold (threshold is an arbitrary coefficient of proportionality that I found to work) then it's a raised finger
	if furthest_angle < 90 and furthest_angle > 50 and get_distance(palm[0], palm[1], furthest_len[0][0], furthest_len[0][1]) > h_bw/36000 and h_bw != 200 and h_bh != 200:
		return 1
	# Same as before, if the hand is not contained within the region of interest, it's invalid
	elif h_bw == 200 or h_bh == 200:
		return -1
	# Otherwise, it's most likely a closed fist.
	else:
		return 0

def get_distance(x1, y1, x2, y2):
	"""
		Programmed by: Slate Hayes
	"""

	return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
	
def angle_between_fingers(side_a, side_b, side_c):
	"""
		Programmed by: Slate Hayes
	"""

	return math.acos((side_b ** 2 + side_c ** 2 - side_a ** 2) / (2 * side_b * side_c)) * 180 / math.pi
