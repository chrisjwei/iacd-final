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

def markov_walk(d, state, steps, order):
	for i in xrange(steps):
		if (state in d):
			print state
			state_transitions = d[state]
			next_state = weighted_choice(state_transitions)
			words = state.split()
			words.pop(0)
			words.append(next_state)
			state = " ".join(words)
		else:
			return
		
		

def dict_record(d, words, val):
	for word in words:
		if (word == ""): return
	# convert array of words into string
	sentence = " ".join(words)
	if (sentence in d):
		chain = d[sentence]
		if (val in chain):
			chain[val] += 1
		else:
			chain[val] = 1
	else:
		chain = {val: 1}
	d[sentence] = chain
	
def sub_format(txt):
	return txt.encode('utf-8') \
			  .translate(None, string.punctuation) \
              .replace('\n', ' ') \
              .lstrip()

def subs_parse(subs, d, order):
	if len(subs) == 0:
		return
	prev_words = [""]*order
	for sub in subs:
		formatted = sub_format(sub.text)
		words = formatted.split()
		if len(words) == 0: continue
		for word in words:
			dict_record(d, prev_words, word)
			prev_words.pop(0)
			prev_words.append(word)

def main():
	d = {}
	order = 3
	for filename in os.listdir("subs"):
		subs = pysrt.open('subs/'+filename)
		subs_parse(subs, d, order)
	markov_walk(d, "You have only", 100, order)

if __name__ == "__main__":
	main()	
