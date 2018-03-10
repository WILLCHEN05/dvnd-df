# -*- coding: utf-8 -*-
from include_lib import include_dvnd, include_pydf
include_dvnd()
include_pydf()
from pyDF import Node, Oper


class DecisionNode(Node):
	def __init__(self, f=lambda x: None, inputn=1, should_run=lambda x: True, keep_going=lambda x, y: True):
		super(DecisionNode, self).__init__(f, inputn)
		self.__should_run = should_run
		self.__keep_going = keep_going

	def run(self, args, workerid, operq):
		param_args = [a.val for a in args]
		if not self.__should_run(param_args):
			self.sendops([Oper(workerid, None, None, None)], operq)
		else:
			resp = self.f(param_args)

			if not self.__keep_going(param_args, resp):
				opers = [Oper(workerid, None, None, None)]
			else:
				opers = self.create_oper(resp, workerid, operq)

			self.sendops(opers, operq)


class OptMessage(object):
	def __init__(self, solmap={}, source=0, target=[], not_improved=[]):
		self.__solmap = solmap
		self.__source = source
		self.__target = target
		self.__not_improved = not_improved
		self.counts = [0 for x in target]

	def __getitem__(self, item=0):
		return self.__solmap[item]

	def __setitem__(self, item=0, val=None):
		self.__solmap[item] = val

	def __len__(self):
		return len(self.__solmap)

	def get_best(self, maximize=False):
		return min(self.__solmap.values()) if not maximize else max(self.__solmap.values())

	@property
	def source(self):
		return self.__source

	@source.setter
	def source(self, value):
		self.__source = value

	def has_target(self, idx=0):
		return self.__target[idx]

	def has_not_improved(self, idx=0):
		return not self.__not_improved[idx]

	def no_improvement(self):
		return all(self.__not_improved)

	def unset_all_targets(self):
		self.__target = [False for x in self.__target]

	def set_target(self, idx=0, val=True):
		self.__target[idx] = val

	def set_not_improved(self, idx=0, val=True):
		self.__not_improved[idx] = val

	def __contains__(self, item=None):
		return item in self.__solmap

	def __str__(self):
		return "sol: {}, s: {}, t: {}, ni: {}".format(self.__solmap, self.__source,
			self.__target, self.__not_improved)

	def get_not_improveds(self):
		return [x for x in xrange(len(self.__not_improved)) if self.__not_improved[x]]
