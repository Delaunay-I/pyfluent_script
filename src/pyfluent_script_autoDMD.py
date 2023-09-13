from ansys.fluent.core import launch_fluent

from ansys.fluent.visualization import set_config
from ansys.fluent.visualization.matplotlib import Plots
from ansys.fluent.visualization.pyvista import Graphics

import numpy as np
import pandas as pd
# import matplotlib.pyplot as plt
import os

from dmd import DMD
from functions import TimeAdvance
from config_parser import get_configuration
from ml.MLmodel import ML_proba

script_dir = os.path.dirname(os.path.abspath(__file__))
NUM_SNAPS, NUM_DMD_MODES, ITER_NUM, DMD_ITER, NUM_VARS, case_file_path, outfName = get_configuration()

DT = 1
assert min(DMD_ITER) > NUM_SNAPS, "number of iterations is smaller than number of snapshots"
FLAG_DMD = False
CALC_MODES = True
APPLY_DMD = True
F_AUTO_DMD = False
ML_Proba_thresh = 0.7
SLOPE_TOL = 1e-4

# =======================
# Problem Setup
# =======================
solver = launch_fluent(version="2d", precision="double", processor_count=6, mode="solver")

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
# tui.define.user_defined.function_hooks("execute-at-end", '"write_slimSoln_par_optimized::libudf"')


tui.solve.monitors.residual.normalize('yes')
tui.solve.monitors.residual.criterion_type(3) # Convergence checking is disabled.
tui.solve.monitors.residual.n_save(ITER_NUM) # number of history points to be stored
tui.solve.monitors.residual.n_display(ITER_NUM)


# solver.solution.run_calculation.pseudo_time_settings.time_step_method.time_step_method = 'user-specified'
# solver.solution.run_calculation.pseudo_time_settings.time_step_method.pseudo_time_step_size = DT

# Initialize the snapshots matrix
data = None
# all_s = []
solver.solution.initialization.hybrid_initialize()
res_norm = []

# timeAdvance_tools= TimeAdvance(iResWinSize=100, iDummyDMDIter=10)
# previous_dmdUpdate_iter = ITER_NUM*2
slope_ratio=0
for iter in range(1, ITER_NUM+1):
    # res_avg, slope_ratio = timeAdvance_tools.solve_steps(solver, num_iters=1000)
    # res_norm.append(res_avg)
    solver.solution.run_calculation.iterate(iter_count=1500)


    if FLAG_DMD:
        soln_file_path = os.path.normpath(os.path.join(script_dir, "..", "solver_data", "soln.csv"))
        df = pd.read_csv(soln_file_path, sep="\t", skiprows=1, index_col=0)
        vSoln = np.concatenate([df[col] for col in df.columns[-NUM_VARS:]]).reshape(-1, 1)

        if iter == 1:
            vSoln_old = vSoln

        elif iter > 1:        
            vSoln_update = vSoln - vSoln_old
            vSoln_old = vSoln

            data = vSoln_update if data is None else np.hstack((data, vSoln_update))
            if data.shape[1] > NUM_SNAPS:
                data = data[:, -NUM_SNAPS:]

    if FLAG_DMD and ((iter in DMD_ITER) or (abs(slope_ratio - 1) <= SLOPE_TOL and F_AUTO_DMD)):
    # if iter > NUM_SNAPS:
        my_dmd = DMD(data, NUM_VARS, NUM_DMD_MODES, verbose=2)
        my_dmd.calc_DMD()

        if CALC_MODES:
            my_dmd.calc_DMD_modes(DT)
            my_dmd.write_modes_to_file()
            # tui.define.user_defined.execute_on_demand('"write_slimUpdate_onDemand::libudf"')
            # tui.define.user_defined.execute_on_demand('"set_Field_udms::libudf"')
            # tui.define.user_defined.execute_on_demand('"calc_Grads::libudf"')

            # sVals = np.diag(my_dmd.Sr)
            # all_s.append(sVals/sVals[0])

        # the ML automation pipelien is only applicable when we have 9 modes
        if APPLY_DMD and (not F_AUTO_DMD or my_dmd.r >= 9):
            # my_dmd.collect_ML_data()
            # effectiveness_proba = ML_proba(my_dmd.dmd_dataset)
            effectiveness_proba = 1000

            if (effectiveness_proba > ML_Proba_thresh):
                print(f"\033[32mProbability of the DMD update to be effective: {effectiveness_proba:.3f}\033[0m")

                tui.define.user_defined.execute_on_demand('"apply_update_par::libudf"')
                if F_AUTO_DMD:
                    previous_dmdUpdate_iter = iter
                    print("\n------Temporarily deactivating DMD...------\n")
                    FLAG_DMD = False
            else:
                print(f"\033[33mProbability of the DMD update to be effective: {effectiveness_proba:.3f}\033[0m")


    # mandating the solver to waint at least for NUM_SNAPS iterations, before applying another DMD update (for the auto DMD module)
    if iter > previous_dmdUpdate_iter + NUM_SNAPS and F_AUTO_DMD and not FLAG_DMD:
        print("\n------Re-activating DMD!!------\n")
        FLAG_DMD = True



residual_norm = np.array(res_norm)
np.savetxt('residual_avg.plt', residual_norm)


# all_s = np.array(all_s)
# np.savetxt(outfName + '_singularvalues_s' + str(NUM_SNAPS) +'_m' + str(NUM_DMD_MODES) +  '.csv', all_s)

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
