import pysrt
import string, os
import random, re
from bisect import bisect

TAG_RE = re.compile(r'<[^>]+>')

def remove_tags(text):
    return TAG_RE.sub('', text)

def subFormat(txt):
	return remove_tags(txt).encode('utf-8') \
			  .translate(None, string.punctuation) \
              .replace('\n', ' ') \
              .lstrip()

class Subtitle:
	def __init__(self, sub, filename):
		self.timeStart = timeToSeconds(sub.start)
		self.timeEnd = timeToSeconds(sub.end)
		self.filename = filename
		self.text = subFormat(sub.text)
		self.words = self.text.split()
		self.key = self.words[0]

	def getKey(self):
		return self.key

	def getLastWords(self, order):
		return " ".join(self.words[-order:])
	def __str__(self):
		return self.filename + " (" + str(self.timeStart) + "," + \
			   str(self.timeEnd) + ") \"" + self.text + "\""

def timeToSeconds(timeObj):
	return timeObj.seconds + 60*(timeObj.minutes) + 60*(timeObj.hours)

def weightedChoice(choices):
    values, weights = zip(*choices.items())
    total = 0
    cum_weights = []
    for w in weights:
        total += w
        cum_weights.append(total)
    x = random.random() * total
    i = bisect(cum_weights, x)
    return values[i]

def randomChoice(choices):
	return random.choice(choices)
	

def main():
	# dictionary of all subtitles, keyed by their first word
	d = {}
	order = 2
	subOrder = []
	for filename in os.listdir("subs"):
		subs = pysrt.open('subs/'+filename)
		for sub in subs:
			CurrentSubtitle = Subtitle(sub, filename)
			key = CurrentSubtitle.getKey()
			#print "<" + key,
			#print CurrentSubtitle.getLastWords(order) + ">",
			#print CurrentSubtitle.text
			# if the current starting word exists in the dictionary,
			# add an additional subtitle object to the list of already
			# existing subtitles that start with that word
			if (key in d):
				d[key].append(CurrentSubtitle)
			else:
				d[key] = [CurrentSubtitle]
			# record subtitle in order
			subOrder.append(CurrentSubtitle)
	
	# now we want to construct a markov chain based on the last n words
	# of a subtitle, and the most likely next word it should transition to
	PrevSubtitle = None
	# an element in markov "sentence": {"word1": count1, "word2": count2}
	markov = {}
	for CurrentSubtitle in subOrder:
		if PrevSubtitle != None:
			firstWord = CurrentSubtitle.getKey()
			lastWords = PrevSubtitle.getLastWords(order)
			if lastWords in markov:
				if firstWord in markov[lastWords]:
					markov[lastWords][firstWord] += 1
				else:
					markov[lastWords][firstWord] = 1
			else:
				markov[lastWords] = {firstWord: 1}
		PrevSubtitle = CurrentSubtitle
	
	CurrentSubtitle = subOrder[0]
	for i in xrange(100):
		print(CurrentSubtitle)
		lastWords = CurrentSubtitle.getLastWords(order)
		transitions = markov[lastWords]
		# get weighted choice
		nextWord = weightedChoice(transitions)
		possibleSubtitles = d[nextWord]
		CurrentSubtitle = randomChoice(possibleSubtitles)
		
			
				

if __name__ == "__main__":
	main()	
