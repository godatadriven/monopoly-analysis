from itertools import combinations, chain
from collections import defaultdict
from monopoly import BuyAll, Board, GaHousePlayer
from random import randint, choice, sample, random
from joblib import Parallel, delayed
from joblib.parallel import cpu_count


streets = [[1, 3], [6, 8, 9], [11, 13, 14], [16, 18, 19], [21, 23, 24], [26, 27, 29], [31, 32, 34], [37, 39]]

def key_chromosome(chromosome):
    def set_max_diff(indexes):
        max_houses = min(chromosome[index] for index in indexes) + 1
        for index in indexes:
            chromosome[index] = min(chromosome[index], max_houses)

    # its not possible to buy chance etc.
    for index in [0, 10, 20, 30, 2, 4, 7, 17, 22, 33, 36, 38]:
        chromosome[index] = 0

    # can only buy the railroads and utilities
    for i in [5, 15, 25, 35, 12, 28]:
        chromosome[i] = min(1, chromosome[i])

    for street in streets:
        set_max_diff(street)

    return ",".join(map(str, chromosome))

buy_all = key_chromosome([6] * 40)

def calculate(chromosome, opponent):
    score = 0
    for _ in range(1000):
        b = Board([GaHousePlayer(chromosome), GaHousePlayer(opponent)])
        if b.start_game(250):
            if b.players[1].is_bankrupt:
                score += 1

    return score, chromosome

def generate_random():
    return key_chromosome([randint(0, 6) for _ in xrange(40)])

def mutate(chromosome, max_mutations=1):
    chromosome = map(int, chromosome.split(","))
    num_mutations = randint(1, max_mutations)

    for mutation in range(num_mutations):
        street = choice(streets)
        idx = choice(street)
        chromosome[idx] = randint(0, 6)

    return key_chromosome(chromosome)

if __name__ == '__main__':
    population_size = 50
    nr_populations = 10
    remain_perc = 0.2
    mutate_perc = 0.01

    population_size = cpu_count() * ((population_size / cpu_count()) + 1)
    population = set(generate_random() for _ in xrange(population_size))
    
    evaluated = {}
    
    for generation in range(1, nr_populations + 1):
        results = Parallel(n_jobs=-1, verbose=100)(delayed(calculate)(chromosome, buy_all) for chromosome in population)
        
        for score, chromosome in results:
            evaluated[chromosome] = score
        
        winners = []
        for chromosome, score in evaluated.iteritems():
            winners.append((score, chromosome))
        winners.sort(reverse=True)

        print "-"*20
        print "Generation", generation
        print "-"*20
        print winners[:10]
        print ";".join(str(score) for score, _ in winners[:10])

        # add top X%
        candidates = set()
        for _, chromosome in winners[:int(population_size * remain_perc)]:
            candidates.add(chromosome)

        # mutate some
        for _, chromosome in winners:
            if mutate_perc > random():
                candidates.add(mutate(chromosome, 3))

        # merge candidates
        population = set()
        while len(population) < population_size:
            male, female = sample(candidates, 2)

            male_chromosome = map(int, male.split(","))
            female_chromosome = map(int, female.split(","))

            child = male_chromosome[:]
            for i, f in enumerate(female_chromosome):
                if random() > 0.5:
                    child[i] = f

            child = key_chromosome(child)
            if not child in evaluated:
                population.add(child)
