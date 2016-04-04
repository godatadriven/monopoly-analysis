from itertools import combinations
from collections import defaultdict
from monopoly import BuyAll, Board, GaHousePlayer
from random import randint
from joblib import Parallel, delayed

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

def key_chromosome(chromosome):
    def set_max_diff(indexes):
        max_houses = min(chromosome[index] for index in indexes) + 1
        for index in indexes:
            chromosome[index] = min(chromosome[index], max_houses)

    for index in [0, 10, 20, 30, 2, 4, 7, 17, 22, 33, 36, 38]:
        chromosome[index] = 0

    # can only buy the railroads and utilities
    for i in [5, 15, 25, 35, 12, 28]:
        chromosome[i] = min(1, chromosome[i])

    set_max_diff([1, 3])
    set_max_diff([6, 8, 9])
    set_max_diff([11, 13, 14])
    set_max_diff([16, 18, 19])
    set_max_diff([21, 23, 24])
    set_max_diff([26, 27, 29])
    set_max_diff([31, 32, 34])
    set_max_diff([37, 39])

    return ",".join(map(str, chromosome))

def eval_func(chromosome):
    return calculate(map(int, chromosome.split(","))), chromosome

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

if __name__ == '__main__':
    population_size = 100
    nr_populations = 100
    
    population = set(generate_random() for _ in xrange(population_size))
    population.add(key_chromosome(map(int, '0,6,0,5,0,2,4,0,4,4,0,6,0,5,5,2,4,0,5,3,0,0,0,0,0,2,0,0,0,0,0,0,0,0,0,4,0,5,0,3'.split(","))))
    population.add(key_chromosome(map(int, '0,6,0,6,0,4,4,0,4,4,0,3,0,5,5,3,4,0,5,6,0,0,0,0,0,2,0,0,0,0,0,0,0,0,0,4,0,5,0,2'.split(","))))

    evaluated = {}

    for generation in range(nr_populations):
        to_schedule = []
        generation_scores = []
        
        for chromosome in population:
            if chromosome in evaluated:
                generation_scores.append((evaluated[chromosome], chromosome))
            else:
                to_schedule.append(chromosome)
        
        generation_scores.extend(Parallel(n_jobs=-1, verbose=100)(delayed(eval_func)(chromosome) for chromosome in to_schedule))
        generation_scores.sort(reverse=True)

        for score, chromosome in generation_scores:
            evaluated[chromosome] = score

        print "-"*20
        print generation
        print "-"*20
        print generation_scores[:10]

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
