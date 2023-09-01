from ansys.fluent.core import launch_fluent
import re, sys
from io import StringIO



def ext_resNorms(input_string):
    # Use regular expression to find variable names and values
    # '\n  iter  continuity  x-velocity  y-velocity     time/iter\n     3  5.9625e-01  1.4960e-01  1.4730e-01  0:00:00    1\n     4  4.0781e-01  7.6064e-02  7.8064e-02  0:00:00    0\n'
    pattern = r'^\s*iter\s+continuity\s+x-velocity\s+y-velocity\s+time/iter\s*[\d.e-]+\s+[\d.e-]+\s+[\d.e-]+\s+[\d.e-]+\s+[0-5]:[0-5][0-9]:[0-5][0-9]\s+[\d]\s*([\d.e-]+)\s+([\d.e-]+)\s+([\d.e-]+)\s+([\d.e-]+)\s+[0-5]:[0-5][0-9]:[0-5][0-9]\s+[\d]'

    match = re.search(pattern, input_string)

    if match:
        # Extract variable values
        iteration = int(match.group(1))
        var1 = float(match.group(2))
        var2 = float(match.group(3))
        var3 = float(match.group(4))

        return iteration, var1, var2, var3
    else:
        # If the pattern is not found in the input string, return None for all values
        return None, None, None, None
    
def solve_steps(solver, num_iters):
    tmp = sys.stdout
    my_result = StringIO()
    sys.stdout = my_result
    solver.solution.run_calculation.iterate(iter_count=num_iters)
    sys.stdout = tmp

    iter, var1, var2, var3 = ext_resNorms(my_result.getvalue())
    if var1!=None and var2!=None and var3!=None:
        print(f"iter:\t{iter}\tcontinuity\t{var1:.4e}\tx-velocity:\t{var2:.4e}\ty-velocity:\t{var3:.4e}")
        res_avg = (var1 + var2 + var3) / 3
    else:
        print(my_result.getvalue())
        res_avg = 0
    
    return res_avg
