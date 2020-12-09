# Generator Configuration

In the following all possible options are listed with their default values.
Of course the different configuration values can be splitted over multiple files.
And so allowing the reuse of some parts, as example the definition of a solver method.
Some of these reusable configurations are available in the subdirectories of this
directory.

Some information regarding the initial value problem to be solved are only necessary
at runtime. If the options are provided at generation time, then these values are
written in the resulting .slv file as defaults for the runtime. 

```yaml
# Specifies the amount of parallel solvers to be generated.
nbr_solver: 1

# Internal numeric value representation
numeric:
    type: 'fixed'  # or 'floating'
    # Fixed point parameters, will be ignored if type != 'fixed'
    fixed_point_signed: True # Currently only signed supported
    fixed_point_fraction_size: 37
    fixed_point_nonfraction_size : 16
    # Floating point parameters, will be ignored if type != 'floating'
    floating_precision: 'double' # or 'single'

# Definition of runge kutta method to be used.
method:
  A: [[],
      [0.5],
      [0, 0.5],
      [0, 0, 1]]
  b: [0.1666666667, 0.3333333334, 0.3333333334, 0.1666666667]
  c: [0, 0.5, 0.5, 1]

# Specifies the initial value problem to be solved
problem:
    x: 0  # Only needed at runtime
    y:  # Only needed at runtime
      - 2
      - 1
    h: 0.17  # Only needed at runtime
    n: 60  # Only needed at runtime
    components:
      - 0.1 * y[0] - 0.2 * y[0] * y[1]
      - -0.2 * y[1] + 0.4 * y[0] * y[1]
```