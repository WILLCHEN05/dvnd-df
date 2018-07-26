# -*- coding: utf-8 -*-
class CommandParams(object):
	def __init__(self, solution_index=0, solution_instance_index=-2, goal="min",
			problem_name="ml", number_of_moves=10, device_count=1, solver="gdvnd", workers=1):
		from util import getparam, hasparam
		self.solution_index = int(getparam("in", None, solution_index))
		self.solution_instance_index = int(getparam("sii", "solution_instance_index", solution_instance_index))
		# solution_in_index = None if "-sn" not in sys.argv else int(sys.argv[sys.argv.index("-sn") + 1])
		self.multi_gpu = hasparam("mg", "multi_gpu")
		self.goal = getparam(None, "goal", goal).lower() == "max"
		self.problem_name = getparam("p", None, problem_name).lower()
		self.number_of_moves = int(getparam(None, "number_of_moves", number_of_moves))
		self.device_count = int(getparam("dc", "device_count", device_count))
		self.solver = getparam("s", "solver", solver).lower()
		self.mpi_enabled = hasparam("mpi")
		self.workers = int(getparam("n", None, workers))

	def __str__(self):
		return "{{solution_index:{}, solution_instance_index:{}, multi_gpu:{}, goal:{}, problem_name:{}, " \
				"number_of_moves:{}, device_count:{}, solver:{}, mpi_enabled:{}, workers:{}}}".\
			format(self.solution_index, self.solution_instance_index, self.multi_gpu, self.goal, self.problem_name,
				self.number_of_moves, self.device_count, self.solver, self.mpi_enabled, self.workers)