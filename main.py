import pysrt, nltk
import string, os, csv, random, re, glob, pickle, gc
from bisect import bisect
import moviepy.editor as mpy
from enum import Enum
from collections import Counter

TAG_RE = re.compile(r'<[^>]+>')

def remove_tags(text):
    return TAG_RE.sub('', text)

def subFormat(txt):
	return remove_tags(txt).encode('utf-8') \
              .replace('\n', ' ') \
              .lstrip()

class PhraseType(Enum):
	unknown = -1
	statement = 0
	shortQuestion = 1
	longQuestion = 2
	response = 3
	yes = 4
	no = 5
	maybe = 6


class Subtitle:
	def __extractSubtype(self, sentence):
		# REMOVE THIS MAYBE?
		return PhraseType.unknown

		try:
			tokens = nltk.word_tokenize(sentence)
			tagged = nltk.pos_tag(tokens)
		except:
			print "failed on sentence: " + sentence
			return PhraseType.unknown
		
		if (sentence[-1] == '?'):
			if (len(tokens) < 6):
				return PhraseType.shortQuestion
			else:
				return PhraseType.longQuestion
		[words, tags] = zip(*tagged)
		if ('UH' in tags):
			interjection = words[tags.index('UH')].lower()
			if (interjection == 'yes' or interjection == 'yeah'):
				if (len(tokens) < 4):
					return PhraseType.yes
				else:
					return PhraseType.unknown
			if (interjection == 'no'):
				return PhraseType.no


		return PhraseType.unknown

	def __init__(self, sub, prevSub, filename):
		self.timeStart = timeToSeconds(sub.start)
		self.timeEnd = timeToSeconds(sub.end)

		base = os.path.basename(filename)
		self.filename = os.path.splitext(base)[0]
		
		self.text = subFormat(sub.text)
		self.textWordsOnly = self.text.strip(string.punctuation)
		self.split = self.text.split()
		self.words = self.textWordsOnly.split()
		self.phraseType = self.__extractSubtype(self.text)

	def __str__(self):
		return self.filename + " (" + str(self.timeStart) + "," + \
			   str(self.timeEnd) + ") \"" + self.text + "\""

	def getWordFrequency(self):
		return Counter(self.words)


def timeToSeconds(timeObj):
	return timeObj.seconds + 60*(timeObj.minutes) + 3600*(timeObj.hours) + timeObj.milliseconds/1000.0

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

def parseSubs(subtitles):
	for filename in os.listdir("subs"):
		subtitles[filename] = []
		print ("Parsing srt file: " + filename)
		subs = pysrt.open('subs/'+filename)
		for sub in subs:
			if (len(sub.text.split()) == 0): continue
			CurrentSubtitle = Subtitle(sub, filename)
			subtitles[filename].append(CurrentSubtitle)

def getFilename(filenameBase):
	path = "movies/" + filenameBase + ".*"
	matches = glob.glob(path)
	if (len(matches) == 1):
		return matches[0]
	else:
		return ""

def writeClips(selectedSubtitles):
	clips = []
	count = 0
	superclips = 0
	for CurrentSubtitle in selectedSubtitles:
		print CurrentSubtitle
		movieFilename = getFilename(CurrentSubtitle.filename)
		clip = mpy.VideoFileClip(movieFilename).subclip(CurrentSubtitle.timeStart,CurrentSubtitle.timeEnd)
		clips.append(clip)
		count += 1
		if (count == 50):
			superClip = mpy.concatenate_videoclips(clips, method="compose")
			superClip.write_videofile("superclip" + str(superclips) + ".mp4")
			superClip = None
			clips = []
			gc.collect()
			count = 0
			superclips += 1

	print "Concatenating clips"
	superClip = mpy.concatenate_videoclips(clips, method="compose")
	print "Writing final clip"
	superClip.write_videofile("superclip" + str(superclips) + ".mp4")

def main():
	movieSubtitles = {} # dictionary of movie to subtitle mappings
	n = 10
	if (os.path.isfile('data.pickle')):
		with open('data.pickle', 'rb') as f:
			movieSubtitles = pickle.load(f)
	else:
		parseSubs(movieSubtitles)
		with open('data.pickle', 'wb') as f:
			pickle.dump(movieSubtitles, f, pickle.HIGHEST_PROTOCOL)
	print movieSubtitles
	for movie in movieSubtitles:
		subtitles = movieSubtitles[movie]
		frequencies = Counter()
		for subtitle in subtitles:
			frequencies += subtitle.getWordFrequency()
		print "top " + str(n) + "word frequencies for " + subtitles[0].filename
		print frequencies.most_common(n)



	'''
	selectedSubtitles = []
	#questionSubtitles = filter(lambda s: s.phraseType == PhraseType.shortQuestion, subtitles)
	yesSubtitles = filter(lambda s: s.phraseType == PhraseType.yes, subtitles)
	#noSubtitles = filter(lambda s: s.phraseType == PhraseType.no, subtitles)

	#for i in xrange(20):
		#selectedSubtitles.append(random.choice(questionSubtitles))
		#yes = random.choice(yesSubtitles)
		#no = random.choice(noSubtitles)
		#selectedSubtitles.append(random.choice(yesSubtitles))
	random.shuffle(yesSubtitles)
	writeClips(yesSubtitles)
	'''

if __name__ == "__main__":
	main()	
