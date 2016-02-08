from pyevolve.G1DList import G1DList
from pyevolve.GSimpleGA import GSimpleGA
from itertools import combinations
from collections import defaultdict
from monopoly import BuyAll, Board, GaPlayer

def calculate(bidding_list):
    score = 0
    for _ in range(5000):
        b = Board([GaPlayer(bidding_list), BuyAll()])
        if b.start_game(250):
            if b.players[1].is_bankrupt:
                score += 1
        else:
            score += 0.5

    return score

evaluated = {}
def key_chromosome(chromosome):
    chromosome = list(chromosome)
    chromosome[0] = 0
    chromosome[10] = 0
    chromosome[20] = 0
    chromosome[30] = 0
    chromosome[2] = 0
    chromosome[4] = 0
    chromosome[7] = 0
    chromosome[17] = 0
    chromosome[22] = 0
    chromosome[33] = 0
    chromosome[36] = 0
    chromosome[38] = 0
    return ",".join(map(str, list(chromosome)))

def eval_func(chromosome):
    key = key_chromosome(chromosome)
    if key not in evaluated:
        evaluated[key] = calculate(list(chromosome))
        print key, evaluated[key]

    return evaluated[key]

genome = G1DList(40)
genome.setParams(rangemin=0, rangemax=1)
genome.evaluator.set(eval_func)

ga = GSimpleGA(genome)
# ga.setPopulationSize(10)
ga.setGenerations(50)
ga.evolve(freq_stats=10)
print ga.bestIndividual()
