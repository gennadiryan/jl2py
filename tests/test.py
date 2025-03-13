# !pip install jl2py

# import jl2py

import numpy as np

from jl2py.quantumcollocationpy import PAULIS
from jl2py.quantumcollocationpy import GATES
from jl2py.quantumcollocationpy.quantumcollocation import QuantumSystem
from jl2py.quantumcollocationpy.problemtemplates import UnitarySmoothPulseProblem
from jl2py.quantumcollocationpy.problemtemplates import UnitaryMinimumTimeProblem
from jl2py.quantumcollocationpy.quantumcollocation import unitary_fidelity
from jl2py.quantumcollocationpy.quantumcollocation import plot_unitary_populations
from jl2py.quantumcollocationpy.quantumcollocation import traj_to_mat

system = QuantumSystem(h_drives=[PAULIS['X'], PAULIS['Y']])
problem = UnitarySmoothPulseProblem(system, GATES['H'], 50, 0.2)

fidelity_initial = unitary_fidelity(problem)
problem.solve(50)
fidelity_final = unitary_fidelity(problem)

assert fidelity_final > fidelity_initial
print(f'unitary_fidelity=(before={fidelity_initial},after={fidelity_final})')

mat = traj_to_mat(problem.value.trajectory)

# ideally in a jupyter notebook we get this to show up, probably just simpler via matplotlib
plot_unitary_populations(problem)