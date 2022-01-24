import random
import unittest

from generator import generator
from generator.tests.helper_solver_dispatcher import SolverDispatcherHelper
from utils.dict_update import deep_update


class DispatcherTestCase(SolverDispatcherHelper):
    def test_keep_order_one_solver(self):
        """
        Testing if dispatcher keeps the package order if only one solver unit is used.
        """
        config_dict = generator._load_config(
            '../../config/problems/predator-prey.yaml',
            '../../config/methods/euler.yaml'
        )
        deep_update(config_dict, {'nbr_solver': 1})

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

    def test_receiving_all_with_shuffled_input(self):
        """
        Testing if all packages are received with an shuffled input (different n per input).
        """
        config_dict = generator._load_config(
            '../../config/problems/predator-prey.yaml',
            '../../config/methods/euler.yaml'
        )
        deep_update(config_dict, {'nbr_solver': 8})

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

    def test_receiving_all_with_permanent_read(self):
        """
        Testing if all packages are received if read of out fifo is permanently true.
        """
        config_dict = generator._load_config(
            '../../config/problems/predator-prey.yaml',
            '../../config/methods/euler.yaml'
        )
        deep_update(config_dict, {'nbr_solver': 8})

        self.run_solver(config_dict, [
            {
                'id': i,
                'x_start': 0,
                'y_start': [2, 1],
                'h': 0.1,
                'n': 10
            } for i in range(1, 101)
        ], {
            i: ({
                'id': i,
                'x': 1,
            }) for i in range(1, 101)
        }, wr_pattern=[10, 5], rd_pattern=[0, 10])

    def test_output_busy(self):
        config_dict = generator._load_config(
            '../../config/problems/predator-prey.yaml',
            '../../config/methods/euler.yaml'
        )
        deep_update(config_dict, {'nbr_solver': 32})

        self.run_solver(config_dict, [
            {
                'id': i,
                'x_start': 0,
                'y_start': [2, 1],
                'h': 0.01,
                'n': 100
            } for i in range(1, 101)
        ], {
            i: ({
                'id': i,
                'x': 1,
            }) for i in range(1, 101)
        }, wr_pattern=[2, 5], rd_pattern=[100, 1])


if __name__ == '__main__':
    unittest.main()
