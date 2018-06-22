#!/usr/bin/python
# -*- coding: utf-8 -*-
import random
# from mpi4py import MPI
from optobj import DecisionNode, OptMessage
from pyDF import DFGraph, Feeder, Scheduler


class DataFlowVND(object):
	def __init__(self, maximize=False, mpi_enabled=False, is_rvnd=False):
		"""
		:param maximize: Indica se é um problema de maximização ou minimização.
		:param mpi_enabled: Indica se usa MPI.
		:param is_rvnd: Indica se o método é VND ou RVND
		"""
		self.__maximize = maximize
		self.__mpi_enabled = mpi_enabled
		self.__is_rvnd = is_rvnd

	@staticmethod
	def __neighborhood(func=lambda args: None, args=[], maximize=False):
		resp = func(args[0][0])
		return [max(resp, args[0][0]) if maximize else min(resp, args[0][0]),
			resp < args[0][0] if not maximize else args[0][0] < resp, args[0][2] + 1]

	def run(self, number_of_workers=1, initial_solution=None, oper_funtions=[], result_callback=lambda x: True):
		"""
		:param number_of_workers: Número de workers Sucuri.
		:param initial_solution: Solução inicial.
		:param oper_funtions: Funções dos operadores, vizinhanças.
		:param result_callback: Método chamado quando o processo termina.
		"""
		graph = DFGraph()

		ini_node = Feeder([initial_solution, True, 0])
		graph.add(ini_node)

		fim_node = DecisionNode(lambda y: result_callback([y[0][0]], [y[0][2]]), 1, lambda a: not a[0][1])
		graph.add(fim_node)

		if self.__is_rvnd:
			oper_funtions = [x for x in oper_funtions]
			random.shuffle(oper_funtions)

		number_of_opers = len(oper_funtions)
		oper_node = [DecisionNode(lambda arg, idx=x: DataFlowVND.__neighborhood(oper_funtions[idx], arg, self.__maximize), 1,
			lambda a, y=x: a[0][1] if y == 0 else (not a[0][1])) for x in xrange(number_of_opers)]

		for oper_it in oper_node:
			graph.add(oper_it)
			oper_it.add_edge(oper_node[0], 0)

		for x in xrange(number_of_opers - 1):
			oper_node[x].add_edge(oper_node[x + 1], 0)

		ini_node.add_edge(oper_node[0], 0)
		oper_node[number_of_opers - 1].add_edge(fim_node, 0)

		Scheduler(graph, number_of_workers, mpi_enabled=self.__mpi_enabled).start()


class DataFlowDVND(object):
	def __init__(self, maximize=False, mpi_enabled=False, process_sol_before_oper=lambda arg: arg):
		"""
		:param maximize: Indica se é um problema de maximização ou minimização.
		:param mpi_enabled: Indica se usa MPI.
		"""
		self.maximize = maximize
		self.__mpi_enabled = mpi_enabled
		self.__process_sol_before_oper = process_sol_before_oper

	def __neighborhood(self, func=lambda arg: None, args=[], inimov=0):
		atual = args[0]
		atual.source = inimov
		# Alterar soluão antes de enviar
		sol_param = atual[inimov] if self.__process_sol_before_oper is None \
			else self.__process_sol_before_oper(atual[inimov])
		atual[inimov] = max(atual[inimov], func(sol_param)) if self.maximize \
			else min(atual[inimov], func(sol_param))
		atual.counts[inimov] += 1
		return atual

	def best_solution(self, atual=None, anterior=None, melhor=None):
		"""
		Decide qual é a melhor solução.
		:param atual: Solution returned by the operation node.
		:param anterior: Actual solution on the manager node.
		:param melhor: Best solution on manager node.
		:return: Melhor solução e flag indicando se a melhor é a atual.
		"""
		if (not self.maximize and atual < anterior) or (self.maximize and anterior < atual):
			return atual, True
		return anterior, False

	def manager(self, args=[]):
		atual = args[0]
		melhor = args[1]

		# melhor_ini = melhor.get_best()
		melhor.unset_all_targets()
		# atualValue = atual[atual.source]

		atual_melhor = self.best_solution(atual[atual.source], melhor[atual.source], melhor.get_best(self.maximize))
		melhor[atual.source] = atual_melhor[0]

		# if (not self.__maximize and atual[atual.source] < melhor[atual.source]) \
		# 		or (self.__maximize and melhor[atual.source] < atual[atual.source]):
		# 	melhor[atual.source] = atual[atual.source]
		# 	melhor.set_target(atual.source)
		# else:
		# 	melhor.set_not_improved(atual.source)
		if atual_melhor[1]:
			melhor.set_target(atual.source)
		else:
			melhor.set_not_improved(atual.source)

		best_sol = melhor[atual.source] = melhor.get_best(self.maximize)
		# Caso não tenha melhorado mas tenha aparecido uma solução melhor
		for x in melhor.get_not_improveds():
			if (not self.maximize and best_sol < melhor[x]) or (self.maximize and best_sol > melhor[x]):
				melhor[x] = best_sol
				melhor.set_target(x)
				# Se vai chamar novamente remove o sinal
				melhor.set_not_improved(x, False)

		for i in xrange(len(melhor.counts)):
			melhor.counts[i] = max(atual.counts[i], melhor.counts[i])

		return melhor

	def run(self, number_of_workers=1, initial_solution=None, oper_funtions=[], result_callback=lambda x: True):
		"""
		:param number_of_workers: Número de workers Sucuri.
		:param initial_solution: Solução inicial.
		:param oper_funtions: Funções dos operadores, vizinhanças.
		:param result_callback: Método chamado quando o processo termina.
		"""
		graph = DFGraph()

		# Nó final Cria n
		number_of_opers = len(oper_funtions)
		fimNode = DecisionNode(lambda y: result_callback([y[0][i] for i in xrange(number_of_opers)], y[0].counts), 1,
			lambda x: x[0].no_improvement())
		graph.add(fimNode)

		# Nó de gerenciamento ligado nele mesmo e no nó final
		man_node = DecisionNode(self.manager, 2)
		graph.add(man_node)
		man_node.add_edge(man_node, 1)
		man_node.add_edge(fimNode, 0)

		# Nó que inicializa o nó gerenciador
		ini_man_node = Feeder(OptMessage({x: initial_solution for x in xrange(number_of_opers)}, number_of_opers,
			[False for y in xrange(number_of_opers)], [False for i in xrange(number_of_opers)]))
		graph.add(ini_man_node)
		ini_man_node.add_edge(man_node, 1)

		# Nós de operações
		oper_should_run = [lambda x, a=y: x[0].has_target(a) for y in xrange(number_of_opers)]
		oper_keep_going = [lambda a, b: True for y in xrange(number_of_opers)]
		oper_node = [DecisionNode(lambda arg, fnc=oper_funtions[i], it=i: self.__neighborhood(fnc, arg, it),
			1, oper_should_run[i], oper_keep_going[i]) for i in xrange(number_of_opers)]
		for x in oper_node:
			graph.add(x)
			man_node.add_edge(x, 0)
			x.add_edge(man_node, 0)

		# if self.__mpi_enabled:
		# 	comm = MPI.COMM_WORLD
		# 	nprocs = comm.Get_size()
		# 	print "MPI {}/{}".format(comm.Get_rank(), nprocs)
		# 	for i in xrange(len(oper_node)):
		# 		# oper_node[i].pin([i % nprocs])

		# Nós que inicializam nós de operação
		ini_node = [Feeder(OptMessage({x: initial_solution}, x, [x == y for y in xrange(number_of_opers)],
			[False for i in xrange(number_of_opers)])) for x in xrange(number_of_opers)]
		for i in xrange(number_of_opers):
			graph.add(ini_node[i])
			ini_node[i].add_edge(oper_node[i], 0)

		Scheduler(graph, number_of_workers, mpi_enabled=self.__mpi_enabled).start()


class DataFlowGDVND(DataFlowDVND):
	def __init__(self, maximize=False, mpi_enabled=False, process_sol_before_oper=lambda arg: None,
			merge_solutions=lambda sols=[]: sols, combine_sol=lambda sol1, sol2: sol1):
		"""
		:param maximize: Indica se é um problema de maximização ou minimização.
		:param mpi_enabled: Indica se usa MPI.
		:param merge_solutions: The merge solution function.
		:param process_sol_before_oper: Process the solution before it is sent to the operation node.
		"""
		super(DataFlowGDVND, self).__init__(maximize, mpi_enabled, process_sol_before_oper)
		self.__merge_solutions = merge_solutions
		self.__combine_sol = combine_sol

	def best_solution(self, atual=None, anterior=None, melhor=None):
		# TODO Falta fazer o merge dos movimentos independentes
		# get_no_conflict(cids, ciis, cjjs, ccosts):
		# TODO Comparar a melhor solução atual com a nova e o não conflito da melhor com a atual
		if len(atual.movtuple) > 0 and len(melhor.movtuple) > 0:
			combined_sol = self.__combine_sol(atual, melhor)
			if self.maximize:
				resp_sol = max(atual, anterior, melhor, combined_sol)
				return resp_sol, resp_sol == atual
			else:
				resp_sol = min(atual, anterior, melhor, combined_sol)
				return resp_sol, resp_sol == atual
		return super(DataFlowGDVND, self).best_solution(atual, anterior, melhor)

	def manager(self, args=[]):
		resp = super(DataFlowGDVND, self).manager(args)
		# TODO fazer o merge de duas soluções e pegar a melhor
		resp_sol = self.__merge_solutions([resp[x] for x in xrange(len(resp))])
		for x in xrange(len(resp)):
			resp[x] = resp_sol[x]
		return resp
