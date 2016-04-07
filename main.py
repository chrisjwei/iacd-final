import pysrt
import string, os

from random import random
from bisect import bisect

def weighted_choice(choices):
    values, weights = zip(*choices.items())
    total = 0
    cum_weights = []
    for w in weights:
        total += w
        cum_weights.append(total)
    x = random() * total
    i = bisect(cum_weights, x)
    return values[i]

def markov_walk(d, state, steps):
	for i in xrange(steps):
		print state
		if (state in d):
			state_transitions = d[state]
			next_state = weighted_choice(state_transitions)
			state = next_state
		else:
			return
		
		

def dict_record(d, key, val):
	if (key == ""): return
	if (key in d):
		chain = d[key]
		if (val in chain):
			chain[val] += 1
		else:
			chain[val] = 1
	else:
		chain = {val: 1}
	d[key] = chain
	
def sub_format(txt):
	return txt.encode('utf-8') \
			  .translate(None, string.punctuation) \
              .replace('\n', ' ') \
              .lstrip()

def subs_parse(subs, d):
	if len(subs) == 0:
		return
	prev_word = ""
	for sub in subs:
		formatted = sub_format(sub.text)
		words = formatted.split()
		if len(words) == 0: continue
		for word in words:
			dict_record(d, prev_word, word)
			prev_word = word

def main():
	d = {}
	for filename in os.listdir("subs"):
		subs = pysrt.open('subs/'+filename)
		subs_parse(subs, d)
	markov_walk(d, "Anakin", 15)

if __name__ == "__main__":
	main()	
