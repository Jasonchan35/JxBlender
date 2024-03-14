import sys

FLT_EPSILON = 1.192092896e-07

def almost_eq(a, b):
	return abs(a - b) <= FLT_EPSILON

def almost_eq0(a):
	return abs(a) <= FLT_EPSILON
