using QuantumCollocation

T = 50
dt = 0.2

system = QuantumSystem([PAULIS[:X], PAULIS[:Y]])
prob = UnitarySmoothPulseProblem(system, GATES[:H], T, dt)
solve!(prob, max_iter=100)

plot = plot_unitary_populations(prob)
display(plot)
