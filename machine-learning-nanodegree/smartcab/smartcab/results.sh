#!/bin/bash

# usage: $0 <pid to check>

#heading
echo "alpha,gamma,reached destination,mistakes,rewards"

for alpha in 1 0.1 0.01 0.001
do
    for gamma in 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9
    do
        fileName=rl$1_$alpha\_$gamma.out
        positives=`cat $fileName | awk '{if ($2 > $3) print 1;}' | wc -l`
        mistakes=`cat $fileName | awk 'BEGIN{x=0}{x+=$5}END{print x}'`
        rewards=`cat $fileName | awk 'BEGIN{x=0}{x+=$1}END{print x}'`
        echo $alpha,$gamma,$positives,$mistakes,$rewards
    done
done
