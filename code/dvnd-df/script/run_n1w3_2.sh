#!/bin/bash
for filei in 1 6
do
	for i in {0..99}
	do
	   echo "np1w3in"$filei"_"$i
	   time mpirun -np 1 --hostfile host_2 python main.py -mpi -n 3 -in $filei > results/"np1w3in"$filei"_"$i.out 2> results/"np1w3in"$filei"_"$i.log
	done
done

