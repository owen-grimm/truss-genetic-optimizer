import math
import numpy as np
from enum import Enum


class Truss:
    class Node:
        class SupportTypes(Enum):
            NONE = 0
            FIXED = 1
            ROLLER_HORIZONTAL = 2
            ROLLER_VERTICAL = 3

            @classmethod
            def get_reaction_component_count(cls, support_type):
                if support_type not in cls:
                    raise ValueError(f"Invalid support type {support_type}.")

                match support_type:
                    case cls.NONE:
                        return 0
                    case cls.FIXED:
                        return 2
                    case cls.ROLLER_HORIZONTAL:
                        return 1
                    case cls.ROLLER_VERTICAL:
                        return 1

        class Force:
            def __init__(self, magnitude_x, magnitude_y):
                self.magnitude_x = magnitude_x
                self.magnitude_y = magnitude_y

        # Cost of a single gusset plate, $
        __node_cost = 5.00

        def __init__(
            self, x, y, support_type=SupportTypes.NONE, applied_force=Force(0, 0)
        ):
            if support_type not in self.SupportTypes:
                raise ValueError(
                    f"Invalid support type {support_type}. Valid support types are provided by the Truss.Node.SupportTypes enum."
                )

            self.x = x
            self.y = y
            self.support_type = support_type
            self.applied_force = applied_force

        def get_reaction_component_count(self):
            return self.SupportTypes.get_reaction_component_count(self.support_type)

        def cost(self):
            return self.__node_cost

        def get_fitness_cost(self):
            return self.cost()

    class Member:
        class DistributedForce:
            def __init__(self, mag_per_dist_x, mag_per_dist_y):
                self.mag_per_dist_x = mag_per_dist_x
                self.mag_per_dist_y = mag_per_dist_y

        # Cost of a member, $/m
        __cost_per_length = 15.00
        # Maximum allowable internal forces, N
        __max_tensile_force = 9000
        __max_compressive_force = 6000

        def __init__(self, connected_node_a, connected_node_b, distributed_force=DistributedForce(0, 0)):
            self.connected_node_a = connected_node_a
            self.connected_node_b = connected_node_b
            self.distributed_force = distributed_force

        def length(self):
            """Returns length of member."""
            return math.sqrt(
                (self.connected_node_a.x - self.connected_node_b.x) ** 2
                + (self.connected_node_a.y - self.connected_node_b.y) ** 2
            )

        def cost(self):
            return self.__cost_per_length * self.length()

        def get_fitness_cost(self, internal_force):
            if internal_force < 0:
                # Member under compression
                beams_needed = max(1, -internal_force / self.__max_compressive_force)
            else:
                # Member under tension or has no internal forces
                beams_needed = max(1, internal_force / self.__max_tensile_force)

            if beams_needed > 3:
                return 999999999
            if self.length() < 1:
                return 999999999

            return self.cost() * beams_needed
        
        def get_assignment_cost(self, internal_force):
            if internal_force < 0:
                # Member under compression
                beams_needed = -internal_force / self.__max_compressive_force
            else:
                # Member under tension or has no internal forces
                beams_needed = internal_force / self.__max_tensile_force

            if beams_needed > 3:
                return 999999999
            if self.length() < 1:
                return 999999999

            return self.cost() * math.ceil(beams_needed)

    def __init__(self, nodes, members):
        self.nodes = nodes
        self.members = members

    def cost(self):
        node_cost = sum(node.cost() for node in self.nodes)
        member_cost = sum(member.cost() for member in self.members)
        return node_cost + member_cost

    def meets_constraints(self):
        pass

    def solve(self):
        node_index_dict = {node: ind for ind, node in enumerate(self.nodes)}

        reaction_force_component_count = sum(
            node.get_reaction_component_count() for node in self.nodes
        )

        # It is possible at this point that the system cannot be solved (not enough supports, not a simple truss, etc.)
        if len(self.members) + reaction_force_component_count > len(self.nodes) * 2:
            raise ValueError("Underconstrained system. Cannot solve truss.")

        force_coefficient_matrix = np.zeros(
            dtype=np.float64,
            shape=(
                len(self.members) + reaction_force_component_count,
                len(self.nodes) * 2,
            ),
        )

        resultant_force_vector = np.zeros(dtype=np.float64, shape=(len(self.nodes) * 2))
        reaction_force_component_index = 0

        # Dealing with distributed forces on members
        for member in self.members:
            node_a_offset_ind = 2*node_index_dict[member.connected_node_a]
            node_b_offset_ind = 2*node_index_dict[member.connected_node_b]

            member_delta_x = abs(member.connected_node_a.x - member.connected_node_b.x)
            member_delta_y = abs(member.connected_node_a.y - member.connected_node_b.y)

            force_x_per_joint = member.distributed_force.mag_per_dist_x * (member_delta_y) / 2
            force_y_per_joint = member.distributed_force.mag_per_dist_y * (member_delta_x) / 2

            resultant_force_vector[node_a_offset_ind+0] -= force_x_per_joint
            resultant_force_vector[node_a_offset_ind+1] -= force_y_per_joint
            resultant_force_vector[node_b_offset_ind+0] -= force_x_per_joint
            resultant_force_vector[node_b_offset_ind+1] -= force_y_per_joint

        for node_index, node in enumerate(self.nodes):
            offset_node_index = 2 * node_index

            for member_index, member in enumerate(self.members):
                if member.connected_node_a is node:
                    other_node = member.connected_node_b
                elif member.connected_node_b is node:
                    other_node = member.connected_node_a
                else:
                    continue

                member_length = member.length()
                member_cos = (other_node.x - node.x) / member_length
                member_sin = (other_node.y - node.y) / member_length

                force_coefficient_matrix[offset_node_index, member_index] = member_cos
                force_coefficient_matrix[offset_node_index+1, member_index] = member_sin

            # Dealing with support reactions, we don't need to know which one is which so no need to keep track
            match node.support_type:
                case Truss.Node.SupportTypes.NONE:
                    pass
                case Truss.Node.SupportTypes.FIXED:
                    force_coefficient_matrix[
                        offset_node_index,
                        len(self.members) + reaction_force_component_index,
                    ] = 1
                    force_coefficient_matrix[
                        offset_node_index + 1,
                        len(self.members) + reaction_force_component_index + 1,
                    ] = 1
                case Truss.Node.SupportTypes.ROLLER_HORIZONTAL:
                    # Applies only a force on the vertical axis
                    force_coefficient_matrix[
                        offset_node_index + 1,
                        len(self.members) + reaction_force_component_index,
                    ] = 1
                case Truss.Node.SupportTypes.ROLLER_VERTICAL:
                    # Applies only a force on the horizontal axis
                    force_coefficient_matrix[
                        offset_node_index,
                        len(self.members) + reaction_force_component_index,
                    ] = 1

            reaction_force_component_index += node.get_reaction_component_count()

            # Dealing with applied forces
            resultant_force_vector[offset_node_index] -= node.applied_force.magnitude_x
            resultant_force_vector[offset_node_index+1] -= node.applied_force.magnitude_y

        try:
            inv_force_matrix = np.linalg.inv(force_coefficient_matrix)

            # By removing the last {reaction_force_component_count} rows
            # We avoid calculating the unused reaction forces

            inv_force_matrix = inv_force_matrix[:-3]

            return inv_force_matrix @ resultant_force_vector
        except np.linalg.LinAlgError as e:
            print(
                "Unable to solve system, over/underconstrained. Numpy error follows: "
            )
            raise e

    def get_fitness_cost(self):
        cost = 0

        sol = self.solve()
        for member_index, member in enumerate(self.members):
            cost += member.get_fitness_cost(sol[member_index])

        for node in self.nodes:
            cost += node.get_fitness_cost()

        return cost
    
    def get_assignment_cost(self):
        cost = 0

        sol = self.solve()
        for member_index, member in enumerate(self.members):
            cost += member.get_assignment_cost(sol[member_index])

        for node in self.nodes:
            cost += node.cost()

        return cost

    def __repr__(self):
        node_indices = {node: i for i, node in enumerate(self.nodes)}

        node_str = [str(node.x) + " " + str(node.y) for node in self.nodes]
        node_str = "\n".join(node_str)

        member_str = [(node_indices[m.connected_node_a], node_indices[m.connected_node_b]) for m in self.members]
        member_str = "\n".join(str(member_endpoints) for member_endpoints in member_str)

        return node_str + "\n" + member_str
