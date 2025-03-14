# !pip install jl2py

# import jl2py

import numpy as np

from pypiccolo import PAULIS
from pypiccolo import GATES
from pypiccolo.problemtemplates import QuantumStateSmoothPulseProblem, UnitarySmoothPulseProblem, UnitaryMinimumTimeProblem
from pypiccolo.quantumcollocation import QuantumSystem
from pypiccolo.quantumcollocation import unitary_rollout_fidelity, plot_unitary_populations, traj_to_mat

system = QuantumSystem(h_drives=[PAULIS['X'], PAULIS['Y']])
problem = UnitarySmoothPulseProblem(system, GATES['H'], 50, 0.2)

fidelity_initial = unitary_rollout_fidelity(problem, system)
problem.solve(50)
fidelity_final = unitary_rollout_fidelity(problem, system)

assert fidelity_final > fidelity_initial
print(f'unitary_fidelity=(before={fidelity_initial},after={fidelity_final})')

mat = traj_to_mat(problem.value.trajectory)

# ideally in a jupyter notebook we get this to show up, probably just simpler via matplotlib
plot_unitary_populations(problem)
