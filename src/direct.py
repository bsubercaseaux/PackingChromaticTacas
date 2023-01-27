import argparse
from structured_api import Structure

parser = argparse.ArgumentParser(description="Generator of instances with the direct encoding.")
parser.add_argument('-o', '--output', help='name of the generated .cnf file', default='enc.cnf')
parser.add_argument('-r', '--radius', help='radius (or side for squares)', type=int, required=True)
parser.add_argument('-k', '--colors', help='number of colors to be used', type=int, required=True)
parser.add_argument('-g', '--geometry', help='geometry (square or diamond)',type=str, default="diamond")
parser.add_argument('-v', '--verbose', action='count', default=0)
parser.add_argument('-a', '--alod', type=int, help="adds ALOD clauses", default=0)
parser.add_argument('-c', '--centerforce', type=int, help="value to which the center is forced (-1 for no forcing, 0 for min(r, c))", default=0)
parser.add_argument('-u', '--units', help="allows introducing unit clauses, format is (i_1,j_1,c_1);...;(i_n, j_n, c_n)", default=None)
parser.add_argument('--unit_ints', help="allows introducing unit clauses as ints, a string in quotes of ints separated by semi-colons", default=None)
parser.add_argument('--chessboard', help="toggles the chessboard of ones; i.e., 1s forced at odd parities", action='store_true')
parser.add_argument('--singlecolor', help="encode only constraints for a single color", type=int, default=None)
parser.add_argument('-S', '--symmetry', type=int, help="symmetry breaking layers", default=0)
args = parser.parse_args()

filename = args.output
radius = args.radius
colors = args.colors
verbose = args.verbose
geometry = args.geometry
alod_clauses = args.alod
center_force=args.centerforce
assert center_force >= -1 and center_force <= colors
units = args.units
unit_ints = args.unit_ints
chessboard = args.chessboard
single_color = args.singlecolor
symmetry = args.symmetry

if verbose > 0:
    print("Parameters:")
    print(f" output = {filename}")
    print(f" radius/size = {radius}")
    if geometry != "diamond":
        geometry = "square"
    print(f" geometry  = {geometry}")
    print(f" maximum color  = {colors}")
    print(f" ALOD clauses  = {alod_clauses}")
    print(f" forcing center to  = {min(radius, colors) if center_force == 0 else center_force}")
    print(f" units = {units}")
    print(f" chessboard = {chessboard}")
    print(f" symmetry = {symmetry}")


structurer = Structure(radius, colors, symmetry)
V = {}
IV = {}

clauses = []

positions = []
if geometry == "diamond":
    for i in range(-radius, radius+1):
        for j in range(-radius, radius+1):
            if abs(i) + abs(j) > radius: continue
            positions.append((i, j))
else:
    for i in range(radius):
        for j in range(radius):
            positions.append((i, j))



# variables 
for pos in positions:
    i, j = pos
    for t in range(1, colors+1):
        V[(i, j, t)] = len(V) + 1
        IV[V[(i, j, t)]] = (i, j, t)

def vdirs_k(k): 
        vdirs = [] 
        for i in range(k+1): 
                for j in range(k+1-i): 
                        if i + j == 0: continue # distance > 0
                        _is = set([i, -i])
                        _js = set([j, -j])
                        for _i in _is:
                                for _j in _js:
                                        vdirs.append((_i, _j))
        return vdirs


# at least one color
if single_color is None: # otherwise we don't include positive clauses
    for pos in positions:
        i, j = pos
        clause = [V[(i, j, t)] for t in range(1, colors+1)]
        clauses.append(clause)

if alod_clauses:
    clauses.extend(structurer.alod_clauses(alod_clauses))

# chessboard of 1s at odd parities
if chessboard:
    for pos in positions:
        i, j = pos
        if (i+j)%2:
            clauses.append([V[(i,j,1)]])

## clauses forbidding x_{i,j,v} and x_{a,b,v} if dist(i, j, a, b) <= v.
if single_color is None:
    colors_to_constrain = range(1, colors+1)
else:
    colors_to_constrain = [single_color]

for clr in colors_to_constrain:
        vdirs = list(filter(lambda x: x[0] > 0 or (x[0] == 0 and x[1] > 0), vdirs_k(clr)))
        for pos in positions:
            i, j = pos
            for vdir in vdirs:
                    di, dj = vdir
                    new_i, new_j = i+di, j +dj
                    if (new_i, new_j) in positions:
                        clauses.append([-V[(i, j, clr)], -V[(new_i, new_j, clr)]]) 

# force center
if center_force != -1:
    if geometry == 'diamond':
        if center_force == 0:
            clauses.append([V[(0, 0, min(radius, colors))]])
        else:
            clauses.append([V[(0, 0, center_force)]])
    else:
        if center_force == 0:
            clauses.append([V[(radius//2, radius//2 , min(radius//2, colors))]])
        else:
            clauses.append([V[(radius//2, radius//2 , center_force)]])
    

if symmetry:
    clauses.extend(structurer.symmetry_breaking())


# units
if units is not None:
    arr_units = units.split(';')
    for unit in arr_units:
        vals = unit[1:-1].split(',')
        si, sj, sc = vals
        clauses.append([V[(int(si), int(sj), int(sc))]])
if unit_ints is not None:
    arr_units = unit_ints.split(';')
    for unit in arr_units:
        clauses.append([int(unit)])

def clause_to_text(clause):
        return " ".join(map(str, clause + [0]))

def write_to_file(clauses, filename):
        with open(filename, 'w') as file:
                file.write(f"p cnf {len(V)} {len(clauses)}\n")
                for clause in clauses:
                        file.write(clause_to_text(clause) + '\n')
        if verbose > 0:
            print(f"# vars = {len(V)}, # clauses = {len(clauses)}")


write_to_file(clauses, filename)
