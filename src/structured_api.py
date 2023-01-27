import sys
import itertools
from pysat.formula import CNF
from pysat.card import *

class Structure:
    def __init__(self, radius, colors, symmetry_breaking_levels=1):
        self.radius = radius
        self.colors = colors
        self.positions = []
        self.symmetry_breaking_levels = symmetry_breaking_levels
        for i in range(-self.radius, self.radius+1):
            for j in range(-self.radius, self.radius+1):
                if abs(i) + abs(j) <= self.radius:
                    self.positions.append((i, j))

        self.V = {}
        for pos in self.positions:
            for color in range(1, self.colors+1):
               self.V[(pos, color)] = len(self.V) + 1

    def long_clauses(self):
        ans = []
        for pos in self.positions:
            ans.append([self.V[(pos, color)] for color in range(1, self.colors+1)])
        return ans

    def foreign_clauses(self):
        M = {
            1: 2,
            2: 5,
            3: 6,
            4: 8,
            6: 10,
        }
        ans = []
        for r in M.keys():
            for pos in self.positions:
                if dist(pos, (0, 0)) + r > self.radius: continue
                clause = []
                for pos2 in self.positions:
                    if dist(pos, pos2) <= r:
                        for col in range(M[r], self.colors+1):
                            clause.append(self.V[(pos2, col)])
                ans.append(clause)
        return ans
        
    def alod_clauses(self, color_limit=1):
        ans = []
        for color in range(1, color_limit+1):
            for pos in self.positions:
                clause = [self.V[(pos, color)]] 
                for pos2 in self.positions:
                    if dist(pos, pos2) <= color and pos2 != pos:
                        clause.append(self.V[(pos2, color)])
                ans.append(clause)
        return ans

    def minimization_clauses(self):
        ans = []
        for pos in self.positions:
            if pos == (0, 0): continue # center doesn't count.
            for color in range(2, self.colors+1):
                clause = [-1*self.V[(pos, color)]]
                for smaller_color in range(1, color):
                    for pos2 in self.positions:
                        if pos2 != pos and dist(pos, pos2) <= smaller_color:
                            clause.append(self.V[(pos2, smaller_color)]) 
                ans.append(clause)
        return ans

    def symmetry_breaking(self):
        clauses = []
        for col in range(self.colors, self.colors-self.symmetry_breaking_levels, -1):
            clause = []
            for h_col in range(col+1, self.colors+1):
                for pos in self.positions:
                    if dist(pos, (0,0)) <= h_col//2 and main_octant(*pos):
                        clause.append(self.V[(pos, h_col)])
            for pos in self.positions:
                if dist(pos, (0, 0)) <= col//2 and not main_octant(*pos):
                    clauses.append(clause + [-1*self.V[(pos, col)]])
        return clauses

    def symmetry_verification(self, filename=None):
        content = ''
        for col in range(self.colors, self.colors-self.symmetry_breaking_levels, -1):
            horz = []
            verz = []
            diagz = []
            for pos in self.positions:
                if dist(pos, (0, 0)) > col//2: continue
                if pos[0] < 0:
                    horz.append(pos)
                elif pos[1] < 0:
                    verz.append(pos)
                elif pos != (0, 0) and not main_octant(*pos):
                    diagz.append(pos)
            for pos in horz:
                content += self.verification_line((pos, col), HORIZONTAL) + '\n'
            for pos in verz:
                content += self.verification_line((pos, col), VERTICAL) + '\n'
            for pos in diagz:
                content += self.verification_line((pos, col), DIAGONAL) + '\n'
        if filename is None:
            filename = f'sym-ver-{self.radius}-{self.colors}'
        with open(filename, 'w') as file:
            file.write(content)

    def verification_line(self, element, trans):
        pos, color = element
        higher_lits = []
        higher_lits_perm = []
        for col in range(color+1, self.colors+1):
            for p in self.positions:
                if (dist((0, 0), p) <= col//2 and main_octant(*p)):
                    higher_lits.append(self.V[(p, col)])
                    higher_lits_perm.append(self.V[(tuple(trans.apply(p)), col)])
        negated_higher_lits = [self.V[(tuple(trans.apply(pos)), color)]] + list(map(lambda x: -x, higher_lits_perm))
        tokens = [-self.V[element]] + higher_lits
        tokens += [-self.V[element]] + negated_higher_lits + [-self.V[element]]
        for color2 in range(1, self.colors+1):
            for pos2 in self.positions:
                symmetrical = tuple(trans.apply(pos2))
                if symmetrical == pos2: continue
                if self.V[element] in [self.V[(pos2, color2)], self.V[(symmetrical, color2)]]:
                    continue
                elif self.V[(symmetrical, color2)] in higher_lits:
                    continue
                else:
                    tokens.append(self.V[(pos2, color2)])
                    tokens.append(self.V[(symmetrical, color2)])
        tokens.append(0)
        return ' '.join(list(map(str, tokens)))

    def center_force(self, val_to_force=None):
        if val_to_force is None or val_to_force == 0:
            val_to_force = min(self.radius, self.colors)
        return [self.V[((0,0), val_to_force)]]

    def conflict_clauses(self, new_vars_per_color, singlecolor=None):
        ans = []
        prf = []
        color_range = [singlecolor] if singlecolor is not None else list(range(1, self.colors+1))
        for color in color_range:
            clses, proof = self.structured(color, new_vars_per_color[color])
            ans.extend(clses)
            prf.extend(proof)
        return ans, prf

    def bounded_border_ones(self, bound):
        clauses = []
        border = list(filter(lambda p: dist(p, (0,0))==self.radius, self.positions))
        for cmb in itertools.combinations(border, bound+1):
            clauses.append([-1*self.V[(p, 1)] for p in list(cmb)])
        return clauses

    def chessboard(self):
        clauses = []
        for pos in self.positions:
            i, j = pos
            if (i+j)%2:
                clauses.append([self.V[(pos, 1)]])
        return clauses


    def structured(self, color, list_new_variables):
        clauses = []
        proof = []
        M = {} # Membership mapping; for each position, map it to new variables it belongs to
        D = {} # Descendant mapping; for each new variable, map it to positions it controls
        
        conflicts_solved = {}
        # assume list new variables is a list L of lists.
        # Each list l in L is a list of positions, corresponding to a new variable.
        long_clauses = []
        for list_variable in list_new_variables:
            if ('n', color, tuple(list_variable)) not in self.V:
                self.V[('n', color, tuple(list_variable))] = len(self.V) + 1
            this_nv = self.V[('n', color, tuple(list_variable))]
            D[this_nv] = list_variable
            for position in list_variable:
                if position not in M:
                    M[position] = [this_nv]
                else:
                    M[position].append(this_nv)
                clauses.append([this_nv, -1*self.V[(position, color)]]) # permission clauses
                proof.append(clauses[-1])
            proof.append([-this_nv] + [self.V[(position, color)] for position in list_variable])
            long_clauses.append(proof[-1])
        

        # implications between two (new) variables.
        two_var_clauses = []
        conflicts = {}
        for nv1 in D.keys():
            for nv2 in D.keys():
                pos1, pos2 = D[nv1], D[nv2]
                if nv1  < nv2  and all_distances_leq(pos1, pos2, color):
                    inter = intersection(D[nv1], D[nv2])
                    if len(inter) != 0:
                        continue

                    intersection_clause = [self.V[(p, color)] for p in inter]
                    clauses.append([-nv1, -nv2] + intersection_clause)
                    for p in D[nv1]:
                        for q in D[nv2]:
                            if p not in inter and q not in inter:
                                conflicts_solved[(p, q)] = True
                                conflicts_solved[(q, p)] = True
                                
                    two_var_clauses.append(clauses[-1])
                    if nv1 not in conflicts:
                        conflicts[nv1] = []
                    if nv2 not in conflicts:
                        conflicts[nv2] = []
                    conflicts[nv1].append(nv2)
                    conflicts[nv2].append(nv1)

        # positions that are in conflict between a variable without being in a two-variable conflict
        deletions = {}
        for nv in D.keys():
            pos_nv = D[nv]
            for pos in self.positions:
                add_clause = False
                if pos not in pos_nv and all_distances_leq(pos_nv, [pos], color):
                    add_clause = True
                    if pos in M and nv in conflicts: # pos is part of another variable
                        # we need to check whether it's part of a two-variable conflict
                        for nv2 in M[pos]:
                            if nv2 in conflicts[nv]:
                                add_clause = False
                                break
                    if add_clause:
                        clauses.append([-nv, -1*self.V[(pos, color)]])
                        proof.append(clauses[-1])
                        for des in D[nv]:
                            a, b = self.V[(pos, color)], self.V[(des, color)]
                            if (min(a,b), max(a,b)) not in deletions:
                                proof.append(['d', -1*a, -1*b])
                                deletions[(min(a,b), max(a,b))] = True
                if add_clause:
                    for p in pos_nv:
                        conflicts_solved[(pos, p)] = True
                        conflicts_solved[(p, pos)] = True
                        
        proof.extend(two_var_clauses)

        # conflicts that are not captured by new variables
        for pos in self.positions:
            for pos2 in self.positions:
                if self.V[(pos, color)] <  self.V[(pos2, color)] and dist(pos, pos2) <= color:
                    if (pos, pos2) not in conflicts_solved:
                        clauses.append([-1*self.V[(pos, color)], -1*self.V[(pos2, color)]])

        for long in long_clauses:
            proof.append(['d'] + long)
        return clauses, proof

    def cubes(self, n_colors_to_split, n_positive_lits,  new_vars_per_color, n_new_vars_to_split, reverse_cubes=False, center_force=None):
        cbs = []
        rel_colors = list(range(self.colors, self.colors-n_colors_to_split, -1))
        if center_force in rel_colors:
            rel_colors.append(min(rel_colors)-1)
            rel_colors.remove(center_force)

        assert len(rel_colors) == n_colors_to_split
        vpc = {}
        print(rel_colors)
        for col in rel_colors:
            new_vars_to_use  = sorted(new_vars_per_color[col], key=dist_to_center)[:n_new_vars_to_split]
            vpc[col] = [self.V[('n', col, tuple(t))] for t in new_vars_to_use]
        for cb_size in range(n_positive_lits, -1, -1):
            for cmb in itertools.combinations(list(range(n_colors_to_split)), cb_size):
                    products = itertools.product(*([vpc[rel_colors[i]] for i in cmb]))
                    negations = []
                    if cb_size != n_positive_lits:
                        for color_id, color in enumerate(rel_colors):
                            if color_id not in cmb:
                                negations.extend([-1*v for v in vpc[color]])
                    for product in products:
                        cbs.append(list(product) + negations)
        if reverse_cubes:
            cbs = list(reversed(cbs))
        return cbs # + [[]]


def dist_to_center(shape):
    s = 0
    for pos in shape:
        s += dist(pos, (0,0))
    return s

def dist(p1, p2):
    return abs(p1[0]-p2[0]) + abs(p1[1] - p2[1])

def all_distances_leq(p1, p2, k):
    for pos1 in p1:
        for pos2 in p2:
            if dist(pos1, pos2) > k:
                return False
    return True

def intersection(l1, l2):
    ans = []
    for a in l1:
        if a in l2:
            ans.append(a)
    return ans

def process_ordered_pair(op_str):
    t_1, t_2 = op_str.split(',')
    return (int(t_1[1:]), int(t_2[:-1]))

def main_octant(i, j):
    return i >= 0 and j >= i

def above_diag(i, j):
    # director = (-1, 1)
    return -1*i + j > 0


def dot_prod(a, b):
    ans = 0
    assert len(a) == len(b)
    for i in range(len(a)):
        ans += a[i]*b[i]
    return ans

class Transformation:
    def __init__(self, matrix):
        self.mat = matrix

    def apply(self, point):
        return [dot_prod(list(point), row) for row in self.mat]

    def multiply(self, mat2):
        cols2 = [[row[i] for row in mat2.mat] for i in range(len(mat2.mat[0]))]
        return Transformation([[dot_prod(row, col) for col in cols2] for row in self.mat])

    def __eq__(self, other):
        return self.mat == other.mat

    def __hash__(self):
        tup = [tuple(row) for row in self.mat]
        return hash(tuple(tup))

VERTICAL = Transformation([[1, 0], [0, -1]])
DIAGONAL = Transformation([[0, 1], [1, 0]])
HORIZONTAL = Transformation([[-1, 0], [0, 1]])
IDENTITY = Transformation([[1, 0], [0, 1]])

def to_break_symmetry(pos, color):
        return dist(pos, (0,0)) <= color//2 and not main_octant(*pos)

def transformation_to_main_octant(pos):
    x, y = pos
    trans = IDENTITY
    if y < 0:
        trans = trans.multiply(VERTICAL)
    if x < 0:
        trans = trans.multiply(HORIZONTAL)
    if x > y:
        trans = trans.multiply(DIAGONAL)
    return trans
