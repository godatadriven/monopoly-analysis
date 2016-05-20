from itertools import combinations, chain
from collections import defaultdict
from monopoly import BuyAll, Board, GaHousePlayer
from random import randint, choice, sample, random
from joblib import Parallel, delayed
from trueskill import update, suggest_opponent, get_player_stats, get_sorted_players, is_player_known
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

def calculate(chromosome, opponents):
    results = []

    for opponent in opponents:
        if chromosome != opponent:
            scores = [0, 0]
            while True:
                b = Board([GaHousePlayer(chromosome), GaHousePlayer(opponent)])
                if b.start_game(250):
                    if b.players[0].is_bankrupt:
                        scores[1] += 1
                        if scores[1] > 4:
                            break
                    else:
                        scores[0] += 1
                        if scores[0] > 4:
                            break

            if scores[0] > scores[1]:
                results.append((chromosome, opponent))
            else:
                results.append((opponent, chromosome))

    return results

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
    nr_populations = 25
    remain_perc = 0.2
    mutate_perc = 0.01
    
    population_size = cpu_count() * ((population_size / cpu_count()) + 1)

    population = set(generate_random() for _ in xrange(population_size))
    population.add(buy_all)
    # population.add(key_chromosome(map(int, '0,6,0,5,0,2,4,0,4,4,0,6,0,5,5,2,4,0,5,3,0,0,0,0,0,2,0,0,0,0,0,0,0,0,0,4,0,5,0,3'.split(","))))
    # population.add(key_chromosome(map(int, '0,6,0,6,0,4,4,0,4,4,0,3,0,5,5,3,4,0,5,6,0,0,0,0,0,2,0,0,0,0,0,0,0,0,0,4,0,5,0,2'.split(","))))

    for generation in range(1, nr_populations + 1):
        to_schedule = []
        
        for chromosome in population:
            get_player_stats(chromosome)
        
        for chromosome in population:
            opponents = [buy_all, ]
            opponents.extend(suggest_opponent(chromosome) for _ in range(100))
            to_schedule.append((chromosome, opponents))

#         results = []
#         for chromosome, opponents in to_schedule:
#             results.append(calculate(chromosome, opponents))
        results = Parallel(n_jobs=-1, verbose=100)(delayed(calculate)(chromosome, opponents) for chromosome, opponents in to_schedule)

        for winner, loser in chain(*results):
            update(winner, loser)

        winners = get_sorted_players()

        print "-"*20
        print "Generation", generation
        print "-"*20
        print winners[:10]

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
            if not is_player_known(child):
                population.add(child)
