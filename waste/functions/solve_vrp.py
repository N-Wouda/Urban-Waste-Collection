from pyvrp import (
    GeneticAlgorithm,
    Individual,
    PenaltyManager,
    Population,
    ProblemData,
    Result,
    XorShift128,
)
from pyvrp.crossover import selective_route_exchange as srex
from pyvrp.diversity import broken_pairs_distance as bpd
from pyvrp.educate import (
    NODE_OPERATORS,
    ROUTE_OPERATORS,
    LocalSearch,
    compute_neighbours,
)
from pyvrp.stop import StoppingCriterion


def solve_vrp(
    data: ProblemData, stop: StoppingCriterion, seed: int = 42
) -> Result:
    rng = XorShift128(seed=seed)
    pen_manager = PenaltyManager()
    pop = Population(bpd)

    neighbours = compute_neighbours(data)
    ls = LocalSearch(data, rng, neighbours)

    for op in NODE_OPERATORS:
        ls.add_node_operator(op(data))

    for op in ROUTE_OPERATORS:
        ls.add_route_operator(op(data))

    init = [Individual.make_random(data, rng) for _ in range(25)]
    algo = GeneticAlgorithm(data, pen_manager, rng, pop, ls, srex, init)

    return algo.run(stop)
