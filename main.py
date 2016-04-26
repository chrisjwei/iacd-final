import pysrt, nltk
import string, os, csv, random, re, glob, pickle, gc, math
from bisect import bisect
import moviepy.editor as mpy
from enum import Enum
from collections import Counter

TAG_RE = re.compile(r'<[^>]+>')
PUNC_EXCLUDE = set(string.punctuation)
__USER_CHOICE = True

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

	def __init__(self, sub, filename):
		self.timeStart = timeToSeconds(sub.start)
		self.timeEnd = timeToSeconds(sub.end)

		base = os.path.basename(filename)
		self.filename = os.path.splitext(base)[0]
		
		self.text = subFormat(sub.text)
		self.textWordsOnly = ''.join(ch for ch in self.text if ch not in PUNC_EXCLUDE)
		self.split = self.text.split()
		self.words = self.textWordsOnly.split()
		self.counter = Counter(self.words)
		self.phraseType = self.__extractSubtype(self.text)

	def __str__(self):
		return self.filename + " (" + str(self.timeStart) + "," + \
			   str(self.timeEnd) + ") \"" + self.text + "\""

	def getWordFrequency(self):
		return self.counter


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

def writeClips(selectedSubtitles, outputBase):
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
			superClip.write_videofile(outputBase + str(superclips) + ".mp4")
			superClip = None
			clips = []
			gc.collect()
			count = 0
			superclips += 1

	print "Concatenating clips"
	superClip = mpy.concatenate_videoclips(clips, method="compose")
	print "Writing final clip"
	if (superclips > 0):
		superClip.write_videofile(outputBase + "_pt_" + str(superclips) + ".mp4")
	else:
		superClip.write_videofile(outputBase + ".mp4")
	superClip = None
	clips = []
	gc.collect()


def extractAndWriteClips(subtitles, word):
	selectedSubtitles = []
	for Subtitle in subtitles:
		if (Subtitle.getWordFrequency()[word] > 0):
			selectedSubtitles.append(Subtitle)
	writeClips(selectedSubtitles, subtitles[0].filename + "_" + word)

def main():
	movieSubtitles = {} # dictionary of movie to subtitle mappings
	n = 10
	if (os.path.isfile('data.pickle')):
		print "Found pickle file, using instead"
		with open('data.pickle', 'rb') as f:
			(movieSubtitles, movieFrequencies, totalFrequencies) = pickle.load(f)
	else:
		print "Parsing movie subtitles"
		parseSubs(movieSubtitles)
		# get the global counter for all movies
		print "Getting global word frequency"
		totalFrequencies = Counter()
		movieFrequencies = {}
		for movie in movieSubtitles:
			print "Parsing " + str(movie)
			subtitles = movieSubtitles[movie]
			currentMovieFrequencies = Counter()
			for subtitle in subtitles:
				currentMovieFrequencies += subtitle.getWordFrequency()
			for word in currentMovieFrequencies:
				totalFrequencies[word] += 1
			movieFrequencies[movie] = currentMovieFrequencies
		print "Pickling movie subtitles"
		with open('data.pickle', 'wb') as f:
			pickle.dump((movieSubtitles, movieFrequencies, totalFrequencies), f, pickle.HIGHEST_PROTOCOL)


	for movie in movieFrequencies:
		relativeFrequencies = {}
		currentMovieFrequencies = movieFrequencies[movie]
		(maxWord, maxWordFreq) = currentMovieFrequencies.most_common(1)[0]
		for word in currentMovieFrequencies:
			currentWordFreq = currentMovieFrequencies[word]
			tf = 0.5 + 0.5 * (currentWordFreq/(maxWordFreq + 0.0))
			idf = math.log(1 + (len(movieFrequencies.keys()) / (totalFrequencies[word] + 0.0)))
			tfidf = tf*idf
			relativeFrequencies[word] = tfidf
		counter = Counter(relativeFrequencies)
		#mostCommonWords, mostCommonWordsTfidf = zip(*counter.most_common(50))
		# remove all words with 
		filtered = \
				filter(\
				lambda (word, relfreq): currentMovieFrequencies[word] > 10 and\
				word[0].islower() \
				, counter.most_common(100))
		if (len(filtered) == 0):
			print "No interesting words found"
			continue
		mostCommonWords, mostCommonWordsTfidf = zip(*filtered)
		if __USER_CHOICE:
			i = 0
			for choice in mostCommonWords:
				print "(" + str(i) + ")" + choice + "[" + str(currentMovieFrequencies[choice]) + "]"
				i += 1
			i = input("Select a word to use or -1 to skip: ")
			if (i == -1):
				continue
			selectedWord = mostCommonWords[i]
		else:
			selectedWord = random.choice(mostCommonWords)
		print "rendering " + movie + " using the word " + selectedWord + " with frequency of " + str(currentMovieFrequencies[selectedWord])
		extractAndWriteClips(movieSubtitles[movie], selectedWord)
		

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
