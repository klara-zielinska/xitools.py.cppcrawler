from bisect import bisect_right


def flatten(l):
	return [item for sublist in l for item in sublist]


def _maxCommonPrefix(s1, s2):
	minlen = min(len(s1), len(s2))
	for i in range(minlen):
		if s1[i] != s2[i]: return s1[:i]
	return s1[:minlen]


def maxCommonPrefix(*strings):
	if not strings: return ""
	comPrefix = strings[0]
	for s in strings[1:]:
		comPrefix = _maxCommonPrefix(comPrefix, s)
	return comPrefix


def insertRangeSorted(ranges, begin, end):
	if begin is None:

		if end is None:
			del ranges[:]
			ranges.append((None, None))

		else:
			i = bisect_right(ranges, end, key=lambda s: s[0] or -1)
			if i > 0:
				if ranges[i-1][1]:
					end = max(end, ranges[i-1][1])
				else:
					end = None
				ranges[0] = (begin, end)
				del ranges[1:i]
			else:
				ranges.insert(0, (begin, end))
					
	else:
		i = bisect_right(ranges, begin, key=lambda s: s[0] or -1)
		intersectBegin = i
		if i > 0:
			if not ranges[i-1][1] or end is not None and end <= ranges[i-1][1]: 
				return
			if begin <= ranges[i-1][1]:
				begin = ranges[i-1][0]
				intersectBegin = i - 1
		if end is None:
			i = len(ranges)
		else:
			while i < len(ranges) and end >= ranges[i][0]:
				end = max(end, ranges[i][1])
				i += 1
		if i - intersectBegin > 0:
			i -= 1
			ranges[i] = (begin, end)
			del ranges[intersectBegin:i]
		else:
			ranges.insert(i, (begin, end))
