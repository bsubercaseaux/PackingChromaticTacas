from pysat.formula import CNF
import tkinter
from tkinter import ttk
from tkinter.filedialog import asksaveasfilename
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
NavigationToolbar2Tk)
import plotter
import structured_api
import numpy as np
import matplotlib.colors as mcolors
import argparse
import json
from PIL import Image


parser = argparse.ArgumentParser(description="Interactive encoding.")
parser.add_argument('-r', '--radius', help='radius', type=int, required=True)
parser.add_argument('-k', '--colors', help='number of colors to be used', type=int, required=True)
parser.add_argument('-v', '--verbose', action='count', default=0)
parser.add_argument('-m', '--minimization', help="adds minimization clauses", action='store_true')
parser.add_argument('-c', '--centerforce', type=int, help="value to which the center is forced (-1 for no forcing, 0 for min(r, c))", default=0)
parser.add_argument('-a', '--arity', type=int, help='cube arity')
parser.add_argument('-s', '--split', type=int, help='number of new variables to use for the split')
parser.add_argument('-b', '--backcubes', help='puts cubes in reverse order', action='store_true')
parser.add_argument('-S', '--symmetry', type=int,  help='enables symmetry breaking, 2 for breaking on the 2 highest colors', default=0)
parser.add_argument('-e', '--evan', help='enables Evan clauses', action='store_true')
args = parser.parse_args()

radius = args.radius
n_colors = args.colors
verbose = args.verbose
minimization = args.minimization
evan_clauses = args.evan
reverse_cubes = args.backcubes
center_force = args.centerforce
symmetry = args.symmetry
arity = args.arity
n_new_vars_to_split = args.split
assert center_force >= -1 and center_force <= n_colors

if verbose > 0:
    for v in vars(args):
        print(f'{v} = {getattr(args,v)}')

colors = [
    'gold',
    'turquoise',
    'plum2',
    'RoyalBlue1',
    'salmon2',
    'goldenrod3',
    'DarkOrchid1',
    'spring green',
    'purple',
    'green',
    'orange',
    'black',
    'gray',
    'cyan',
    'plum1',
]
class InteractiveEncoder:
    def __init__(self, radius, colors):
        self.radius = radius
        self.colors = colors
        self.active_color = 4 # default?
        self.new_vars_per_color = {}
        for c in range(1, colors+1):
            self.new_vars_per_color[c] = []

        # tkinter stuff starts :)
        self.window = tkinter.Tk()
        self.window.title("Interactive Encoder")
        self.window.overrideredirect(True)
        self.window.overrideredirect(False)
        self.window.attributes('-fullscreen',True)

        # in-window title
        self.in_window_title = tkinter.Label(
                self.window,
                text="Interactive Encoder",
                font=('Helvetica', 30))
        self.in_window_title.pack(pady=(20, 20))

        # RHS pannel
        self.pannel = tkinter.Frame(self.window, highlightbackground="red")
        self.pannel.pack(side=tkinter.RIGHT, padx=(0, 100))

        # export button
        self.export_btn = tkinter.Button(self.pannel, text='Export', command=self.export)
        self.export_btn.pack(side=tkinter.BOTTOM)

        # export placement button
        self.export_placement_btn = tkinter.Button(self.pannel, text='Export placement', command=self.export_placement)
        self.export_placement_btn.pack(side=tkinter.BOTTOM)

        # number of clauses labels
        self.clauses_label_var = tkinter.StringVar()
        self.clauses_label_var.set('#vars = 0, #clauses = 0')
        self.clauses_label = tkinter.Label(
                self.pannel,
                textvariable=self.clauses_label_var,
                font=('Helvetica', 18))
        self.clauses_label.pack()

        # Structurer! :)
        self.structurer = structured_api.Structure(self.radius, self.colors)
        self.proof = []
        self.update_clauses() # note that this needs to go after the creation of the clauses_label, as it updates its value

        # active color selector
        self.color_selector_frame = tkinter.Frame(self.pannel)
        self.color_selector_frame.pack()
        self.active_color_selector = ttk.Combobox(
                self.color_selector_frame,
                state="readonly", 
                values=list(range(2, self.colors+1)))
        self.active_color_selector.pack(side=tkinter.RIGHT)
        self.active_color_selector.current(2) # set default
        self.active_color_selector.bind("<<ComboboxSelected>>", self.active_color_change)
        self.active_color_selector_label = tkinter.Label(
                self.color_selector_frame, 
                text="Active color",
                font=('Helvetica', 18))
        self.active_color_selector_label.pack(side=tkinter.LEFT)

        # active shape 
        self.active_shape = [(0, 0), (0, -1), (-1, 0), (1, 0), (0, 1)]
        self.shape_selector_frame = tkinter.Frame(self.pannel)
        self.shape_selector_frame.pack()
        self.active_shape_svar = tkinter.StringVar()
        self.active_shape_svar.set(f'Active shape = {self.active_shape}')
        self.active_shape_label = tkinter.Label(
                self.shape_selector_frame,
                textvariable=self.active_shape_svar,
                font=('Helvetica', 18))
        self.active_shape_label.pack()
        self.active_shape_entry = tkinter.Entry(self.shape_selector_frame)
        self.active_shape_entry.pack()
        self.shape_change_btn = tkinter.Button(self.shape_selector_frame, text='Change shape', command=self.change_shape)
        self.shape_change_btn.pack()

        # replicate for other colors with a box
        self.replicator_frame = tkinter.Frame(self.pannel)
        self.replicator_frame.pack()
        self.replicator_entry = tkinter.Entry(self.replicator_frame)
        self.replicator_entry.pack()
        self.replicator_btn = tkinter.Button(self.replicator_frame, text='Replicate', command=self.replicate)
        self.replicator_btn.pack()


       # plot
        self.canvas = tkinter.Canvas(self.window, width=800, height=800, highlightthickness=0, bg='white')
        self.canvas.pack(padx=(30, 30), pady=(0, 0))
        self.rec_side = 800 // (2*self.radius+2)
        self.canvas.update()
        self.update_plot()


        # mouse position
        self.mouse_pos_var = tkinter.StringVar()
        self.mouse_pos = tkinter.Label(self.pannel, textvariable=self.mouse_pos_var)
        self.mouse_pos.pack(side=tkinter.BOTTOM)
        # mouse activity
        self.window.bind('<Button-1>', self.click)

        tkinter.mainloop()

    def click(self, event):
        w, h = self.canvas.winfo_reqwidth(), self.canvas.winfo_reqheight()
        print(f'w = {w}, h = {h}')
        rel_x = event.x - w//2+self.rec_side//2
        rel_y = event.y - h//2-self.rec_side//2
        sq_relx, sq_rely  = rel_x // self.rec_side, (-1*rel_y) // self.rec_side
        self.mouse_pos_var.set(f'mouse at {event.x, event.y} out of {h, w}. Rel square {sq_relx, sq_rely}')
        new_var = center_shape(self.active_shape, (sq_relx, sq_rely))
        # check that new_var is within borders
        if structured_api.all_distances_leq(new_var, [(0, 0)], self.radius):        
            self.new_vars_per_color[self.active_color].append(new_var)
            #self.update_clauses()
            self.update_plot()

    def update_clauses(self):
        self.clauses = self.structurer.long_clauses()
        conflict_clauses, conflict_proof = self.structurer.conflict_clauses(self.new_vars_per_color)
        self.clauses.extend(conflict_clauses)
        self.proof = conflict_proof
        foreign_clauses = False
        if foreign_clauses:
            foreign_cls = self.structurer.foreign_clauses()
            self.clauses.extend(foreign_cls)
        if evan_clauses:
            evan_cls = self.structurer.evan_clauses()
            self.clauses.extend(evan_cls)
        if minimization:
            min_clauses = self.structurer.minimization_clauses()
            self.clauses.extend(min_clauses)
            self.proof.extend(min_clauses)
        if symmetry:
            symmetry_clauses = self.structurer.symmetry_breaking()
            self.clauses.extend(symmetry_clauses)
        if center_force != -1:
            center_clause = self.structurer.center_force(center_force)
            self.clauses.append(center_clause)
            self.proof.append(center_clause)
        self.clauses_label_var.set(f'#vars = {n_vars_from_clauses(self.clauses)}, #clauses = {len(self.clauses)}')

    def update_plot(self):
        self.canvas.delete('all')
        mh = self.canvas.winfo_reqwidth()//2
        mv = self.canvas.winfo_reqheight()//2
        for i in range(-self.radius, self.radius+1):
            for j in range(-self.radius, self.radius+1):
                if abs(i) + abs(j) <= self.radius:
                    top_left = (mh-self.rec_side//2 + i*self.rec_side, mv-self.rec_side//2 - j*self.rec_side)
                    bottom_right = (top_left[0] + self.rec_side+1, top_left[1] + self.rec_side+1)
                    part_of_new = False
                    for idx, nv in enumerate(self.new_vars_per_color[self.active_color]):
                        if (i, j) in nv:
                            part_of_new = True
                            self.canvas.create_rectangle(top_left[0], top_left[1], bottom_right[0], bottom_right[1], fill=colors[idx%(len(colors))])
                            self.canvas.create_text(top_left[0] + self.rec_side//2, top_left[1] + self.rec_side//2, text=str(idx), font=('Helvetica', 22))
                            break 
                    if not part_of_new:
                        self.canvas.create_rectangle(top_left[0], top_left[1], bottom_right[0], bottom_right[1], fill='red')


    def active_color_change(self, event):
        selection = self.active_color_selector.get()
        self.active_color = int(selection)
        self.update_plot()

    def change_shape(self):
        shape_text = self.active_shape_entry.get()
        self.active_shape = parse_shape(shape_text)
        self.active_shape_svar.set(f'Active shape = {self.active_shape}')
        self.shape_selector_frame.propagate(0)

    def replicate(self):
        rep_text = self.replicator_entry.get()
        bgn, end = rep_text.split('-')
        bgn, end = int(bgn), int(end)
        if bgn < 2 or bgn > end or end > self.colors:
            return
        for color in range(bgn, end+1):
            self.new_vars_per_color[color] = list(self.new_vars_per_color[self.active_color])
        self.update_clauses()
        print('updated!')

    def export(self):
        filename = asksaveasfilename()
        print(f'filename = {filename}')
        self.canvas.postscript(file = filename + '.eps') 
        img = Image.open(filename + '.eps')
        img.save(filename + '.png', 'png') 
        cnf = CNF(from_clauses=self.clauses)
        cnf.to_file(filename)
        proof_to_file(self.proof, filename+'.drat')

    def export_placement(self):
        filename = asksaveasfilename()
        with open(filename, 'w') as f:
            json.dump(self.new_vars_per_color, f, sort_keys=True)

def n_vars_from_clauses(clauses):
    set_vrs = set()
    for clause in clauses:
        for lit in clause:
            set_vrs.add(abs(lit))
    return len(set_vrs)

def parse_shape(shape_txt):
    tokens = shape_txt.split(' ')
    ans = []
    for token in tokens:
        without_par = token[1:-1]
        numbers = without_par.split(',')
        ans.append((int(numbers[0]), int(numbers[1])))
    return ans

def center_shape(shape, center):
    return [(s[0] + center[0], s[1] + center[1]) for s in shape]

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

InteractiveEncoder(radius, n_colors)
