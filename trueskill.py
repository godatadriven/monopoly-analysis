import numpy as np
import pandas as pd
import json 

size_arr = 100
d = {} 

def get_player_stats(name):
    if name not in d.keys(): 
        d[name] = np.ones(size_arr)/np.sum(np.ones(size_arr))
    return d[name]

def gen_matrix(arr1, arr2):
    margin = 0
    mat = np.zeros([len(arr1), len(arr2)]) + 1./size_arr**2/10
    for i in range(len(arr1)): 
        for j in range(i - margin, len(arr2)):
            mat[j,i] = arr1[i] * arr2[j]
    mat = np.fliplr(mat)/np.sum(mat)
    return mat 

def parse_matrix(mat): 
    new_win = np.sum(mat, 0).reshape(-1)
    new_lose = np.sum(np.flipud(mat), 1).reshape(-1)
    return new_win/np.sum(new_win), new_lose/np.sum(new_lose)

def update(winner, loser):
    winner_arr = get_player_stats(winner)
    loser_arr = get_player_stats(loser)
    new_winner, new_loser = parse_matrix(gen_matrix(winner_arr, loser_arr))
    d[loser] = new_winner
    d[winner] = new_loser
