#!/usr/bin/env python

__valid__ = ['ja','en']
__lang__ = "ja"

__words__ = {
	'ja': {
		
	},
	'en': {
		
	}
}

def lang(lng = False):
	global __lang__, __valid__
	
	if(not lng):
		return __valid__
	
	if(lng not in __valid):
		raise NotImplementedError('Unsupported language. Falling back to default (%s).'%__lang__)
		return False
	
	if(lng in __valid__):
		__lang__ = lng
		return True

def _(x):
	return __words__[__lang__][x]