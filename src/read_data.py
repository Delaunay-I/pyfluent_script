import numpy as np
import pandas as pd
from dmd import DMD


NUM_SNAPS = 100
NUM_DMD_MODES = 95
DT=1

# data = np.empty((21708480, NUM_SNAPS))
# for col in range(1, NUM_SNAPS + 1):
#     colVec = np.loadtxt("solver_data/largeProblem/solution_data-" + str(col) + ".dat").flatten('F')
#     # data = colVec if data is None else np.concatenate((data, colVec), axis=1)
#     data[:, col - 1] = colVec
#     print(data.shape)

data = pd.DataFrame()
for col in range(1, NUM_SNAPS + 1):
    file_path = "solver_data/largeProblem/solution_data-" + str(col) + ".dat"
    col_df = pd.read_csv(file_path, sep='\t', header=None)
    col_df = col_df.stack().reset_index(drop=True)
    data[col] = col_df  # Add the column to the DataFrame
    print(data.shape)

# Convert the DataFrame to a NumPy array
data_array = data.to_numpy()


my_dmd = DMD(data_array, 6, NUM_DMD_MODES, verbose=2)
my_dmd.calc_DMD()
my_dmd.calc_DMD_modes(DT)
my_dmd.write_modes_to_file()