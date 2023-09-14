from ansys.fluent.core import launch_fluent

from ansys.fluent.visualization import set_config
from ansys.fluent.visualization.matplotlib import Plots
from ansys.fluent.visualization.pyvista import Graphics

import numpy as np
import pandas as pd
# import matplotlib.pyplot as plt
import os

from dmd import DMD
from config_parser import get_configuration
from functions import file_IO
import time


script_dir = os.path.dirname(os.path.abspath(__file__))
NUM_SNAPS, NUM_DMD_MODES, ITER_NUM, DMD_ITER, NUM_VARS, case_file_path, outfName = get_configuration()

DT = 1
assert min(DMD_ITER) > NUM_SNAPS, "number of iterations is smaller than number of snapshots"
FLAG_DMD = True
CALC_MODES = True
APPLY_DMD = True

# =======================
# Problem Setup
# =======================
solver = launch_fluent(version="2d", precision="double", processor_count=11, mode="solver")

tui = solver.tui
# Read the mesh file and set the configuration
cas_file_path = os.path.normpath(case_file_path)
cas_file_path = cas_file_path.replace("\\", "/")
tui.file.read_case(cas_file_path)

# Allocate UDMs
tui.define.user_defined.user_defined_memory(NUM_VARS + 3)

# Compile and load UDFs
tui.define.user_defined.auto_compile_compiled_udfs("no")
tui.define.user_defined.compiled_functions("compile", "libudf", "y", "write_soln.c", "apply_update.c", "set_udms.c")
tui.define.user_defined.compiled_functions("load", 'libudf')
tui.define.user_defined.function_hooks("execute-at-end", '"write_slimSoln_par::libudf"')


tui.solve.monitors.residual.normalize('yes')
tui.solve.monitors.residual.criterion_type(3) # Convergence checking is disabled.
tui.solve.monitors.residual.n_save(ITER_NUM) # number of history points to be stored
tui.solve.monitors.residual.n_display(ITER_NUM)


# solver.solution.run_calculation.pseudo_time_settings.time_step_method.time_step_method = 'user-specified'
# solver.solution.run_calculation.pseudo_time_settings.time_step_method.pseudo_time_step_size = DT

# Initialize the snapshots matrix
data = None
solver.solution.initialization.hybrid_initialize()


soln_file_path = os.path.normpath(os.path.join(script_dir, "..", "solver_data"))
IO = file_IO(soln_file_path)
res_norm = []

for iter in range(1, ITER_NUM+1):
    start_time = time.time()
    solver.solution.run_calculation.iterate(iter_count=1)
    end_time = time.time()
    print(f"\033[33mElapsed time: {end_time - start_time} seconds\033[0m")


    if FLAG_DMD:
        vSoln = IO.read_soln()
        print(vSoln.shape)

        if iter == 1:
            vSoln_old = vSoln

        elif iter > 1:        
            vSoln_update = vSoln - vSoln_old
            vSoln_old = vSoln

            data = vSoln_update if data is None else np.hstack((data, vSoln_update))
            if data.shape[1] > NUM_SNAPS:
                data = data[:, -NUM_SNAPS:]

    if FLAG_DMD and (iter in DMD_ITER):
        my_dmd = DMD(data, NUM_VARS, NUM_DMD_MODES, verbose=2)
        my_dmd.calc_DMD()

        if CALC_MODES:
            my_dmd.calc_DMD_modes(DT)
            my_dmd.write_modes_to_file()
            # tui.define.user_defined.execute_on_demand('"set_Field_udms::libudf"')

        if APPLY_DMD:
            IO.write_file(my_dmd.dmd_update_col)
            tui.define.user_defined.execute_on_demand('"apply_update_par::libudf"')
            

residual_norm = np.array(res_norm)
np.savetxt('residual_avg.plt', residual_norm)

# ===================
# Visualization Part
# ===================
# figure = plt.figure(figsize=(8,6), dpi=120)
# plt.plot(all_amps)

# plt.xlabel('Iteration')
# plt.ylabel("Magnitude of amplification factors")
# plt.title('Progression of the dominant DMD modes')
# plt.grid(True, alpha=0.5, linestyle='--')
# plt.tight_layout()

# legend_labels = [f'mode {i+1}' for i in range(all_amps.shape[1])]
# plt.legend(legend_labels)

# plt.show()


# ====================
# Data Recording Part
# ====================
res_file_path = os.path.normpath(os.path.join(script_dir, "..", "out", "res", outfName + "_res.plt"))
res_file_path = res_file_path.replace("\\", "/")

if os.path.exists(res_file_path):
    os.remove(res_file_path)
    print(f'{res_file_path} has been deleted')
else:
    print(f'{res_file_path} does not exist')

tui.plot.residuals_set("plot-to-file", res_file_path)
tui.plot.residuals('y', 'y', 'y')


outfName = os.path.normpath(os.path.join(script_dir, "..", "out", outfName))
# solver.file.write(file_name=outfName, file_type="case")
solver.file.write(file_name=outfName, file_type="data")


solver.exit()
