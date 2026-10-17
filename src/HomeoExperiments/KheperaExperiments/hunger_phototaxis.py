'''
Hunger-driven phototaxis: the 2+2 Braitenberg vehicle of
phototaxis_braitenberg2_direct with a battery.

The robot carries a battery (KheperaSimulator.Battery) that drains at a
constant rate and recharges from the light at the robot's centre, whatever
its heading; the homeostat senses it through a Battery unit, an
interoceptive sensor (Simulator.HomeoExperiments.add_battery_to_homeostat).

Architecture
------------
    Left Sensor  ──►  Right Motor   (as phototaxis_braitenberg2_direct)
    Right Sensor ──►  Left Motor
    Battery      ──►  both motors   (small random weights, under the motors'
                                     uniselector)

With --hunger-unit, a Newtonian Hunger unit stands between the Battery and
the motors (Battery ──► Hunger ──► both motors), and its own uniselector
adjusts its inputs.

The battery breaks even 1.0 from the light (the acquisition radius): closer,
it gains charge; farther, it loses it.  What an empty battery does is the
depletion mode, death by default here: the robot stops for good and the run
ends, so a run records how long the robot survived.


Options
-------
   The options of every phototaxis experiment (phototaxis_common.COMMON_OPTIONS_HELP),
   the vehicle's (--fixed-weights, --signs, --uncrossed, --motor: see
   phototaxis_braitenberg2_direct), and the battery's:
   --depletion M        what an empty battery does: death (default: the robot
                        stops for good and the run ends), paralysis (the wheels
                        stop while it is empty), graded (the wheels slow with
                        the level) or none
   --capacity C         a full battery's charge (default 1)
   --discharge R        the charge lost per tick (default 1e-5: a full battery
                        lasts 100,000 ticks)
   --recharge F         the charge gained per tick per unit of food (default:
                        break-even 1.0 from the light)
   --food-saturation S  the most food a tick absorbs (default: the food at the
                        light's edge)
   --critical-level L   the fraction of capacity below which the battery is
                        critical (default 0.3)
   --min-efficiency E   with --depletion graded, an empty battery's wheel
                        efficiency (default 0.1)
   --battery-signal S   what the Battery unit reads: hunger (default,
                        capacity - level) or level
   --hunger-unit        a Hunger unit between the Battery and the motors
   --hunger-inputs I    the Hunger unit's inputs: battery (default) or all
   --battery-recorded   the battery does not feed the motors: it is only
                        recorded
   --stress-source S    (with --continuous) also the Hunger unit's; battery
                        makes the search grow with hunger

   Files and batches are named hunger_phototaxis_..., with the depletion
   mode and the battery's options as tags.

Usage
-----
    # The fixed-weight crossed ++ vehicle with a battery, 20 random starts
    python -m HomeoExperiments.KheperaExperiments.hunger_phototaxis --fixed-weights --random-start --batch 20

    # The OU vehicle whose search grows with hunger, with a Hunger unit
    python -m HomeoExperiments.KheperaExperiments.hunger_phototaxis --continuous --stress-source battery --hunger-unit

@author: stefano
'''

from HomeoExperiments.KheperaExperiments import phototaxis_common as common
from HomeoExperiments.KheperaExperiments import phototaxis_braitenberg2_direct as direct

EXPERIMENT = 'hunger_phototaxis'

# What an empty battery does in these experiments, unless asked otherwise
DEFAULT_DEPLETION = 'death'

BATTERY_FLAGS = ('--hunger-unit', '--battery-recorded')
BATTERY_VALUED = {'--depletion': 1, '--capacity': 1, '--discharge': 1, '--recharge': 1,
                  '--food-saturation': 1, '--critical-level': 1, '--min-efficiency': 1,
                  '--battery-signal': 1, '--hunger-inputs': 1}

# The numeric options: option -> add_battery_to_homeostat's argument
_NUMERIC = {'--capacity': 'capacity', '--discharge': 'discharge_rate',
            '--recharge': 'recharge_factor', '--food-saturation': 'saturation',
            '--critical-level': 'critical_level', '--min-efficiency': 'min_efficiency'}


def parse_battery(argv, continuous_params=None):
    '''The battery the options in argv ask for: add_battery_to_homeostat's
    arguments, a dict.  continuous_params: the parsed --stress-source, given
    to the Hunger unit too.'''
    from KheperaSimulator.Battery import DEPLETION_MODES
    from RobotSimulator.Transducer import HOMEO_BatterySensor

    def choice(option, choices, default):
        if option not in argv:
            return default
        idx = argv.index(option)
        value = argv[idx + 1] if idx + 1 < len(argv) else ''
        if value not in choices:
            raise SystemExit('%s must be one of %s, got %r' % (option, ' '.join(choices), value))
        return value

    battery = dict(depletion=choice('--depletion', DEPLETION_MODES, DEFAULT_DEPLETION),
                   signal=choice('--battery-signal', HOMEO_BatterySensor.SIGNALS, 'hunger'),
                   hunger_unit='--hunger-unit' in argv,
                   to_motors='--battery-recorded' not in argv)
    for option, name in _NUMERIC.items():
        if option in argv:
            battery[name] = common._value(argv, option, float, '%s needs a number' % option)
    if '--hunger-inputs' in argv:
        if not battery['hunger_unit']:
            raise SystemExit('--hunger-inputs applies only with --hunger-unit')
        battery['hunger_inputs'] = choice('--hunger-inputs', ('battery', 'all'), 'battery')
    if continuous_params and continuous_params.get('stress_source'):
        battery['stress_source'] = continuous_params['stress_source']
    return battery


def main(argv):
    o = common.parse_common_args(argv, flags=direct.VEHICLE_FLAGS + BATTERY_FLAGS,
                                 valued=dict(direct.VEHICLE_VALUED, **BATTERY_VALUED))
    direct.run(o, direct.parse_vehicle(argv),
               battery=parse_battery(argv, o['continuous_params']),
               experiment=EXPERIMENT, batch_name='hunger')


if __name__ == '__main__':
    import sys
    main(sys.argv)
