from pylab import *
import sys
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.colors as mcolors
import matplotlib as mpl
import os

def create_positions(radius, color):
    V = {}
    IV = {}
    positions = []
    for i in range(-radius, radius+1):
        for j in range(-radius, radius+1):
            if abs(i) + abs(j) <= radius:
                positions.append((i, j))

    for position in positions:
        for c in range(1, color+1):
            V[(position, c)] = len(V) + 1
            IV[V[(position, c)]] = (position, c)
    return positions, V, IV

def visualize(M, text=True, title='Untitled', colors_to_use=None, fig=None):
    if fig is None:
        fig = plt.figure(dpi=300)
    ax = fig.add_subplot(aspect='equal')
    diff_values = set()
    for i in range(len(M)):
        for j in range(len(M[0])):
            if isinstance(M[i][j], list):
                for val in M[i][j]:
                    diff_values.add(val)
    radius = len(M)//2
    ax.set_xlim([-radius-1, radius+1])
    ax.set_ylim([-radius-1, radius+1])
    #    ax.set_title(title)
    ax.axis('off')
    for i in range(-radius, radius+1):
        for j in range(-radius, radius+1):
            if abs(i) + abs(j) <= radius:
                rect = patches.Rectangle(
                    (i-0.5, j-0.5), 1, 1, edgecolor='black', linewidth=0, facecolor='gray')
                ax.add_patch(rect)

    rect_large = patches.Rectangle(
            (-radius-1.5, 0), 1, 1)
    ax.add_patch(rect_large)
    for i in range(len(M)):
        for j in range(len(M[0])):
            if isinstance(M[i][j], list):
                n = len(M[i][j])
                for k in range(n):
                    rect = patches.Rectangle((i+0.5-1, j+0.5-1+(1/n)*k), 1, 1/n, edgecolor='black',
                                             linewidth=1, facecolor=colors_to_use[M[i][j][k]-1])
                    ax.add_patch(rect)
                    if text:
                        ax.text(i, j-0.5+(1/n)*k+1/(2*n),
                                M[i][j][k], ha='center', va='center', color='black', fontsize=6)
    
    plt.gca().set_aspect('equal')
    return fig
        
def mat_from_coloring(coloring, radius):
    mat = [[-10 for _ in range(2*radius+1)] for _ in range(2*radius+1)]
    for i in range(-radius, radius+1):
        for j in range(-radius, radius+1):
            if abs(i) + abs(j) <= radius:
                mat[i+radius][j+radius] = 0
    for key, val in coloring.items():
        i, j = key
        mat[i+radius][j+radius] = val
    return mat

def print_mat(mat):
    for row in mat:
        print(", ".join(list(map(str, row))))

def create_colorings(clauses, radius, colors):
    positions, V, IV = create_positions(radius, colors)
    max_natural_var = len(V)

    def natural(v):
        return abs(v) <= max_natural_var

    coloring = {}
    coloring_op = {}
    map_unnatural_variables = {}
    G = nx.DiGraph()
    for clause in clauses:
        clause = list(sorted(clause, key=abs))
        if len(clause) < 2 or natural(clause[1]): # fully natural clause
            continue
        if not natural(clause[0]): # fully unnatural clause
            G.add_edge(-1*clause[0], clause[1])
            continue

        position, color = IV[abs(clause[0])]
        if abs(clause[1]) not in map_unnatural_variables:
                map_unnatural_variables[abs(clause[1])] = len(map_unnatural_variables) + 1
        
        # permission  natural -> permission from unnatural.  (not natural or unnatural)
        if clause[1] > 0 and clause[0] < 0: # permission check
            if position not in coloring:
                coloring[position] = []
            coloring[position].append(map_unnatural_variables[abs(clause[1])])

        # prohibition natural -> forbid unnatural (not natural or not unnatural)
        if clause[1] < 0 and clause[0] < 0: # prohibition check
            if position not in coloring_op:
                coloring_op[position] = []
            coloring_op[position].append(map_unnatural_variables[abs(clause[1])])
    return coloring, coloring_op


def get_fig(clauses, radius, colors):
    coloring, coloring_op = create_colorings(clauses, radius, colors)
    M = mat_from_coloring(coloring, radius)
    diff_values = set()
    for i in range(len(M)):
        for j in range(len(M[0])):
            if isinstance(M[i][j], list):
                for val in M[i][j]:
                    diff_values.add(val)

    colors_to_use = []
    # matplotlib color palette name, n colors
    cmap = cm.get_cmap('tab20b')
    for i in range(cmap.N):
        colors_to_use.append(cmap(i)[:3])

    return visualize(M, text=radius<10, title="Permission Clauses", colors_to_use=colors_to_use)
