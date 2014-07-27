def compute_timepost_day(user):
	time_dict = {}
	follow_list = user.user.all()

	for follow in follow_list:
		if follow.follower.timestamp:
			f_datetime = follow.follower.timestamp_datetime
			if not f_datetime == -1:
				hour = int(f_datetime.strftime('%H'))
				try:
					time_dict[hour] += 1
				except KeyError:
					time_dict.update({hour: 1})
	return time_dict
