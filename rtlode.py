#!/usr/bin/env python3

import argparse
import sys

import json


class RtlOde(object):

    def __init__(self):
        parser = argparse.ArgumentParser(
            description='Used to generate and run ode solver logic on FPGAs.',
            usage='''rtlode <command> [<args>]

The most commonly used git commands are:
   build       Generate a solver for a given configuration
   run         Solve a single initial value problem in a given solver
   benchmark   Bechmark a given solver
''')
        parser.add_argument('command', help='Subcommand to run')
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print('Unrecognized command')
            parser.print_help()
            exit(1)
        getattr(self, args.command)()

    def build(self):
        parser = argparse.ArgumentParser(description='Generate a solver for a given configuration')

        parser.add_argument('configuration', nargs='+',
                            help='configuration files for the solver')

        args = parser.parse_args(sys.argv[2:])
        import generator
        generator.build(*args.configuration)

    def run(self):
        parser = argparse.ArgumentParser(
            description='Solve a the given number (default: 0) of initial value problems in a given solver'
        )

        parser.add_argument('solver', help='solver file to execute')
        parser.add_argument('--runtime_config', help='overwrites the default config, must be an json string')
        parser.add_argument('--amount', type=int, help='number of initial value problems to solve', default=0)
        args = parser.parse_args(sys.argv[2:])

        from runtime import runtime
        res = runtime.run(
            args.solver,
            json.loads(args.runtime_config) if args.runtime_config is not None else None,
            amount_data=args.amount
        )
        print('Result:\n%r' % json.dumps(res, sort_keys=True, indent=4))

    def benchmark(self):
        parser = argparse.ArgumentParser(description='Benchmark a given solver')

        parser.add_argument('solver', help='solver file to execute')
        parser.add_argument('--runtime_config', help='overwrites the default config, must be an json string')
        args = parser.parse_args(sys.argv[2:])

        from runtime import runtime
        for adata in [1, 10, 100, 1000, 10000]:
            timing = runtime.benchmark(
                args.solver,
                json.loads(args.runtime_config) if args.runtime_config is not None else None,
                amount_data=adata
            )
            print('For %s ivp the solver finished in: %s' % (adata, timing))


if __name__ == '__main__':
    RtlOde()
