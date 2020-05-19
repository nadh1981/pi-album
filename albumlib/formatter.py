import datetime
class Formatter():
	# def __init__(self):
		# self = self

	def formatDate(datestring):
		date = datestring.split('T')[0]
		date = datetime.datetime.strptime(date, '%Y-%m-%d')
		date = date.strftime('%A %d %B')
		return (date)