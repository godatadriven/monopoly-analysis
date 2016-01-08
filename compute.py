from pyevolve.G1DList import G1DList
from pyevolve.GSimpleGA import GSimpleGA
from itertools import combinations
from collections import defaultdict
from monopoly import BuyAll, Board, GaPlayer

def calculate(bidding_list):
    score = 0
    for _ in range(1000):
        b = Board([GaPlayer(bidding_list), BuyAll()])
        if b.start_game(250):
            if b.players[1].is_bankrupt:
                score += 1
        else:
            score += 0.5

    return score

evaluated = {}
def eval_func(chromosome):
    key = ",".join(map(str, list(chromosome)))
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
