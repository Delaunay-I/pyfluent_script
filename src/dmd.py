import os
import numpy as np
from scipy.linalg import eigvals
import math

output_directory = 'solver_data'

# Create the output directory if it doesn't exist
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

class DMD:
    """
    A class that performs DMD analysis and use the DMD modes to compute an over-relaxation method

    Parameters
    ----------
    self.r = rank of the truncated SVD. Can be updated by refine_num_modes method

    """
    VERBOSE_NONE = 0
    VERBOSE_BASIC = 1
    VERBOSE_DETAILED = 2

    refine_on_condS = True

    counter = 0

    def __init__(self, data: np.ndarray, num_vars: int, num_dmd_modes: int, verbose=VERBOSE_BASIC) -> None:
        self.verbose = verbose

        self.data = data
        self.X = data[:, :-1]
        self.Y = data[:, 1:]

        self.r = num_dmd_modes
        assert num_vars < 10
        assert isinstance(num_vars, int)
        self.num_vars = num_vars
        self.num_cells = self.data.shape[0]//num_vars        

        self.Ur = None
        self.Sr = None
        self.Vr = None
        self.eigs = None
        self.W = None

        self.b = None

        self.Phi = None
        self.omega = None
        self.time_dynamics = None
        self.time_dynamics2 = None
        self.Atilde = None
        self.dmd_update = None

        # Vector data for ML analysis
        self.dmd_dataset = np.array([])

        DMD.counter += 1

    def log(self, message, level=VERBOSE_BASIC):
        if level <= self.verbose:
            print(message)

    def calc_DMD(self,):
        self.log('Starting DMD analysis.\nCalculating SVD...', self.VERBOSE_BASIC)

        U, S, Vstar = np.linalg.svd(self.X, full_matrices=False)
        np.savetxt("solver_data/singularvalues.csv", S)
        V = Vstar.T.conj()
        S_matrix = np.diag(S)

        while True:
            self.Ur = U[:, :self.r]
            self.Sr = S_matrix[:self.r, :self.r]
            self.Vr = V[:, :self.r]

            Sr_inv = np.linalg.inv(self.Sr)
            self.Atilde = self.Ur.T @ self.Y @ self.Vr @ Sr_inv

            new_rank = self.refine_num_modes()
            if new_rank < self.r:
                self.log(f"Reducing rank from {self.r} to {new_rank}.")
                self.r = new_rank
            else:
                break

        if (self.r < 9):
            print(f"\033[1;31mThe current machine learning model for DMD automation is not applicable to this dataset.\nNumber of modes {self.r}\033[0m")

        I = np.identity(self.r)
        Gtilde = np.linalg.inv(I - self.Atilde) @ self.Atilde
        self.dmd_update = self.Ur @ Gtilde @ (self.Ur.T @ self.Y[:, -1])

        self.log(f"cond(S): {np.linalg.cond(self.Sr):.2e}\ncond(Atilde): {np.linalg.cond(self.Atilde):.2e}\ncond(Gtilde): {np.linalg.cond(Gtilde):.2e}", self.VERBOSE_DETAILED)


        split_data = np.array_split(np.real(self.dmd_update), self.num_vars, axis=0)
        data_mat = np.column_stack(split_data)
        np.savetxt("solver_data/DMDUpdate.csv", data_mat, delimiter='\t', fmt='%s')




    def calc_DMD_modes(self, dt: int):
        end_time = dt * (self.data.shape[1] - 1)
        t = np.arange(0, end_time, dt) # shape: (r,)

        self.log("Calculating solution mode time-dynamics...", self.VERBOSE_BASIC)
        eigs, W = np.linalg.eig(self.Atilde)
        # Check the size of the eigenvectors
        assert W.shape == (self.r, self.r), "Size of eigenvectors is incorrect"

        # Sort the eigenvalues and eigenvectors
        idx = np.argsort(eigs)[::-1]
        self.eigs = eigs[idx]
        self.W = W[:, idx]
        self.eigs = self.eigs
        if np.any(self.eigs > 1):
            print("DMD calculated an unstable mode!!")

        np.savetxt("solver_data/amps.csv", self.eigs)
        # Reconstructing the high-dimensional DMD modes from the r sub-space
        self.Phi = self.Y @ self.Vr @ np.linalg.inv(self.Sr) @ self.W

        self.omega = np.log(self.eigs)/dt # shape: (r,)
        assert np.all(np.isinf(self.omega)) == False, "Omega values have inf"
        np.savetxt("solver_data/eigs.csv", self.omega)

        # Doing least-squares to find initial solution
        x1 = self.data[:, 0]
        b, res, rnk, singularvalues = np.linalg.lstsq(self.Phi, x1, rcond=None)
        self.b = b.T # shape: (r,)

        self.time_dynamics = np.empty((len(t), self.r))
        for iter in range(0, len(t)):
            self.time_dynamics[iter, :] = np.real(self.b*np.exp(self.omega*t[iter]))

        # You can play with this variable (time_multiplier) to predict further in the future
        time_multiplier = 20
        t2 = np.arange(0, time_multiplier*end_time, dt)
        self.time_dynamics2 = np.empty((len(t2), self.r))
        for iter in range(0, len(t2)):
            self.time_dynamics2[iter, :] = np.real(self.b*np.exp(self.omega*t2[iter]))

        sOutputName = 'time_dynamics.csv'
        sOutputName = os.path.join(output_directory, sOutputName)
        self.log(f"Writing the DMD time-dynamics to file {sOutputName}", self.VERBOSE_DETAILED)
        np.savetxt(sOutputName, self.time_dynamics)
        sOutputName = 'time_dynamics2.csv'
        sOutputName = os.path.join(output_directory, sOutputName)
        self.log(f"Writing the DMD time-dynamics (longer - predicted) to file {sOutputName}", self.VERBOSE_DETAILED)
        np.savetxt(sOutputName, self.time_dynamics2)


    def write_modes_to_file(self,) -> None:

        # Split the DMD-mode-vector into its corresponding variables        
        split_data = np.array_split(np.real(self.Phi[:, 0]), self.num_vars, axis=0)
        data_mat = np.column_stack(split_data)
        sOutputName = "solver_data/DMD_modes_separated.csv"
        np.savetxt(sOutputName, data_mat, delimiter='\t')
        self.log(f"dmd modes saved to file {sOutputName} successfully!!", self.VERBOSE_DETAILED)

    def refine_num_modes(self) -> int:
        if DMD.refine_on_condS:
            new_svd_rank_condS = self._refine_by_condition_number()
            if new_svd_rank_condS == self.r:
                DMD.refine_on_condS = False
            else:
                return new_svd_rank_condS

        return self._refine_by_unstable_modes()
    

    # Internal methods
    def _refine_by_condition_number(self) -> int:
        self.log("Refining the number of SVD modes (condition number check)...", self.VERBOSE_BASIC)
        condS = np.linalg.cond(self.Sr)
        print(f"cond(Sr): {condS:.2e}")
        
        OMag_condSr = np.floor(np.log10(abs(condS)))
        OMag_S_array = np.floor(np.log10(np.diag(self.Sr)))
        return np.sum(OMag_S_array - OMag_condSr > -18)

    def _refine_by_unstable_modes(self) -> int:
        self.log("Refining the number of SVD modes (unstable mode check)...", self.VERBOSE_BASIC)
        eigs = eigvals(self.Atilde)
        num_unstable_modes = np.sum(np.abs(eigs) >= 1)
        self.log(f"number of unstable modes: {num_unstable_modes}", self.VERBOSE_BASIC)
        return len(eigs) - num_unstable_modes


    def collect_ML_data(self, ):
        """
        combines the required dataset to feed to the ML pipeline of the DMD automation framework
        The data includes, in order: singular values, amplification factors, eigenvalues, DMD energies, future projections of the mode residual norms

        The model is trained on 9 modes, so we only keep 9 elements of each of these vectors
        """
        # Collecting the singular values for the ML model
        singular_values = np.diag(self.Sr[:9])
        amps = self.eigs[:9]
        eigs = self.omega[:9]
        energies = None
        mode_residual_predictions = abs(self.b*np.exp(self.omega*20))[:9]

        # computing DMD mode energies
        epsilon = np.linalg.inv(self.W) @ self.Sr @ self.Vr.conj().T
        row_norms = np.linalg.norm(epsilon, axis=1)
        energies = row_norms[:9]

        self.dmd_dataset = np.concatenate((singular_values, amps, eigs, energies, mode_residual_predictions)).real.tolist()
