import pysrt, nltk
from nltk.corpus import cmudict
import string, os, csv, random, re, glob, pickle, gc, math, subprocess
from bisect import bisect
import moviepy.editor as mpy
import moviepy.video.fx.all as mpyfx
import numpy as np
from enum import Enum
from collections import Counter

TAG_RE = re.compile(r'<[^>]+>')
PUNC_EXCLUDE = set(string.punctuation)
__USER_CHOICE = False

def remove_tags(text):
    return TAG_RE.sub('', text)

def subFormat(txt):
	return remove_tags(txt).encode('ascii', 'ignore') \
              .replace('\n', ' ') \
              .lstrip()
	


class Subtitle:
	
	_CMUDICT = cmudict.dict()

	def __init__(self, sub, filename):
		self.start = sub.start
		self.end = sub.end
		self.timeStart = timeToSeconds(sub.start)
		self.timeEnd = timeToSeconds(sub.end)

		base = os.path.basename(filename)
		self.filename = os.path.splitext(base)[0]
		
		self.text = subFormat(sub.text)
		self.textWordsOnly = ''.join(ch for ch in self.text if ch not in PUNC_EXCLUDE)
		self.split = nltk.word_tokenize(self.text)
		self.words = nltk.word_tokenize(self.textWordsOnly)
		self.lastWord = self.words[-1]
		# extract pronunciation data
		vocalData = []
		for word in self.words:
			word = word.lower()
			if word in Subtitle._CMUDICT:
				vocalData.append(Subtitle._CMUDICT[word][0])
			else:
				vocalData = []
				break
		# if all went well in translating words to pronunciation, extract the
		# number of syllables
		if len(vocalData) > 0:
			self.numSyllable = 0
			for word in vocalData:
				# for each word in the vocal data, count the number of stress
				# characters to determine the number syllables
				self.numSyllable += len(list(y for y in word if y[-1].isdigit()))
			self.lastWordData = vocalData[-1]
		else:
			self.numSyllable = -1
			self.lastWordData = []
		

	def __str__(self):
		return self.filename + " (" + str(self.timeStart) + "," + \
			   str(self.timeEnd) + ") \"" + self.text + "\""

	def isRhyme(self, TargetSubtitle):
		p1 = self.lastWordData
		p2 = TargetSubtitle.lastWordData
		w1 = self.lastWord
		w2 = TargetSubtitle.lastWord
		if p1 == p2: return False

		p1Accents = list((idx, val, int(val[-1])) for (idx, val) in enumerate(p1) if val[-1].isdigit())
		p2Accents = list((idx, val, int(val[-1])) for (idx, val) in enumerate(p2) if val[-1].isdigit())
		
		# cannot rhyme without syllables
		if (len(p1Accents) == 0 or len(p2Accents) == 0):
			return False

		p1AccentOrderOnly = map(lambda (idx, val, order): order, p1Accents)
		p1MaxAccent = max(p1AccentOrderOnly)
		p1AccentIndex = p1AccentOrderOnly.index(p1MaxAccent)

		p2AccentOrderOnly = map(lambda (idx, val, order): order, p2Accents)
		p2MaxAccent = max(p2AccentOrderOnly)
		p2AccentIndex = p2AccentOrderOnly.index(p2MaxAccent)

		if p1Accents[p1AccentIndex:] != p2Accents[p2AccentIndex:]:
			return False
		
		if p1[-2:] == p2[-2:]:
			#print (w1, p1Accents, w2, p2Accents)
			return True
		return False

	def getRhymingSubtitles(self, possibleSubtitles):
		rhymingSubtitles = []
		for CurrentSubtitle in possibleSubtitles:
			# Can't rhyme with yourself lol
			if CurrentSubtitle == self:
				continue
			if self.isRhyme(CurrentSubtitle):
				rhymingSubtitles.append(CurrentSubtitle)
		return rhymingSubtitles				


	

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
		print ("Parsing srt file: " + filename)
		try:
			subs = pysrt.open('subs/'+filename)
		except:
			print "Could not parse "+ filename
			continue
		for i in xrange(len(subs)):
			sub = subs[i]
			if i != len(subs)-1:
				# some subbers are crazy impatient! subs drop out prematurely
				# given a threshold for about 1.5 seconds, we will extend the sub up to
				# 750ms based on the start tiem of the next subtitle
				nextSub = subs[i+1]
				timeToNextSub = nextSub.start - sub.end
				secondsToNextSub = timeToNextSub.seconds + timeToNextSub.milliseconds/1000.0
				if secondsToNextSub <= 2:
					sub.end.seconds += secondsToNextSub/2.0
				else:
					sub.end.seconds += 1


			if (len(sub.text.split()) == 0): continue
			CurrentSubtitle = Subtitle(sub, filename)
			subtitles.append(CurrentSubtitle)

def getFilename(filenameBase):
	path = "movies/" + filenameBase + ".*"
	matches = glob.glob(path)
	if (len(matches) == 1):
		return matches[0]
	else:
		return ""

def appendSubtitle(subs, Subtitle):
	newSub = pysrt.srtitem.SubRipItem()
	newSub.start = pysrt.srttime.SubRipTime()
	newSub.end = pysrt.srttime.SubRipTime()
	if (len(subs) == 0):
		newSub.start.milliseconds = 0
	else:
		newSub.start = subs[-1].end
	newSub.end = Subtitle.end - Subtitle.start + newSub.start
	newSub.text = Subtitle.text
	newSub.index = len(subs)+1

	subs.append(newSub)

def writeClips(selectedSubtitles, outputBase):
	clips = []
	count = 0
	superclips = 0
	volumeFn = lambda array: np.sqrt(((1.0*array)**2).mean())
	desiredVolume = 0.03
	# create subtitle file to go along with it
	newSubs = pysrt.srtfile.SubRipFile()
	for CurrentSubtitle in selectedSubtitles:
		print CurrentSubtitle
		appendSubtitle(newSubs, CurrentSubtitle)
		movieFilename = getFilename(CurrentSubtitle.filename)
		clip = mpy.VideoFileClip(movieFilename).subclip(CurrentSubtitle.timeStart,CurrentSubtitle.timeEnd)
		volume = volumeFn(clip.audio.to_soundarray())
		clip.audio = clip.audio.fx(mpy.afx.volumex, desiredVolume/volume)
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
	
	# calculate the lowest resolution height
	minHeight = min(map(lambda clip: clip.h, clips))
	for (i, clip) in enumerate(clips):
		clips[i] = mpyfx.resize(clip, width=clip.w * minHeight / clip.h , height=minHeight)

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
	print "Writing srt file"
	newSubs.save(outputBase + ".srt")

def main():
	if os.path.isfile("rhyme.pickle"):
		with open('rhyme.pickle','rb') as f:
			rhymes = pickle.load(f)
	else:
		allSubtitles = []
		parseSubs(allSubtitles)
		numSyllableSegmentedSubtitleList = []
		for i in xrange(8,13):
			Subtitles = filter(lambda Subtitle: Subtitle.numSyllable == i, allSubtitles)
			numSyllableSegmentedSubtitleList.append(Subtitles)
			print ("Found " + str(len(Subtitles)) + " subtitles with " + str(i) + " syllables")
		rhymes = []
		# keep looking for a subtitle with a rhyme
		for sameNumSyllableSubtitles in numSyllableSegmentedSubtitleList:
			for CurrentSubtitle in sameNumSyllableSubtitles:
				rhymingSubtitles = CurrentSubtitle.getRhymingSubtitles(sameNumSyllableSubtitles)
				if len(rhymingSubtitles) > 0:
					rhymes.append((CurrentSubtitle, rhymingSubtitles))
		print "Found " + str(len(rhymes)) + " rhyming subtitles"
		with open('rhyme.pickle', 'wb') as f:
			pickle.dump(rhymes, f, pickle.HIGHEST_PROTOCOL)

	# in order is boring
	random.shuffle(rhymes)
	selectedSubtitles = []
	for (CurrentSubtitle, rhymingSubtitles) in rhymes:
		flag = False
		for i in xrange(10):
			selected = random.choice(rhymingSubtitles)
			if selected not in selectedSubtitles:
				flag = True
				break;
		if (flag):
			selectedSubtitles.append(CurrentSubtitle)
			selectedSubtitles.append(selected)
	
	writeClips(selectedSubtitles[0:10], "final")




if __name__ == "__main__":
	main()	
