import numpy as np
import random
import tkinter as tk
import pickle
import time

from truss import Truss
from genetics import Genome
from joblib import Parallel, delayed
from pathlib import Path


def map(x, old_min, old_max, new_min, new_max):
    return ((x - old_min) / (old_max - old_min)) * (new_max - new_min) + new_min

node_radius = 5
member_thickness = 2.5

def draw(truss: Truss, x, y, width, height):
    min_x = min(n.x for n in truss.nodes)
    max_x = max(n.x for n in truss.nodes)
    min_y = min(n.y for n in truss.nodes)
    max_y = max(n.y for n in truss.nodes)

    # Dealing with aspect ratio scaling
    if max_x - min_x >= max_y - min_y:
        output_x_min = x
        output_x_max = x + width
        output_y_span = height * (max_y - min_y) / (max_x - min_x)
        output_y_min = y + (height - output_y_span) / 2
        output_y_max = y + height - (height - output_y_span) / 2
    else:
        output_y_min = y
        output_y_max = y + height
        output_x_span = width * (max_x - min_x) / (max_y - min_y)
        output_x_min = x + (width - output_x_span) / 2
        output_x_max = x + width - (width - output_x_span) / 2

    # Flipping y-coords because of screen-space coordiante disagreement
    output_y_min, output_y_max = output_y_max, output_y_min

    # Drawing nodes
    for node in truss.nodes:
        mapped_x = map(node.x, min_x, max_x, output_x_min, output_x_max)
        mapped_y = map(node.y, min_y, max_y, output_y_min, output_y_max)

        canvas.create_oval(
            mapped_x - node_radius,
            mapped_y - node_radius,
            mapped_x + node_radius,
            mapped_y + node_radius,
        )

    # Drawing members
    for member in truss.members:
        mapped_a_x = map(member.connected_node_a.x, min_x, max_x, output_x_min, output_x_max)
        mapped_a_y = map(member.connected_node_a.y, min_y, max_y, output_y_min, output_y_max)
        mapped_b_x = map(member.connected_node_b.x, min_x, max_x, output_x_min, output_x_max)
        mapped_b_y = map(member.connected_node_b.y, min_y, max_y, output_y_min, output_y_max)

        canvas.create_line(mapped_a_x, mapped_a_y, mapped_b_x, mapped_b_y)


canvas_width = 800
canvas_height = 800

root = tk.Tk()
root.geometry(f"{canvas_width}x{canvas_height}")
root.title("Truss Optimizer 9001")

canvas = tk.Canvas(root, width=canvas_width, height=canvas_height, bg="white")
canvas.pack(anchor=tk.CENTER, expand=True)

canvas_truss_rows = 10
canvas_truss_cols = 10

# margin between truss visuals, px
cell_margins = 20

# creating truss_checkpoints folder
Path("truss_checkpoints").mkdir(parents=True, exist_ok=True)

# evolution parameters
batch_size = 100
cut_limit = batch_size // 2

selection_weights_array = [(batch_size - i - 1) ** 2 for i in range(batch_size)]

pool = [Genome() for __ in range(batch_size)]
print("Generating starting pool")
for __ in range(10):
    pool = [g.create_mutation(position_mutation_chance=0.5,
                position_mutation_rate=0.1,
                new_node_chance=0.25,
                remove_node_chance=0.1,
                change_member_connection_chance=0,
            ) for g in pool]

initial_rate = 0.5
last_fitness = pool[0].to_truss().get_assignment_cost()

while True:
    root.update_idletasks()
    root.update()
    canvas.delete("all")

    fitnesses = Parallel(n_jobs=15)(delayed(Genome.get_assignment_fitness_gentle)(g) for g in pool)
    
    pool_fitnesses = zip(fitnesses, pool)
    pool_fitnesses = sorted(pool_fitnesses, key=lambda x: x[0])

    cur_fitness = pool_fitnesses[0][0]

    fitnesses, pool = zip(*pool_fitnesses)
    pool = list(pool)

    rate = 0.5

    print(f"fit: {cur_fitness}, rate:{rate}")
    try:
        with open("truss_checkpoints/" + str(time.time()) + " " + str(cur_fitness) + ".truss", 'wb+') as f:
            pickle.dump(pool[0], f)
    except:
        print("Could not write truss checkpoint. Check directory permissions.")

    # Drawing trusses
    for r in range(canvas_truss_rows):
        for c in range(canvas_truss_cols):
            w = (canvas_width - (canvas_truss_cols + 1) * cell_margins) / canvas_truss_cols
            h = (canvas_width - (canvas_truss_rows + 1) * cell_margins) / canvas_truss_cols
            x = cell_margins + c * (w + cell_margins)
            y = cell_margins + r * (h + cell_margins)
            draw(pool[c + r * canvas_truss_cols].to_truss(), x, y, w, h)

    selection = random.sample(pool, k=cut_limit, counts=selection_weights_array)
    pool[:cut_limit] = selection

    pool[cut_limit:] = Parallel(n_jobs=15)(delayed(Genome.create_mutation)(
            g,
            position_mutation_chance=0.5,
            position_mutation_rate=0.1,
            new_node_chance=0.25,
            remove_node_chance=0.1,
            change_member_connection_chance=0,
        )
    for g in pool[:cut_limit])

    last_fitness = cur_fitness
