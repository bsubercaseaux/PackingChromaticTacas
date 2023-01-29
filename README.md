# The Packing Chromatic Number of the Infinite Square Grid is 15. (TACAS'2023)

by Bernardo Subercaseaux and Marijn J. H. Heule.

---

## Required software

1. `Python 3.10.0` 
2. Python libraries specified in the `requirements.txt` file. (Run `pip3 install -r requirements.txt`).
3. CaDiCaL.
4. `ppr2drat`, which shall be obtained from [https://github.com/marijnheule/ppr2drat](https://github.com/marijnheule/ppr2drat).


## Instructions

Throughout these instructions, we show how to generate the different instances for $D_6$ with $11$ colors as a running example, while also showcasing the impact of the different optimizations.

###  **1. Direct Encoding**

To use the direct encoding one must run the file `src/direct.py`. 
This `src/direct.py` file takes several CLI arguments. 
For now, the documentation will only cover the subset required to reproduce the results in our paper. For a complete list of arguments, it suffices to run

```
python3 src/direct.py --help
```

To generate the direct encoding on $D_r$ (in DIMACS format), with colors $\lbrace 1, \ldots, k \rbrace$ and assigning color $c$ to the center, resulting in a file `direct-<r>-<k>-<c>.cnf`, run:

```
python3 src/direct.py -r <r> -k <k> -c <c> -o formulas/direct-<r>-<k>-<c>
```

So for example:

```
python3 src/direct.py -r 6 -k 11 -c 6 -o formulas/direct-6-11-6
head formulas/direct-6-11-6.cnf
```

should generate the following output:

```
p cnf 935 21086
1 2 3 4 5 6 7 8 9 10 11 0
12 13 14 15 16 17 18 19 20 21 22 0
23 24 25 26 27 28 29 30 31 32 33 0
34 35 36 37 38 39 40 41 42 43 44 0
45 46 47 48 49 50 51 52 53 54 55 0
56 57 58 59 60 61 62 63 64 65 66 0
67 68 69 70 71 72 73 74 75 76 77 0
78 79 80 81 82 83 84 85 86 87 88 0
89 90 91 92 93 94 95 96 97 98 99 0
```

This formula is included as an example in the `formulas` sub-folder.

__Note__: when $c$, the center color is unspecified, the program takes $c := \min(r, k).$

To add the ALOD clauses, it suffices to add `-A 1` to the Python3 command.

To do symmetry breaking, using 5 layers (as in the article), it suffices to add `-S 5` to the Python3 command.

For example, by incorporating both, and checking the resulting file:

```
python3 src/direct.py -r 6 -k 11 -c 6 -a 1 -S 1 -o formulas/direct-6-11-6-A-S5
head formulas/direct-6-11-6-A-S5.cnf
```

We obtain the following output:

```
p cnf 935 21220
1 2 3 4 5 6 7 8 9 10 11 0
12 13 14 15 16 17 18 19 20 21 22 0
23 24 25 26 27 28 29 30 31 32 33 0
34 35 36 37 38 39 40 41 42 43 44 0
45 46 47 48 49 50 51 52 53 54 55 0
56 57 58 59 60 61 62 63 64 65 66 0
67 68 69 70 71 72 73 74 75 76 77 0
78 79 80 81 82 83 84 85 86 87 88 0
89 90 91 92 93 94 95 96 97 98 99 0
```


### **2. Plus Encoding**

The plus encoding needs to be executed in two separate steps.
The first step consists of specifying the different regions $S_i$ of the encoding (a process we call _"placing"_), and the second part takes the specification of the regions $S_i$ (we call this a _"placement"_) and produces the CNF formula.

_Note_: we provide as well the placements used in the paper inside the `placements` folder. So it is possible to skip the placing step and used the pre-generated placement files directly. 

2.1. **Placing**

To create a placement for radius $r$ and $k$ colors, run the following command:

```
python3 src/interactive_encoder.py -r <r> -k <k>
```

As a result, a new window with a GUI should pop up.
For example, for $r = 6, k = 11$, it should look like this:


![Screenshot of the interactive placement encoder for r=6, k=11.](/img/ss-placing.png?raw=true "Interactive Encoder")

This interface is composed of several parts that we explain now.

Firstly, at all points in time there is a single color $a$ (in $\lbrace 1, \ldots, k \rbrace$) that is considered _"active"_. This means that the regions $S_i$ to create will be associated to color $a$, thus creating a regional variable $r_{S_i, a}$. The default active color is $4$, as described in our paper, we do not create regional variables for colors $\lbrace 1, 2, 3\rbrace$.

At all points in time there is also an active _"shape"_, which describes the geometry of the regions $S_i$ to create. More precisely, a shape is an ordered set of 2D vectors $\vec{v}_1, \ldots, \vec{v}_m$. For example, the active shape by default is the _"plus"_ shape, which consists of the 2D vectors: $(0, 0),  (0, -1),  (0, 1),   (-1, 0),   (1, 0)$.

A _"region"_ $S_i$ is then defined by a _"shape"_ $H$ and a _"center"_ $c$. A _"center_" is simply a 2D point. The region $S_i$ is defined simply as the following set of points:

$$
    \lbrace c + \vec{v} \mid \vec{v} \in H \rbrace.
$$

In practice, to create a new region $S_i$, it suffices only to specify its center $c$, as the shape $H$ will be the current active shape (i.e., a "+" by default). To specify its center it suffices to click it on the GUI.
The next two images illustrates the _before and after_ of creating a new region.


In order to simplify the job of creating a placement, and given that it's natural for a placement to use the same regions for different colors, the GUI presents a functionality that allows to replicate the regions $S_i$ used for the active colors to other colors. In particular, by specifying a range with notation `<start>-<end>` on the `Replicate` textbox, the current regions for the active color will induce new regional variables for every color in the specified range.

For example, once we have placed the following regions for the active color $4$:


![Screenshot of the interactive placement encoder for r=6, k=11.](/img/ss-placing-4.png?raw=true "Interactive Encoder")

We can replicate them to colors $5$ through $11$ simply by typing `5-11` on the textbox and clicking on replicate.

Once a placement is complete, we need to export it as a file by clicking the `Export placement` button. Then we will simply select a filename for it, where the extension does not matter. For example, in this case we could name it `placement-6-11-plus`. 

2.2 **From placement to encoding**.

Once we have the desired placement file, we will simply use the following Python command to generate an encoding from it.

```
python3 src/from_placement.py -i <placement file> -o <output file> -r <r> -k <k>
```

Continuing with our example:

```
python3 src/from_pacement.py -i placements/placement-6-11-plus -o formulas/plus-6-11 -r 6 -k 11
```
generates `plus-6-11.cnf` in the `formulas` subfolder. Now it's a good time to test the advantages of our work.

If we were to run:

```
cadical formulas/direct-6-11.cnf
```
we would obtain an UNSAT result after several hours.

Instead, by using the plus encoding instead, we can run

```
cadical formulas/plus-6-11.cnf
```
from which we obtain the UNSAT result after roughly 11 minutes:

![Screenshot displaying the time statistics for a CaDiCaL run on plus-6-11.cnf](/img/time-plus.jpg?raw=true "Time Statistics")

_Note 2_: Both experiments have been run on my (i.e., Bernardo) personal machine (i.e., different than the one used in the paper), a MacBook Pro 2020 with M1 and 16GB of RAM.

_Note 3_: The `from_placement.py` script can take a bunch of other optional arguments. This documentation only covers the basics. By using the `--help` flag you can see a list of the optional arguments and brief descriptions about them.


To enable symmetry breaking for $5$ layers (the choice we make in the paper), we proceed exactly as with the direct encoder, by simply adding  the flag `-S 5`.
So for example after running 

```
python3 src/from_pacement.py -i placements/placement-6-11-plus -o formulas/plus-6-11-S5 -r 6 -k 11 -S 5
```

and then running

```
cadical formulas/plus-6-11-S5.cnf
```

we obtain the following runtime:



3. **Cube and Conquer split**

To execute as well the PTR algorithm, is enough to specify the parameters $P$, $T$ and $R$ when running the `from_placement.py` file.

For example, if we run the following command:

```
python3 src/from_placement.py -i placements/placement-6-11-plus -o formulas/plus-6-11-P5R5T5 -r 6 -k 11 -P 5 -T 5 -R 5
```
this will generate 7776 cubes, and store them in the file `formulas/plus-6-11-P5R5T5.icnf`, which can then be solved with any incremental solver. For example, using [iLingeling](https://github.com/arminbiere/lingeling), we can run:

```
ilingeling formulas/plus-6-11-P5R5T5.icnf 8 -v 
```
to use 8 cores. As a result, the wall-clock time of the UNSAT result is barely above a minute! Also, note that even the total runtime is better than before!

![Screenshot displaying the time statistics for an iLingeling run on p-6-11-plus-P5R5T5.icnf](/img/time-cubes-6-11.png?raw=true "Time Statistics")

4. **Verification**

Here we will cover how to verify a solution for $r = 6$, $k = 11$, using the plus encoding, symmetry breaking and the ALOD clauses.

When we run the encoding command:

```
python3 src/from_placement.py -i placements/placement-6-11-plus -o formulas/plus-6-11-A-S5 -r 6 -k 11 -a 1 -S 5
```

several different verification files are automatically generated inside of the `formulas` subfolder:

- `plus-6-11-A-S5.cnf`
- `plus-6-11-A-S5-alod.drat`
- `plus-6-11-A-S5.symver`

```
ppr2drat formulas/direct-6-11.cnf proofs/plus-6-11-A-S5.symver > proofs/proofsym-plus-6-11-A-S5.drat
cat proofs/proofsym-plus-6-11-A-S5.drat proofs/plus-6-11-A-S5-alod.drat > cb1-plus-6-11-A-S5.drat
cat cb1-plus-6-11-A-S5.drat proofs/plus-6-11-A-S5.drat > cb2-plus-6-11-A-S5.drat
cadical formulas/plus-6-11-A-S5.cnf proofs/proof-sol-plus-6-11-A-S5.drat
cat cb2-plus-6-11-A-S5.drat proofs/proof-sol-plus-6-11-A-S5.drat > proofs/final-plus-6-11-A-S5.drat
drat-trim formulas/direct-6-11.cnf proofs/final-plus-6-11-A-S5.drat -f
```


