import math
import random
import tkinter as tk
from tkinter import *
import numpy as np

num_cities = 25
num_roads = 100
city_scale = 5
road_width = 4
padding = 100

# ACO parameters
NUM_ANTS = 50
ALPHA = 1.0  # Pheromone importance
BETA = 2.0   # Distance importance
RHO = 0.1    # Pheromone evaporation rate
Q = 100      # Pheromone deposit factor
MAX_ITERATIONS = 100

class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def draw(self, canvas, color='black'):
        canvas.create_oval(self.x-city_scale, self.y-city_scale, self.x+city_scale, self.y+city_scale, fill=color)

class Edge:
    def __init__(self, a, b):
        self.city_a = a
        self.city_b = b
        self.length = math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)

    def draw(self, canvas, color='grey', style=(2, 4)):
        canvas.create_line(self.city_a.x,
                           self.city_a.y,
                           self.city_b.x,
                           self.city_b.y,
                           fill=color,
                           width=road_width,
                           dash=style)

class AntColonyOptimization:
    def __init__(self, cities):
        self.cities = cities
        self.num_cities = len(cities)
        self.pheromone = np.ones((self.num_cities, self.num_cities))
        self.best_path = None
        self.best_distance = float('inf')

    def distance(self, city1, city2):
        return math.sqrt((city1.x - city2.x)**2 + (city1.y - city2.y)**2)

    def run(self, ui):
        for iteration in range(MAX_ITERATIONS):
            paths = self.construct_solutions()
            self.update_pheromones(paths)
            self.update_best_solution(paths)
            if iteration % 10 == 0:
                print(f"Iteration {iteration}: Best distance = {self.best_distance}")
            ui.draw_solution(self.best_path)
            ui.update()
        return self.best_path

    def construct_solutions(self):
        paths = []
        for _ in range(NUM_ANTS):
            path = self.construct_path()
            paths.append(path)
        return paths

    def construct_path(self):
        unvisited = set(range(self.num_cities))
        start = random.choice(list(unvisited))
        path = [start]
        unvisited.remove(start)

        while unvisited:
            current = path[-1]
            next_city = self.choose_next_city(current, unvisited)
            path.append(next_city)
            unvisited.remove(next_city)

        return path

    def choose_next_city(self, current, unvisited):
        probabilities = []
        for city in unvisited:
            pheromone = self.pheromone[current][city]
            distance = self.distance(self.cities[current], self.cities[city])
            probability = (pheromone ** ALPHA) * ((1.0 / distance) ** BETA)
            probabilities.append((city, probability))

        total = sum(prob for _, prob in probabilities)
        normalized_probabilities = [(city, prob / total) for city, prob in probabilities]

        return random.choices(
            [city for city, _ in normalized_probabilities],
            weights=[prob for _, prob in normalized_probabilities]
        )[0]

    def update_pheromones(self, paths):
        self.pheromone *= (1 - RHO)
        for path in paths:
            distance = self.calculate_path_distance(path)
            for i in range(len(path)):
                j = (i + 1) % len(path)
                self.pheromone[path[i]][path[j]] += Q / distance
                self.pheromone[path[j]][path[i]] += Q / distance

    def calculate_path_distance(self, path):
        return sum(self.distance(self.cities[path[i]], self.cities[path[(i + 1) % len(path)]]) for i in range(len(path)))

    def update_best_solution(self, paths):
        for path in paths:
            distance = self.calculate_path_distance(path)
            if distance < self.best_distance:
                self.best_distance = distance
                self.best_path = path

class UI(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("Traveling Salesman")
        self.option_add("*tearOff", FALSE)
        width, height = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry("%dx%d+0+0" % (width, height))
        self.state("zoomed")
        self.canvas = Canvas(self)
        self.canvas.place(x=0, y=0, width=width, height=height)
        self.w = width-padding
        self.h = height-padding*2
        self.cities_list = []
        self.roads_list = []
        self.edge_list = []
        self.aco = None

    def add_city(self):
        x = random.randint(padding, self.w)
        y = random.randint(padding, self.h)
        node = Node(x, y)
        self.cities_list.append(node)

    def add_road(self):
        a = random.randint(0, len(self.cities_list)-1)
        b = random.randint(0, len(self.cities_list)-1)
        road = f'{min(a, b)},{max(a, b)}'
        while a == b or road in self.roads_list:
            a = random.randint(0, len(self.cities_list)-1)
            b = random.randint(0, len(self.cities_list)-1)
            road = f'{min(a, b)},{max(a, b)}'
        edge = Edge(self.cities_list[a], self.cities_list[b])
        self.roads_list.append(road)
        self.edge_list.append(edge)

    def generate_city(self):
        self.cities_list = []
        self.roads_list = []
        self.edge_list = []
        for c in range(num_cities):
            self.add_city()
        for r in range(num_roads):
            self.add_road()

    def draw_city(self):
        self.canvas.delete("all")
        for e in self.edge_list:
            e.draw(self.canvas)
        for n in self.cities_list:
            n.draw(self.canvas)

    def draw_solution(self, solution):
        self.canvas.delete("all")
        # Draw original grey roads
        for e in self.edge_list:
            e.draw(self.canvas)
        # Draw the red solution lines
        for i in range(len(solution)):
            city1 = self.cities_list[solution[i]]
            city2 = self.cities_list[solution[(i + 1) % len(solution)]]
            self.canvas.create_line(city1.x, city1.y, city2.x, city2.y, fill='red', width=2)
        # Draw the city nodes on top
        for city in self.cities_list:
            city.draw(self.canvas, 'red')

    def generate(self):
        self.generate_city()
        self.draw_city()
        self.aco = AntColonyOptimization(self.cities_list)

    def run_aco(self):
        if self.aco:
            best_solution = self.aco.run(self)
            self.draw_solution(best_solution)

    def create_menu(self):
        menu_bar = Menu(self)
        self['menu'] = menu_bar
        menu_TS = Menu(menu_bar)
        menu_bar.add_cascade(menu=menu_TS, label='Salesman', underline=0)
        menu_TS.add_command(label="Generate", command=self.generate, underline=0)
        menu_TS.add_command(label="Run ACO", command=self.run_aco, underline=0)

if __name__ == '__main__':
    ui = UI()
    ui.create_menu()
    ui.mainloop()