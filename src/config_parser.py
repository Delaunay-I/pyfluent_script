
import argparse
import os

def parse_config(file_path):
    with open(file_path, 'r') as file:
        return file.read().strip().split()

def get_configuration():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    directories = ['solver_data', 'out']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)

    parser = argparse.ArgumentParser()
    parser.add_argument("-case", type=str, help="path to the CASE file")
    parser.add_argument("-nvars", type=int, help="Set the number of variables.")
    parser.add_argument("-dmd_iters", type=int, nargs='*', help="Iterations to do DMD analysis")
    parser.add_argument("-nIter", type=int, help="number of iterations for the solver")
    parser.add_argument("-preIters", type=int, help="number of pre-iterations for the solver")
    parser.add_argument("-nSnapshots", type=int, help="Number of snapshots for DMD")
    parser.add_argument("-nDMDmodes", type=int, help="Number of DMD modes to use")

    config_file_path = os.path.join(script_dir, 'config.txt')
    args_from_file = parse_config(config_file_path)
    args = parser.parse_args(args_from_file)

    NUM_SNAPS = args.nSnapshots
    NUM_DMD_MODES = args.nDMDmodes
    PRE_ITER_NUM = args.preIters
    DMD_ITER = args.dmd_iters
    POST_ITER_NUM = args.nIter
    NUM_VARS = args.nvars
    case_file_path = args.case
    cas_name = os.path.basename(case_file_path)
    outfName = cas_name.replace(".cas.h5", "") + 'DMDi' + str(DMD_ITER[0]) + '_s' + str(NUM_SNAPS) + '_m' + str(NUM_DMD_MODES)

    return NUM_SNAPS, NUM_DMD_MODES, PRE_ITER_NUM, DMD_ITER, POST_ITER_NUM, NUM_VARS, case_file_path, outfName
