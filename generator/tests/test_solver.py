import random
import unittest

from generator import generator
from generator.tests.helper_solver_dispatcher import SolverDispatcherHelper


class SolverTestCase(SolverDispatcherHelper):
    def test_keep_order_without_cycle(self):
        """
        Testing if solver keeps the package order if n is 1.
        """
        config_dict = generator._load_config(
            '../../config/problems/predator-prey.yaml',
            '../../config/methods/euler.yaml'
        )

        self.run_solver(config_dict, [
            {
                'id': i,
                'x_start': 0,
                'y_start': [2, 1],
                'h': 1,
                'n': 1
            } for i in range(1, 101)
        ], [
            {
                'id': i,
                'x': 1,
            } for i in range(1, 101)
        ], wr_pattern=[10, 5], rd_pattern=[100, 1])

    def test_keep_order_with_cycle(self):
        """
        Testing if solver keeps the package order if n is 10.
        """
        config_dict = generator._load_config(
            '../../config/problems/predator-prey.yaml',
            '../../config/methods/euler.yaml'
        )

        self.run_solver(config_dict, [
            {
                'id': i,
                'x_start': 0,
                'y_start': [2, 1],
                'h': 0.1,
                'n': 10
            } for i in range(1, 101)
        ], [
            {
                'id': i,
                'x': 1,
            } for i in range(1, 101)
        ], wr_pattern=[10, 5], rd_pattern=[100, 1])

    def test_keep_order_with_increasing_n(self):
        """
        Testing if solver keeps the package order if n is only increasing.
        """
        config_dict = generator._load_config(
            '../../config/problems/predator-prey.yaml',
            '../../config/methods/euler.yaml'
        )

        self.run_solver(config_dict, [
            {
                'id': i,
                'x_start': 0,
                'y_start': [2, 1],
                'h': 0.1,
                'n': i
            } for i in range(1, 101)
        ], [
            {
                'id': i,
                'x': i * 0.1,
            } for i in range(1, 101)
        ], wr_pattern=[10, 5], rd_pattern=[100, 1])

    def test_receiving_all_with_decreasing_n(self):
        """
        Testing if all packages are received with decreasing n.
        """
        config_dict = generator._load_config(
            '../../config/problems/predator-prey.yaml',
            '../../config/methods/euler.yaml'
        )

        self.run_solver(config_dict, [
            {
                'id': i,
                'x_start': 0,
                'y_start': [2, 1],
                'h': 0.1,
                'n': 101 - i
            } for i in range(1, 101)
        ], {
            i: ({
                'id': i,
                'x': (101 - i) * 0.1,
            }) for i in range(1, 101)
        }, wr_pattern=[10, 5], rd_pattern=[100, 1])

    def test_receiving_all_with_shuffled_input(self):
        """
        Testing if all packages are received with an shuffled input (different n per input).
        """
        config_dict = generator._load_config(
            '../../config/problems/predator-prey.yaml',
            '../../config/methods/euler.yaml'
        )

        input_data = [
            {
                'id': i,
                'x_start': 0,
                'y_start': [2, 1],
                'h': 0.1,
                'n': 101 - i
            } for i in range(1, 101)
        ]
        random.shuffle(input_data)

        self.run_solver(config_dict, input_data, {
            i: ({
                'id': i,
                'x': (101 - i) * 0.1,
            }) for i in range(1, 101)
        }, wr_pattern=[10, 5], rd_pattern=[100, 1])

    def test_keep_order_with_permanent_read(self):
        """
        Testing if solver keeps the package order if read of out fifo is permanently true.
        """
        config_dict = generator._load_config(
            '../../config/problems/predator-prey.yaml',
            '../../config/methods/euler.yaml'
        )

        self.run_solver(config_dict, [
            {
                'id': i,
                'x_start': 0,
                'y_start': [2, 1],
                'h': 0.1,
                'n': 10
            } for i in range(1, 101)
        ], [
            {
                'id': i,
                'x': 1,
            } for i in range(1, 101)
        ], wr_pattern=[10, 5], rd_pattern=[0, 10])


if __name__ == '__main__':
    unittest.main()
