import random
from copy import deepcopy
from truss import Truss


class Genome:
    class GeneticNode:
        def __init__(
            self,
            x,
            y,
            support_type=Truss.Node.SupportTypes.NONE,
            applied_force=Truss.Node.Force(0, 0),
            mutable_position=False,
            mutable_existance=False,
        ):
            self.position_is_mutable = mutable_position
            self.existance_is_mutable = mutable_existance

            self.node = Truss.Node(x, y, support_type, applied_force)

        def set_pos(self, x, y):
            if not self.position_is_mutable:
                raise Exception("Node does not have mutable position.")

            self.node.x = x
            self.node.y = y

        def randomize_position(self):
            self.set_pos(20 * (random.random() - 0.5), 20 * (random.random() - 0.5))

    class GeneticMember:
        def __init__(
            self,
            parent_genetic_node,
            child_genetic_node,
            mutable_child=False,
        ):
            self.child_is_mutable = mutable_child

            self.parent_genetic_node = parent_genetic_node
            self.child_genetic_node = child_genetic_node

            self.member = Truss.Member(
                self.parent_genetic_node.node, self.child_genetic_node.node
            )

        def change_child_node(self, new_child_genetic_node):
            self.child_genetic_node = new_child_genetic_node
            self.member.connected_node_b = new_child_genetic_node.node

    def __init__(self):
        self.nodes = [
            # Road trusses
            self.GeneticNode(
                -7,
                0,
                support_type=Truss.Node.SupportTypes.FIXED,
                applied_force=Truss.Node.Force(0, -8750 / 2),
            ),
            self.GeneticNode(-3.5, 0, applied_force=Truss.Node.Force(0, -17500 / 2)),
            self.GeneticNode(0, 0, applied_force=Truss.Node.Force(0, -17500 / 2)),
            self.GeneticNode(3.5, 0, applied_force=Truss.Node.Force(0, -17500 / 2)),
            self.GeneticNode(
                7.0,
                0,
                support_type=Truss.Node.SupportTypes.ROLLER_HORIZONTAL,
                applied_force=Truss.Node.Force(0, -8750 / 2),
            ),
            # Supporting Trusses to make simple truss
            self.GeneticNode(0, 0, mutable_position=True),
            self.GeneticNode(0, 0, mutable_position=True),
            self.GeneticNode(0, 0, mutable_position=True),
            self.GeneticNode(0, 0, mutable_position=True),
        ]

        self.members = [
            # Pavement members
            self.GeneticMember(self.nodes[0], self.nodes[1]),
            self.GeneticMember(self.nodes[1], self.nodes[2]),
            self.GeneticMember(self.nodes[2], self.nodes[3]),
            self.GeneticMember(self.nodes[3], self.nodes[4]),
            # Supporting members to make simple truss
            self.GeneticMember(self.nodes[5], self.nodes[0]),
            self.GeneticMember(self.nodes[5], self.nodes[1]),
            self.GeneticMember(self.nodes[5], self.nodes[6]),
            self.GeneticMember(self.nodes[6], self.nodes[1]),
            self.GeneticMember(self.nodes[6], self.nodes[2]),
            self.GeneticMember(self.nodes[6], self.nodes[7]),
            self.GeneticMember(self.nodes[7], self.nodes[2]),
            self.GeneticMember(self.nodes[7], self.nodes[3]),
            self.GeneticMember(self.nodes[7], self.nodes[8]),
            self.GeneticMember(self.nodes[8], self.nodes[3]),
            self.GeneticMember(self.nodes[8], self.nodes[4]),
        ]

        self.randomize_positions()

    def randomize_positions(self):
        for genetic_node in self.nodes:
            if genetic_node.position_is_mutable:
                genetic_node.randomize_position()

    def change_child_node(self, genetic_member):
        if not genetic_member.child_is_mutable:
            raise Exception("Member's child is not mutable.")

        possible_child_nodes = self.nodes.copy()
        try:
            possible_child_nodes.pop(
                possible_child_nodes.index(genetic_member.parent_genetic_node)
            )
        except:
            pass

        for check_member in self.members:
            if check_member.parent_genetic_node == genetic_member.parent_genetic_node:
                # Members share a parent node, cannot change connection to this node
                try:
                    possible_child_nodes.pop(
                        possible_child_nodes.index(check_member.parent_genetic_node)
                    )
                except:
                    pass

        genetic_member.change_child_node(random.choice(possible_child_nodes))

    def create_mutation(
        self,
        position_mutation_chance=0.01,
        position_mutation_rate=0.1,
        new_node_chance=0.01,
        remove_node_chance=0.01,
        change_member_connection_chance=0.01,
    ):
        mutated_genome = deepcopy(self)

        if random.random() <= new_node_chance:
            child_node_a, child_node_b = random.sample(mutated_genome.nodes, k=2)
            
            new_node = self.GeneticNode(
                0, 0, mutable_position=True, mutable_existance=True
            )
            new_node.randomize_position()
            
            mutated_genome.nodes.append(new_node)
            
            mutated_genome.members.append(
                self.GeneticMember(
                    new_node,
                    child_node_a,
                    mutable_child=True,
                )
            )
            mutated_genome.members.append(
                self.GeneticMember(
                    new_node,
                    child_node_b,
                    mutable_child=True,
                )
            )

        for genetic_node in mutated_genome.nodes:
            # Changing position of a node
            if (
                genetic_node.position_is_mutable
                and random.random() <= position_mutation_chance
            ):
                genetic_node.set_pos(
                    random.normalvariate(genetic_node.node.x, position_mutation_rate),
                    random.normalvariate(genetic_node.node.y, position_mutation_rate),
                )

            # Node deleted
            if (
                genetic_node.existance_is_mutable
                and random.random() <= remove_node_chance
            ):
                mutated_genome.nodes.pop(mutated_genome.nodes.index(genetic_node))
                for member_index, mem in reversed(list(enumerate(mutated_genome.members))):
                    genetic_member = mutated_genome.members[member_index]

                    if genetic_member.child_genetic_node is genetic_node:
                        mutated_genome.change_child_node(genetic_member)

                    if genetic_member.parent_genetic_node is genetic_node:
                        mutated_genome.members.pop(member_index)

        # Change member connection
        for genetic_member in mutated_genome.members:
            if (
                genetic_member.child_is_mutable
                and random.random() <= change_member_connection_chance
            ):
                mutated_genome.change_child_node(genetic_member)

        return mutated_genome

    def to_truss(self):
        return Truss(
            [genetic_node.node for genetic_node in self.nodes],
            [genetic_member.member for genetic_member in self.members],
        )

    def get_fitness(self):
        return self.to_truss().get_fitness_cost()

    def get_fitness_gentle(self):
        try:
            return self.get_fitness()
        except:
            return 999999999999
        
    def get_assignment_fitness(self):
        return self.to_truss().get_assignment_cost()
    
    def get_assignment_fitness_gentle(self):
        try:
            return self.get_assignment_fitness()
        except:
            return 999999999999
