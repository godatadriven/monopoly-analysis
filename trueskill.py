import numpy as np

size_arr = 100
d = {}

def get_player_stats(name):
    """
    Check if a player exists in the dictionary. If not, add it.
    Then returns the player belief.
    """
    if name not in d.keys():
        d[name] = np.ones(size_arr)/np.sum(np.ones(size_arr))
    return d[name]

def gen_prior(arr1, arr2):
    """
    Combines two arrays into a matrix.
    """
    return np.matrix(arr1).T * np.matrix(arr2)

def cut_matrix(mat):
    """
    Cuts the matrix according to likelihood update rule.
    Also applies normalisation
    """
    posterior = np.triu(mat)
    posterior = posterior/np.sum(posterior)
    return posterior

def gen_marginals(posterior_mat):
    """
    From a cut matrix, generate the appropriate marginals back
    """
    winner = np.squeeze(np.asarray(np.sum(posterior_mat, 0)))
    loser = np.squeeze(np.asarray(np.sum(posterior_mat, 1)))
    return winner, loser

def update(winner, loser):
    """
    Given a winner and user, update our state.
    """
    winner_arr = get_player_stats(winner)
    loser_arr = get_player_stats(loser)
    prior_mat = gen_prior(loser_arr, winner_arr)
    posterior_mat = cut_matrix(prior_mat)
    new_winner, new_loser = gen_marginals(posterior_mat)
    d[loser] = new_loser
    d[winner] = new_winner

p1 = np.array([1.,2.,3.])
p2 = np.array([3.,2.,1.])
p3 = np.array([1.,1.,1.])
mat1 = gen_prior(p1, p2)
mat2 = gen_prior(p2, p1)
mat3 = gen_prior(p3, p3)
m1, m2 = gen_marginals(mat1)
m3, m4 = gen_marginals(mat2)
np1, np2 = gen_marginals(cut_matrix(mat1))

# marginals should still be same shape
assert all(m1 == m2[::-1])
# marginals should still be same shape
assert all(m3 == m4[::-1])
# matrices should have equal values
assert np.sum(mat1) == np.sum(mat2)
# all ones should sum to 9
assert np.sum(mat3) == 9
# marginals should still be same shape
assert all(np1 == np2[::-1])
