if __name__ == "__main__":
    from preset import *
    from solver.solver import *
    from time import time

    start = time()
    results = minimum_steps_bfs(board_6_3)
    print("minimum_steps_bfs:", results, "Time spent:", time()-start)

    start = time()
    results = minimum_steps_dfs(board_6_3)
    print("minimum_steps_dfs:", results, "Time spent:", time()-start)
    