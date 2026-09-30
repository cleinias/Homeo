# Research Journal

Dated entries, newest first. Longer write-ups live in
`../Cybernetics-research/Research-notes/` (see its `INDEX.md`).

---

## 2026-09-30 (session of 29–30 Sep): GA GUI fixes; first battery test

Resumed work after a break of about six months (last activity: 3 Mar 2026,
branch `Hunger-drive`).

### GA Simulation GUI

- **A run with the default settings learns nothing.** The run used
  `initializeBraiten2_2_Full_GA_phototaxis`, population 150, 100 generations,
  **1000 steps**. The best fitness plateaued at 4.212 by generation 12,
  against a starting distance of 4.243. In 1000 steps the robot moves about
  1.5 cm, so the GA is only selecting among twitches. The Feb 2026 runs used
  60,000 steps.
- **Bug: GA trajectory files were empty or truncated** (fixed: `0e90217` on
  `Hunger-drive`, `a414b7d` on `master`). The GA evaluators never closed the
  `.traj` file, so buffered rows were lost. Python 3.14's 128 KB buffer holds
  a whole 1000-step trajectory (~100 KB), so 78% of files had only a header,
  which caused the viewer error "too many indices for array". With the older
  8 KB buffer, every file lost its last rows, including the final position.
  **GA `.traj` files from before this fix are incomplete; logbook fitness
  values are unaffected.** The viewer now reports empty files clearly.
- **Bug: runs were nested inside another run's folder** (fixed: `b12e273` /
  `6fb2a29`). `simulations_data_dir()` read `~/.HomeoSimDataDir.txt` as the
  root, but the general GUI writes its session folder there.
- Wrote `Research-notes/Homeo GA Simulation GUI - user guide.md`.
- `…_Full_GA` vs `…_Full_GA_phototaxis`: the only difference is the light's
  intensity (+100 vs −100). `…_Full_GA` rewards approaching a light the
  vehicle tends to avoid; it's the 2014 original. Use `…_phototaxis` to
  compare with Feb 2026.

### Hunger drive: first battery test

- **The battery setup had never been run** before this session. There are
  no output files after 3 Mar.
- **Bugs found in the first visualizer test (battery at 0 throughout),
  fixed in `74f399f`:**
  1. Recharge quality `'light'` was looked up in `detectableSources`, which
     is empty in the Braiten2 world, so the battery never recharged. It now
     falls back to `detectableLights`.
  2. Irradiance was read at the left eye. It was negative for the −100
     phototaxis light, which would have turned recharge into drain, and it
     depended on heading. It is now measured by the new
     `KheperaRobot.irradAtCentre()`: independent of heading, using
     |intensity|, capped at 100 like the eyes.
  3. The battery ticked once per physics sub-step (twice per homeostat
     tick). It now ticks once per tick via `Homeostat._tick_hooks`.
- **The recharge rate is not calibrated yet.** Centre irradiance by
  distance to the light:

  | Distance | ≤ 1 | 1.5 | 2 | 3 | 4.24 (start) | 6 | 10 |
  |---|---|---|---|---|---|---|---|
  | Irradiance | 100 | 44.4 | 25 | 11.1 | 5.6 | 2.8 | 1.0 |

  With the default `recharge_factor = 0.01` the battery stays full
  everywhere. Break-even at 1.5 would need about 2.25e-5.
- **A full battery made the robot spin.** The battery unit sat at +10 and
  fed both motors through random weights between −1 and +1 (from
  `addFullyConnectedUnit`), a constant bias about 10–40 times stronger than
  the light input. **Change:** the battery unit now carries hunger
  (`invert=True`: 0 when full, +10 when empty), so a fed robot gets no
  battery input (in `hunger_chemotaxis.py` only; the GA initializers still
  use the level).
- **The robot still spins, and not because of the battery.** The underlying
  weight-free OU vehicle with the hand-picked genome has random-signed
  starting sensor weights (seed 1: −0.036 / +0.056). With the negative
  sensor readings, these drive the wheels in opposite directions. The OU
  process barely explores: stress is about 0 whether it comes from hunger
  (full battery) or from each unit's own deviation (0.002–0.009, since
  `maxDeviation ≈ 500`). The weights just shrink toward θ = 0.01. This is
  the same failure as Feb Exp 2 (OU alone).

### Next

- Test the battery on a vehicle that does reach the light: hand-wired
  fixed crossed weights, as in the control experiment. Calibrate
  `recharge_factor` there.
- Then restore the hunger-driven OU: lower the recharge so hunger rises,
  and check whether the resulting exploration finds the light.
- Look into why headless runs were about 40× slower than non-headless ones
  (JIT recompiling?).

---

## Earlier work (summary, Feb–Mar 2026)

See `Research-notes/Development summary - February-March 2026.md`. Main
results: GA+OU phototaxis looked promising at 60k steps (best 0.27–0.34),
but in 300k-step validation every mechanism drifted away from the light.
The OU process gets no feedback from performance, which motivated the
hunger drive (`Final report on phototaxis comparison experiments.md`,
`Validation experiment - 300k steps.md`).
