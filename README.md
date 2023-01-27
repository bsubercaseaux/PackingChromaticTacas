# The Packing Chromatic Number of the Infinite Square Grid is 15. (TACAS'2023)

by Bernardo Subercaseaux and Marijn J. H. Heule.

---

### Required software

1. Python 3.10.0 
2. Python libraries specified in the 'requirements.txt' file. (Run `pip3 install -r requirements.txt`).
3. CaDiCaL
4. ...


### Instructions

1. **Direct Encoding**

To use the direct encoding one must run the file `src/direct.py`. 
This `src/direct.py` file takes several CLI arguments. 
For now, the documentation will only cover the subset required to reproduce the results in our paper.

To generate the direct encoding on $$D_r$$, with colors $$\{1, \ldots, k\}$$ and assigning color $$c$$ to the center, resulting in a file `direct-<r>-<k>-<c>.cnf`, run:

```python3 direct.py -r <r> -k <k> -c <c> -o direct-<r>-<k>-<c>.cnf```

So for example:

```
python3 direct.py -r 6 -k 11 -c 6 -o direct-6-11-6.cnf
head direct-6-11-6.cnf
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





2. Plus Encoding
3. Cube And Conquer Split





