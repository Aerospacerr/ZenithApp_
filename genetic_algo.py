import random
import math

# Genetic Algorithm Configuration
POPULATION_SIZE = 100
GENERATIONS = 100
TOURNAMENT_SIZE = 5
CROSSOVER_RATE = 0.8
MUTATION_RATE = 0.2
MIN_PORTION = 0  # grams
MAX_PORTION = 300  # grams


class GeneticAlgorithm:
    def __init__(self, food_items, target_nutrients):
        self.food_items = food_items
        self.target_nutrients = target_nutrients

    def initialize_population(self):
        population = []
        for _ in range(POPULATION_SIZE):
            chromosome = []
            for food in self.food_items:
                if food["unit_category"] == "Base Units":
                    qty = random.uniform(1, 300)  # Quantities for Base Units
                else:
                    qty = random.randint(1, 20)  # Integer quantities for other units
                chromosome.append(qty)
            population.append(chromosome)
        return population

    def fitness(self, chromosome):
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fats = 0
        for gene, food in zip(chromosome, self.food_items):
            if food["unit_category"] == "Base Units":
                factor = gene / food["quantity"]  # Use actual quantity from data
            else:
                factor = gene  # For non-base units, gene itself is the multiplier

            total_calories += food["calories"] * factor
            total_protein += food["protein"] * factor
            total_carbs += food["carbs"] * factor
            total_fats += food["fats"] * factor
        # Calculate squared deviations
        calorie_dev = (total_calories - self.target_nutrients["calories"]) ** 2
        protein_dev = (total_protein - self.target_nutrients["protein"]) ** 2
        carbs_dev = (total_carbs - self.target_nutrients["carbs"]) ** 2
        fats_dev = (total_fats - self.target_nutrients["fats"]) ** 2
        # Sum of squared deviations
        total_deviation = calorie_dev + protein_dev + carbs_dev + fats_dev
        return math.sqrt(total_deviation)  # Lower is better

    def tournament_selection(self, population, scores):
        selected = []
        for _ in range(POPULATION_SIZE):
            tournament = random.sample(list(zip(population, scores)), TOURNAMENT_SIZE)
            tournament.sort(key=lambda x: x[1])  # Sort by fitness (lower is better)
            selected.append(tournament[0][0])
        return selected

    def crossover(self, parent1, parent2):
        if random.random() < CROSSOVER_RATE:
            point = random.randint(1, len(parent1) - 1)
            child1 = parent1[:point] + parent2[point:]
            child2 = parent2[:point] + parent1[point:]
            return child1, child2
        else:
            return parent1.copy(), parent2.copy()

    def mutate(self, chromosome):
        for i in range(len(chromosome)):
            if random.random() < MUTATION_RATE:
                mutation_factor = random.uniform(0.98, 1.02)
                if self.food_items[i]["unit_category"] == "Base Units":
                    new_qty = chromosome[i] * mutation_factor
                    new_qty = max(MIN_PORTION, min(new_qty, MAX_PORTION))
                else:
                    new_qty = chromosome[i] + random.choice(
                        [-1, 1]
                    )  # Mutate by adding or subtracting 1
                    new_qty = max(
                        1, min(new_qty, 20)
                    )  # Keep within reasonable range for non-base units
                chromosome[i] = new_qty
        return chromosome

    def run(self):
        population = self.initialize_population()
        for generation in range(GENERATIONS):
            scores = [self.fitness(chrom) for chrom in population]
            selected = self.tournament_selection(population, scores)
            next_generation = []
            for i in range(0, POPULATION_SIZE, 2):
                parent1 = selected[i]
                parent2 = selected[i + 1] if i + 1 < POPULATION_SIZE else selected[0]
                child1, child2 = self.crossover(parent1, parent2)
                next_generation.extend([self.mutate(child1), self.mutate(child2)])
            population = next_generation[:POPULATION_SIZE]
            if (generation + 1) % 10 == 0 or generation == 0:
                best_score = min(scores)
                avg_score = sum(scores) / len(scores)
                # print(
                #     f"Generation {generation+1}: Best Fitness = {best_score:.4f}, Avg Fitness = {avg_score:.4f}"
                # )
        final_scores = [self.fitness(chrom) for chrom in population]
        best_index = final_scores.index(min(final_scores))
        best_chromosome = population[best_index]
        return best_chromosome, final_scores[best_index]

    def calculate_nutrients(self, chromosome):
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fats = 0
        for gene, food in zip(chromosome, self.food_items):
            if food["unit_category"] == "Base Units":
                factor = gene / food["quantity"]  # Use actual quantity from data
            else:
                factor = gene  # For non-base units, gene itself is the multiplier

            total_calories += food["calories"] * factor
            total_protein += food["protein"] * factor
            total_carbs += food["carbs"] * factor
            total_fats += food["fats"] * factor
        return total_calories, total_protein, total_carbs, total_fats
