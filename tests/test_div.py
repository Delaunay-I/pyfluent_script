from ansys.fluent.core import launch_fluent
import os
script_dir = os.path.dirname(os.path.abspath(__file__))


def test_divergence_UDF():
    solver = launch_fluent(version="2d", precision="double", processor_count=1, mode="solver")

    tui = solver.tui
    cas_fpath = os.path.normpath(os.path.join(script_dir, "..", "data", "uniform.cas.h5"))
    tui.file.read_case(cas_fpath)

    # Allocate UDMs
    tui.define.user_defined.user_defined_memory(3 + 3)

    # Compile and load UDFs
    tui.define.user_defined.auto_compile_compiled_udfs("no")
    tui.define.user_defined.compiled_functions("compile", "libudf", "y", "write_soln.c", "set_udms.c")
    tui.define.user_defined.compiled_functions("load", 'libudf')

    solver.solution.initialization.hybrid_initialize()
    dat_fpath = os.path.normpath(os.path.join(script_dir, "uniform.dat.h5"))
    solver.file.read(file_type="data", file_name=dat_fpath)
    
    tui.define.user_defined.execute_on_demand('"write_slimSoln_onDemand::libudf"')
    tui.define.user_defined.execute_on_demand('"set_Field_udms::libudf"')
    tui.define.user_defined.execute_on_demand('"calc_Grads::libudf"')

    file1 = open("total_divergence.txt", "r+")
    total_divergence = float(file1.read().strip()) 

    solver.exit()

    assert abs(total_divergence) < 1e-2, "Check if the UDMs are set from the correct field data."
