from itertools import combinations
from collections import defaultdict
from monopoly import BuyAll, Board, GaHousePlayer
from random import randint

def calculate(bidding_list):
    score = 0
    for _ in range(2500):
        b = Board([GaHousePlayer(bidding_list), BuyAll()])
        if b.start_game(250):
            if b.players[1].is_bankrupt:
                score += 1
        else:
            score += 0.5

    return score

evaluated = {}
def key_chromosome(chromosome):
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

    # can only buy the railroads and utilities
    for i in [5, 15, 25, 35, 12, 28]:
        chromosome[i] = min(1, chromosome[i])

    # TODO: add house constraints
    return ",".join(map(str, chromosome))

def eval_func(chromosome):
    if chromosome not in evaluated:
        evaluated[chromosome] = calculate(map(int, chromosome.split(",")))
        print chromosome, evaluated[chromosome]

    return evaluated[chromosome]

def generate_random():
    return key_chromosome([randint(0, 6) for _ in xrange(40)])

def swap_agent(chromosome, max_mutations):
    chromosome = map(int, chromosome.split(","))
    num_mutations = randint(1, max_mutations)

    for mutation in range(num_mutations):
        swap_index1 = randint(0, len(chromosome) - 1)
        swap_index2 = swap_index1

        while swap_index1 == swap_index2:
            swap_index2 = randint(0, len(chromosome) - 1)

        chromosome[swap_index1], chromosome[swap_index2] = chromosome[swap_index2], chromosome[swap_index1]
    return key_chromosome(chromosome)

def mutate_agent(chromosome, max_mutations):
    chromosome = map(int, chromosome.split(","))
    num_mutations = randint(1, max_mutations)

    for mutation in range(num_mutations):
        mutate_index = randint(0, len(chromosome) - 1)
        chromosome[mutate_index] = randint(0, 6)

    return key_chromosome(chromosome)

population_size = 100
nr_populations = 100

population = set(generate_random() for _ in xrange(population_size))
population.add(key_chromosome(map(int, '0,6,0,5,0,2,4,0,4,4,0,6,0,5,5,2,4,0,5,3,0,0,0,0,0,2,0,0,0,0,0,0,0,0,0,4,0,5,0,3'.split(","))))
population.add(key_chromosome(map(int, '0,6,0,6,0,4,4,0,4,4,0,3,0,5,5,3,4,0,5,6,0,0,0,0,0,2,0,0,0,0,0,0,0,0,0,4,0,5,0,2'.split(","))))
for generation in range(nr_populations):
    generation_scores = []
    for chromosome in population:
        generation_scores.append((eval_func(chromosome), chromosome))
    generation_scores.sort(reverse=True)

    print generation, generation_scores[:10]

    population = set()
    for score, chormosome in generation_scores[:10]:
        # Create 1 exact copy
        population.add(chormosome)

        # Create 9 offsprings with point mutations
        for offspring in range(3):
            population.add(swap_agent(chormosome, 3))

        for offspring in range(3):
            population.add(mutate_agent(chormosome, 3))

        for offspring in range(3):
            population.add(mutate_agent(chormosome, 9))
