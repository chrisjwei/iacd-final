import pysrt
import string, os
from pymarkovchain import MarkovChain

def markov_convert(d):
	return pykov.Chain(d);

def dict_record(d, a, b):
	key = (a,b)
	if (key in d):
		d[key] += 1
	else:
		d[key] = 1
	
def sub_format(txt):
	return txt.encode('utf-8') \
			  .translate(None, string.punctuation) \
              .replace('\n', ' ') \
              .lstrip()

def subs_parse(subs):
	parsed_string = ""
	for sub in subs:
		parsed_string = parsed_string + " " + sub_format(sub.text)
	return parsed_string

def main():
	mc = MarkovChain()
	training_str = ""	
	for filename in os.listdir("subs"):
		subs = pysrt.open('subs/'+filename)
		sub_str = subs_parse(subs)
		training_str = training_str + " " + sub_str
	mc.generateDatabase(training_str)
	mc.generateString(10)

if __name__ == "__main__":
	main()	
