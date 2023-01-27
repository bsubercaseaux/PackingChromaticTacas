import json
from pysat.formula import CNF
import argparse
import structured_api

parser = argparse.ArgumentParser(description="Placement to encoding.")
parser.add_argument('-r', '--radius', help='radius', type=int, required=True)
parser.add_argument('-k', '--colors', help='number of colors to be used', type=int, required=True)
parser.add_argument('-i', '--input', help='name of the input placement file', required=True)
parser.add_argument('-o', '--output', help='basename of the output files', required=True)
parser.add_argument('-v', '--verbose', action='count', default=0)
parser.add_argument('-m', '--minimization', help="adds minimization clauses", action='store_true')
parser.add_argument('-c', '--centerforce', type=int, help="value to which the center is forced (-1 for no forcing, 0 for min(r, c))", default=0)
parser.add_argument('-p', '--positive', type=int, help='max number of positive literals in the split')
parser.add_argument('-z', '--splitcolors', type=int, help='number of colors to split')
parser.add_argument('-s', '--split', type=int, help='number of new variables to use for the split')
parser.add_argument('-b', '--backcubes', help='puts cubes in reverse order', action='store_true')
parser.add_argument('-S', '--symmetry', type=int,  help='enables symmetry breaking, 2 for breaking on the 2 highest colors', default=0)
parser.add_argument('-a', '--alod', type=int, help='enables ALOD clauses', default=0)
parser.add_argument('-f', '--foreign', help='foreign clauses', action='store_true')
parser.add_argument('--symver', help='name for the symmetry verification file', default=None)
parser.add_argument('-B', '--borderones', type=int, help='maximum number of ones in the border', default=0)
parser.add_argument('-C', '--chessboard', help='forces the chessboard pattern of 1s', action='store_true')
parser.add_argument('--singlecolor', type=int, help='specify a single color for clauses', default=None)
args = parser.parse_args()


radius = args.radius
n_colors = args.colors
input_file = args.input
output_file = args.output
verbose = args.verbose
minimization = args.minimization
alod_clauses = args.alod
reverse_cubes = args.backcubes
center_force = args.centerforce
symmetry = args.symmetry
positive_lits = args.positive
foreign = args.foreign
colors_to_split = args.splitcolors
n_new_vars_to_split = args.split
assert center_force >= -1 and center_force <= n_colors
border_ones = args.borderones
chessboard = args.chessboard
symverfilename = args.symver
singlecolor = args.singlecolor

if verbose > 0:
    for v in vars(args):
        print(f'{v} = {getattr(args,v)}')

structurer = structured_api.Structure(radius, n_colors, symmetry)

clauses = []
if singlecolor is None:
    clauses = structurer.long_clauses()
with open(input_file, 'r') as f:
    placement_map_json = json.load(f)


placement_map = {}
for k,v in placement_map_json.items():
    placement_map[int(k)] = list(map(lambda x: list(map(tuple, x)), v))


conflict_clauses, conflict_proof = structurer.conflict_clauses(placement_map, singlecolor)
clauses.extend(conflict_clauses)
proof = conflict_proof
alod_proof = []

if center_force != -1:
    center_clause = structurer.center_force(center_force) 
    clauses.append(center_clause)
    proof.append(center_clause)

if alod_clauses:
    alod_cls = structurer.alod_clauses(alod_clauses)
    clauses.extend(alod_cls)
    alod_proof = alod_cls
    

if minimization:
    min_clauses = structurer.minimization_clauses()
    clauses.extend(min_clauses)
    proof.extend(min_clauses) #todo not abstractly correct

if foreign:
    foreign_clauses = structurer.foreign_clauses()
    clauses.extend(foreign_clauses)

if symmetry:
    symmetry_clauses = structurer.symmetry_breaking()
    structurer.symmetry_verification(symverfilename)
    clauses.extend(symmetry_clauses)

if border_ones:
    border_clauses = structurer.bounded_border_ones(border_ones)
    clauses.extend(border_clauses)

if chessboard:
    chessboard_clauses = structurer.chessboard()
    clauses.extend(chessboard_clauses)

def joiner(lst, fn):
    return ''.join(list(map(fn, lst)))

def cubes_to_str(cubes):
    def cube_to_str(cube):
        return 'a ' + ' '.join(list(map(str, cube))) + ' 0\n'
    return joiner(cubes, cube_to_str)

def clauses_to_str(clauses):
    def clause_to_str(clause):
        return ' '.join(list(map(str, clause))) + ' 0\n'
    return joiner(clauses, clause_to_str)

def cubes_to_file(clauses, cubes, filename):
    with open(filename, 'w') as f:
        f.write('p inccnf\n')
        f.write(clauses_to_str(clauses))
        f.write(cubes_to_str(cubes))

def proof_to_file(proof, proof_filename):
    with open(proof_filename, 'w') as f:
        for line in proof:
            fline = ' '.join(list(map(str, line + [0])))
            f.write(fline + '\n')


cnf = CNF(from_clauses=clauses)
print(f'# clauses = {len(clauses)}')
cnf.to_file(output_file + '.cnf')

if singlecolor is None:
    cubes = structurer.cubes(colors_to_split, positive_lits, placement_map, n_new_vars_to_split, reverse_cubes, center_force)
    print(f'# cubes = {len(cubes)}')
    cubes_to_file(clauses, cubes, output_file + '.icnf')
    proof_to_file(proof, output_file + '.drat')
    proof_to_file(alod_proof, output_file + '-alod.drat')
