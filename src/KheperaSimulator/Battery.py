'''
The robot's energy store: a battery that drains at a constant rate and
recharges from the food the robot absorbs, and what an empty battery does
to the wheels.

The battery models a metabolism, not eating: each tick it loses a constant
amount and gains an amount proportional to the food at the robot's centre
(KheperaRobot.foodAtCentre), whatever the robot's heading -- absorption
across the body surface, as a bacterium takes up dissolved nutrient.
Sensing and feeding are separate: the eyes say where the food is, the food
at the centre whether the robot gets any.

Both robots carry one (KheperaRobot.battery, WebotsRobot.battery; None: no
battery), both worlds tick it once per homeostat tick, after the units and
the world have moved (KheperaSimulation.tickAdvance,
WebotsSimulation.tickAdvance), and both robots' wheels apply its motor
efficiency.

@author: stefano
'''

# What an empty battery does (see Battery.motorEfficiency)
DEPLETION_MODES = ('none', 'paralysis', 'graded', 'death')

# A homeostat's battery with no recharge_factor given breaks even at this
# distance from the source the robot feeds on: closer, it gains charge;
# farther, it loses it (see Battery.breakEvenRechargeFactor).  The
# acquisition radius of the phototaxis experiments.
BREAK_EVEN_DISTANCE = 1.0


class Battery(object):
    '''A battery of the given capacity, full at the start.  Each tick
        level <- level - discharge_rate + recharge_factor * min(food, saturation)
    clamped to [0, capacity], where food is what the robot absorbs that tick.

    capacity        the charge of a full battery (the level's unit)
    discharge_rate  the charge lost per tick (the default empties a full
                    battery in 100,000 ticks: a fixed-weight crossed ++
                    vehicle, Braitenberg's 2b, reaches a light of intensity
                    100 from 6 units away in about 75,000)
    recharge_factor the charge gained per tick per unit of food (the default
                    breaks even at food 100, 1 unit from a light of
                    intensity 100)
    saturation      the most food a tick can absorb
    critical_level  the fraction of capacity below which the battery is
                    critical: counted (ticksCritical), and the gate of a
                    continuous uniselector whose stress_source is
                    'battery_critical'.  Above the lethal zero.
    depletion       what an empty battery does to the wheels, one of
                    DEPLETION_MODES:
                    'none'       nothing: the battery is only sensed
                    'paralysis'  the wheels stop while the battery is empty,
                                 and move again once it holds charge
                    'graded'     the wheels' speed is scaled by
                                 min_efficiency + (1 - min_efficiency) x level / capacity
                    'death'      at zero the robot dies: its wheels stop for
                                 good, and the run ends (deathTick records when)
    min_efficiency  the 'graded' mode's efficiency of an empty battery

    The battery also keeps its run's statistics: ticks, the mean and the
    minimum level, the ticks below the critical level and at zero, and the
    tick of death (None while alive) -- see summary().'''

    def __init__(self, capacity=1.0, discharge_rate=1e-5, recharge_factor=1e-7,
                 saturation=None, critical_level=0.3, depletion='none',
                 min_efficiency=0.1):
        if not capacity > 0:
            raise ValueError('capacity must be > 0, got %r' % capacity)
        if discharge_rate < 0 or recharge_factor < 0:
            raise ValueError('discharge_rate and recharge_factor must be >= 0, got %r, %r'
                             % (discharge_rate, recharge_factor))
        if saturation is not None and not saturation > 0:
            raise ValueError('saturation must be > 0 (None: none), got %r' % saturation)
        if not 0 <= critical_level < 1:
            raise ValueError('critical_level is a fraction of capacity in [0, 1), got %r'
                             % critical_level)
        if depletion not in DEPLETION_MODES:
            raise ValueError('depletion must be one of %s, got %r' % (DEPLETION_MODES, depletion))
        if not 0 <= min_efficiency <= 1:
            raise ValueError('min_efficiency must lie in [0, 1], got %r' % min_efficiency)
        self.capacity = float(capacity)
        self.discharge_rate = float(discharge_rate)
        self.recharge_factor = float(recharge_factor)
        self.saturation = None if saturation is None else float(saturation)
        self.critical_level = float(critical_level)
        self.depletion = depletion
        self.min_efficiency = float(min_efficiency)
        self.level = self.capacity
        self.alive = True
        self.deathTick = None
        self.ticks = 0
        self._levelSum = 0.0
        self.minLevel = self.capacity
        self.ticksCritical = 0
        self.ticksEmpty = 0

    def tick(self, food=0.0):
        '''One tick of metabolism, absorbing `food` (negative food counts as
        none); a dead battery stays empty.'''
        self.ticks += 1
        if self.alive:
            food = max(0.0, food)
            if self.saturation is not None:
                food = min(food, self.saturation)
            self.level = min(self.capacity, max(0.0, self.level - self.discharge_rate
                                                + self.recharge_factor * food))
            if self.depletion == 'death' and self.level <= 0:
                self.alive = False
                self.deathTick = self.ticks
        self._levelSum += self.level
        self.minLevel = min(self.minLevel, self.level)
        if self.isCritical():
            self.ticksCritical += 1
        if self.level <= 0:
            self.ticksEmpty += 1

    def fraction(self):
        "The level as a fraction of capacity"
        return self.level / self.capacity

    def hunger(self):
        "1 - level / capacity: 0 when full, 1 when empty"
        return 1.0 - self.fraction()

    def isCritical(self):
        "Is the level below the critical level?"
        return self.fraction() < self.critical_level

    def meanLevel(self):
        "The mean level over the ticks so far (the level itself before any)"
        return self._levelSum / self.ticks if self.ticks else self.level

    def meanOver(self, ticks):
        """The mean level over a run of `ticks` ticks, the ticks the battery
        has not lived through (after its death) counting as empty"""
        return self._levelSum / ticks if ticks else self.level

    def motorEfficiency(self):
        "The factor the wheels' speeds are multiplied by (see depletion)"
        if self.depletion == 'none':
            return 1.0
        if self.depletion == 'paralysis':
            return 1.0 if self.level > 0 else 0.0
        if self.depletion == 'graded':
            return self.min_efficiency + (1.0 - self.min_efficiency) * self.fraction()
        return 1.0 if self.alive else 0.0

    def range(self):
        "The level's range, (0, capacity)"
        return (0.0, self.capacity)

    def settings(self):
        "The battery's parameters, as the run's records give them"
        return dict(battery_capacity=self.capacity,
                    battery_discharge_rate=self.discharge_rate,
                    battery_recharge_factor=self.recharge_factor,
                    battery_saturation=self.saturation,
                    battery_critical_level=self.critical_level,
                    depletion=self.depletion,
                    battery_min_efficiency=self.min_efficiency)

    def summary(self):
        '''The run so far, as the run's result gives it: the mean, minimum and
        final level, the ticks below the critical level and at zero, whether
        the robot is alive and the tick it died (None if it did not).'''
        return dict(battery_mean=self.meanLevel(), battery_min=self.minLevel,
                    battery_final=self.level, battery_ticks=self.ticks,
                    ticks_critical=self.ticksCritical, ticks_empty=self.ticksEmpty,
                    alive=self.alive, death_tick=self.deathTick)

    @staticmethod
    def breakEvenRechargeFactor(discharge_rate, food):
        '''The recharge factor at which `food` (> 0) exactly balances the
        discharge: the food at BREAK_EVEN_DISTANCE from the source gives the
        battery its default recharge factor.'''
        if not food > 0:
            raise ValueError('break-even needs food > 0, got %r' % food)
        return discharge_rate / food
