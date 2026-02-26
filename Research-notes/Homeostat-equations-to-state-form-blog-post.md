# From Ashby's Homeostat to State-Space Form: A Control-Theoretic Perspective

Ashby's homeostat is a remarkable device: a network of interconnected units, each driven by a second-order differential equation, that collectively seeks equilibrium through homeostatic feedback. But what can modern control theory tell us about it? In this post we convert the homeostat's equations into state-space form and investigate what controllability and observability look like for this system. We then take a detour into Braitenberg vehicles---simple stimulus-response robots---and analyze their dynamics as a stepping stone toward understanding homeostat-controlled vehicles.

## The Homeostat's Equation

A single unit $i$ in an $N$-unit homeostat obeys:

$$m_i \ddot{y}_i = -v_i \dot{y}_i + \sum_{j=1}^{N} w_{ij} y_j + c_i u_i$$

where:
- $m_i$ is the mass (inertia) of unit $i$'s needle
- $v_i$ is the viscosity of unit $i$'s medium
- $w_{ij}$ is the connection weight **from unit $j$ to unit $i$**
- $u_i$ is the external input to unit $i$, scaled by coefficient $c_i$

This is a damped harmonic oscillator coupled to every other unit through the weights $w_{ij}$---exactly the kind of system that state-space methods are designed to handle.

## Converting to State-Space Form

For each unit $i$, we define two state variables:

$$\begin{bmatrix} x_{i_1} \\ x_{i_2} \end{bmatrix} = \begin{bmatrix} y_i \\ \dot{y}_i \end{bmatrix}$$

This gives us:
- $\dot{x}_{i_1} = x_{i_2}$ (position derivative is velocity)
- $\dot{x}_{i_2} = \frac{1}{m_i}\left(-v_i x_{i_2} + \sum_{j=1}^{N} w_{ij} x_{j_1} + c_i u_i\right)$ (from the original equation)

The full state vector $\mathbf{x} = [x_{1_1}, x_{1_2}, x_{2_1}, x_{2_2}, \ldots, x_{N_1}, x_{N_2}]^T$ has dimension $2N$, and we need matrices $A$ ($2N \times 2N$), $B$ ($2N \times 1$ for a scalar input $u$), and $C$ ($1 \times 2N$) satisfying:

$$\dot{\mathbf{x}} = A\mathbf{x} + Bu, \quad y = C\mathbf{x}$$

The $A$ matrix has a characteristic block structure. For each unit $i$, there are two rows:
- **Odd row** (position): all zeros except a 1 in column $2i$ (the velocity component)
- **Even row** (velocity): $w_{ij}/m_i$ in each odd column $2j-1$ (the position components from all units), and $-v_i/m_i$ in column $2i$ (its own velocity)

### 2-Unit Example

For a 2-unit homeostat, the matrices are:

$$A = \begin{bmatrix} 0 & 1 & 0 & 0 \\ w_{11}/m_1 & -v_1/m_1 & w_{12}/m_1 & 0 \\ 0 & 0 & 0 & 1 \\ w_{21}/m_2 & 0 & w_{22}/m_2 & -v_2/m_2 \end{bmatrix}$$

$$B = \begin{bmatrix} 0 \\ c_1/m_1 \\ 0 \\ c_2/m_2 \end{bmatrix}, \quad C = \begin{bmatrix} 1 & 0 & 1 & 0 \end{bmatrix}$$

The pattern is clear: odd rows propagate velocities to positions, even rows encode the coupled dynamics. The $B$ vector delivers the input only to the velocity (even) components, weighted by each unit's $c_i/m_i$. The output matrix $C$ observes both units' positions.

With the default Homeo values ($m_1 = m_2 = 100$, $v_1 = v_2 = 10$, $c_1 = c_2 = 1$), this becomes:

$$A' = \begin{bmatrix} 0 & 1 & 0 & 0 \\ w_{11}/100 & -1/10 & w_{12}/100 & 0 \\ 0 & 0 & 0 & 1 \\ w_{21}/100 & 0 & w_{22}/100 & -1/10 \end{bmatrix}, \quad B' = \begin{bmatrix} 0 \\ 1/100 \\ 0 \\ 1/100 \end{bmatrix}$$

## Controllability: Can We Steer the Homeostat?

A system is completely controllable if and only if the **controllability matrix**

$$\Gamma = \begin{bmatrix} B & AB & A^2B & \cdots & A^{n-1}B \end{bmatrix}$$

has full rank (i.e., $\operatorname{rank}(\Gamma) = n$, the state dimension).

For our 2-unit homeostat with $n = 4$, we need $\Gamma = [B, AB, A^2B, A^3B]$ to have rank 4. A symbolic computation (using Sage) confirms that **the rank is indeed 4---provided all coefficients are distinct**. The homeostat is fully controllable.

But here's the interesting result: **if all weights are identical** ($w_{11} = w_{12} = w_{21} = w_{22}$) and the unit parameters are the same ($m_1 = m_2$, $v_1 = v_2$, $c_1 = c_2$), the rank drops to 2. The system becomes uncontrollable because the two units are now dynamically indistinguishable---the controllability matrix develops repeated rows.

This makes physical sense. If every unit is identical and identically connected, you can't independently steer them with a single input. The system has a symmetry that collapses the effective state space.

Controllability can be recovered even with minimal differentiation. Setting just $w_{11} = w_{12} = 1$ and $w_{21} = w_{22} = 2$ (same weights within each unit, but different between units) restores full rank. **Any symmetry-breaking in the weights suffices.**

This is a notable result for the homeostat: Ashby's uniselector mechanism, which randomly reassigns connection weights, is not just a heuristic for finding stability---it also serves to break symmetries that would make the system uncontrollable.

## Observability: Can We See the Full State?

Dually, a system is completely observable if and only if the **observability matrix**

$$\Omega = \begin{bmatrix} C \\ CA \\ CA^2 \\ \vdots \\ CA^{n-1} \end{bmatrix}$$

has full rank. For the 2-unit homeostat with $C = [1, 0, 1, 0]$ (observing both positions), a symbolic computation yields:

$$\Omega = \begin{bmatrix} 1 & 0 & 1 & 0 \\ 0 & 1 & 0 & 1 \\ w_{11}/m_1 + w_{21}/m_2 & -v_1/m_1 & w_{12}/m_1 + w_{22}/m_2 & -v_2/m_2 \\ (\text{4th row from } CA^3) & \cdots & \cdots & \cdots \end{bmatrix}$$

The rank is 4 (with distinct coefficients), so the system is fully observable. The same caveat applies: identical parameters collapse the observable subspace, and the same weight-differentiation strategy restores it.

## Detour: Braitenberg Vehicles in Control-Theoretic Terms

Braitenberg's vehicles are minimal creatures: a sensor, a motor, and a wire between them. Yet their emergent behaviour---seeking, fleeing, oscillating---is surprisingly rich. Can we understand these behaviours through phase portraits?

### Setup

Consider a 1D world with a stimulus source at position $s$ emitting stimulus of intensity $S$. A point-like vehicle at position $x$ has a single omnidirectional sensor and a single motor. The perceived intensity at the vehicle is:

$$I(x) = \frac{S}{1 + |s - x|^2}$$

(inverse-square falloff, with a regularizing +1 to avoid singularity at the source). The sensor output, scaled by efficiency $\alpha \in [0,1]$, is $y = \alpha \cdot I(x)$.

Two wiring schemes:
- **Direct** ($u = Ky$): motor output proportional to sensor reading. Close to the source means strong stimulus means fast movement.
- **Inverse** ($u = K/y$): motor output inversely proportional. Close means weak drive; far means strong drive.

### Omnidirectional Sensor

Substituting and collapsing to a single ODE:

**Direct connection:**
$$\dot{x} = \frac{\alpha K S}{1 + |s - x|^2}$$

**Inverse connection:**
$$\dot{x} = \frac{K(1 + |s - x|^2)}{\alpha S}$$

Both are always positive (assuming positive constants), so **neither has a fixed point in the omnidirectional case**. The vehicle always moves in the same direction. The only difference is the speed profile: the direct-connected vehicle speeds up as it approaches the source (Braitenberg's "aggressive" vehicle), while the inverse-connected one slows down (the "timid" vehicle). But neither stops.

### Adding Directionality

Real sensors have a limited field of view. We model a forward-looking sensor by multiplying the intensity by a logistic cutoff:

$$\sigma(x) = \frac{1}{1 + e^{\beta(s-x)}}$$

where $\beta < 0$ (steep negative). This equals ~1 when the source is ahead ($s > x$) and ~0 when behind ($s < x$).

The resulting ODEs become:

**Direct connection, directional:**
$$\dot{x} = \frac{\alpha K S}{1 + |s - x|^2 + e^{\beta(s-x)}}$$

**Inverse connection, directional:**
$$\dot{x} = \frac{K(1 + |s - x|^2)}{\alpha S (1 + e^{\beta(s-x)})}$$

Now things get interesting. For both vehicles, once $x > s$ (robot has passed the source), the logistic factor kills the drive and $\dot{x} \approx 0$. Both vehicles effectively stop at $s$. But their approach profiles differ dramatically:

- The **direct-connected** vehicle accelerates as it nears the source, rushing in aggressively.
- The **inverse-connected** vehicle decelerates, approaching timidly.

The phase portraits confirm this: $x = s$ is an attracting quasi-fixed-point (not a true equilibrium, but the exponential suppression makes it effectively one), and all points beyond $s$ are also quasi-fixed.

### Toward More Complex Controllers

These pure Braitenberg vehicles have no internal dynamics---the mapping from sensor to motor is instantaneous. Adding a neural network or a homeostat as controller introduces internal state, turning the first-order system into a higher-order one. A Braitenberg vehicle with physics (mass and friction) already requires second-order dynamics:

$$m\ddot{x} = u(x) - v\dot{x}$$

where $u(x)$ is the stimulus-dependent drive. With a homeostatic controller in the loop, the full system becomes the coupled dynamics of the vehicle *and* the controller---precisely the state-space framework developed in the first part of this note.

## Why This Matters

The state-space formulation of the homeostat opens several doors:

1. **Stability analysis**: eigenvalues of $A$ directly reveal whether the system is stable, oscillatory, or divergent---without running simulations.

2. **Controllability and observability**: we can formally determine whether a given configuration of weights allows full control and full observation. The result that identical weights destroy controllability is practically significant: it explains why Ashby's random weight reassignment is not just a search strategy but a structural necessity.

3. **Controller design**: with the state-space form in hand, standard techniques (pole placement, LQR, Kalman filtering) become applicable, offering a bridge between homeostatic and optimal control.

4. **Braitenberg vehicle analysis**: even the simplest vehicles exhibit non-trivial dynamics that are cleanly captured by phase portraits. The transition from omnidirectional to directional sensors creates quasi-fixed-points that explain goal-seeking behaviour.

The unfinished business---linearizing the nonlinear Braitenberg equations, analyzing the Jacobian, connecting a homeostatic controller to a physical vehicle---points toward a unified control-theoretic framework for adaptive, homeostatic robots. The mathematical machinery is ready; the interesting work is in choosing the right operating points and understanding what the eigenvalues tell us about behaviour.
