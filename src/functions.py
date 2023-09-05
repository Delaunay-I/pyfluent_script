from ansys.fluent.core import launch_fluent
import re, sys
from io import StringIO
from scipy import stats
import numpy as np


class TimeAdvance:
    """
    This class represents a time advance analysis.

    Parameters:
        iResWinSize (int): The size of the residual window for analysis.
        iDummyDMDIter (int, optional): The iteration to do a dummy DMD analysis (default is 0).

    Attributes:
        iResWindowSize (int): The size of the residual window for slope analysis.
        iDummyDMDIter (int): The iteration that we start recording the residual norms.
        resWindow (numpy.ndarray): An array to store the residuals.
        LRx (numpy.ndarray): An array of indices for regression.
        slope_old (float): The previous slope value.
        slope_ratio (float): .

    Methods:
        slope_analysis(resNorm, iter):
            Perform slope analysis on the given data.

        solve_steps(self, solver, num_iters):

        ext_resNorms(self, input_string):

    """
    def __init__(self, iResWinSize, iDummyDMDIter = 0):
        self.iResWindowSize = iResWinSize
        self.iDummyDMDIter = iDummyDMDIter
        self.resWindow = np.array([], dtype=float)

        self.LRx = np.arange(0, self.iResWindowSize)

        self.slope_old = 0
        self.slope_ratio = -1
        
    def solve_steps(self, solver, num_iters):
        tmp = sys.stdout
        my_result = StringIO()
        sys.stdout = my_result
        solver.solution.run_calculation.iterate(iter_count=num_iters)
        sys.stdout = tmp

        iter, var1, var2, var3 = self.ext_resNorms(my_result.getvalue())
        resWin_avgSlope = -1

        if var1!=None and var2!=None and var3!=None:
            res_avg = (var1 + var2 + var3) / 3
            self.slope_analysis(res_avg, iter)
            print(f"iter:{iter:04} continuity:{var1:.4e}\tx-velocity:{var2:.4e}\ty-velocity:{var3:.4e}\tSlope_ratio:{self.slope_ratio:.4f}")
        else:
            print(my_result.getvalue())
            res_avg = 0

        return res_avg, self.slope_ratio


    def slope_analysis(self, resNorm, iter):
        """
        This function checks the average residual norms continuously,
        and returns the slope ratio of two consecutive residual windows

        The goal of this method is to check if the convergence history has a constant average slope

        Also, this function works with the log-scale of the residual norms.
        The reason is that we are plot the convergence history in log scale,
        and the log-scale can better interpret the evolution at this small scale
        """
        resNorm = np.log(resNorm)
        if iter >= self.iDummyDMDIter:
            self.resWindow = np.append(self.resWindow, resNorm)
        if iter >= self.iDummyDMDIter + self.iResWindowSize:
            self.resWindow = self.resWindow[1:]

            assert self.resWindow.shape == self.LRx.shape, f"""the X and Y shapes for regression are not the same.
resWindow.shape: {self.resWindow.shape}\t LRx.shape: {self.LRx.shape}"""
            
            slope, intercept, r, p, std_err = stats.linregress(self.LRx, self.resWindow)
            # print(f"slope_analysis|\tslope:{slope:.2e}, intercept:{intercept:.2e}, r:{r:.2e}, p:{p:.2e}, std_err:{std_err:.2e}")

            if iter >= self.iDummyDMDIter + self.iResWindowSize + 1:
                self.slope_ratio = slope / self.slope_old
                self.slope_old = slope
            else:
                self.slope_old = slope
   


    def ext_resNorms(self, input_string):
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
