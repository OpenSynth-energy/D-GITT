# Substation disaggregation and limit scoring

Participants submit one net active-power injection $\hat P_s$ per substation,
positive for injection into the AC grid and negative for withdrawal. The scorer
converts it into equipment setpoints before running the DC power flow.

## Case selection

Cases are mutually exclusive and applied in this order:

| Priority | Condition | Case |
|---:|---|---|
| 1 | Zero reference throughput, regardless of equipment | Case 2 |
| 2 | Nonzero throughput with a dangling line or designated HVDC proxy | Case 3 |
| 3 | Any other nonzero-throughput substation | Case 1 |

## Reference contributions

Let $P_s^{\ast}$ be the reference substation net and $c_i^{\ast}$ the signed reference
contribution of equipment $i$. The private factor file stores

$$
f_i =
\begin{cases}
c_i^{\ast}/\lvert P_s^{\ast}\rvert, & \lvert P_s^{\ast}\rvert>\varepsilon,\\
c_i^{\ast}, & \lvert P_s^{\ast}\rvert\leq\varepsilon,
\end{cases}
\qquad \varepsilon=10^{-6}\ \mathrm{MW}.
$$

The scorer reconstructs

$$
c_i^{\ast} =
\begin{cases}
f_i\lvert P_s^{\ast}\rvert, & \lvert P_s^{\ast}\rvert>\varepsilon,\\
f_i, & \lvert P_s^{\ast}\rvert\leq\varepsilon.
\end{cases}
$$

Therefore $\hat P_s=P_s^{\ast}$ reproduces the reference dispatch.

For nonzero-throughput substations, equipment roles follow $c_i^{\ast}$ rather than
equipment type:

| Reference contribution | Role |
|---:|---|
| $c_i^{\ast}>0$ | Positive injector |
| $c_i^{\ast}<0$ | Negative injector |
| $c_i^{\ast}=0$ | Zero-reference unit |

A load may be a positive injector and a generator may be a negative injector.
Connection status is separate: connected units are active and disconnected units
are never used.

## Limits and scoring

All limits use the signed-injection convention. Generator `minP` and `maxP`
already follow it. Load and dangling-line `p0` limits must be sign-reversed and
swapped because $c_i=-p_{0,i}$.

| Available limits | Positive injector $[\ell_i,u_i]$ | Negative injector $[\ell_i,u_i]$ |
|---|---:|---:|
| `pmin`, `pmax` | $[p_{\min},p_{\max}]$ | $[p_{\min},p_{\max}]$ |
| `pmax` only | $[0,p_{\max}]$ | $(-\infty,p_{\max}]$ |
| `pmin` only | $[p_{\min},+\infty)$ | $[p_{\min},0]$ |
| Neither | $[0,+\infty)$ | $(-\infty,0]$ |

An injector may cross zero when its limits permit it. A missing directional
limit remains infinite.

### Boundary-transfer assets

Dangling lines and designated HVDC generator proxies are boundary-transfer
assets. Their excess never contributes to the ordinary asset count
$N^{\mathrm{lim}}$. Instead, minor and severe thermal violations contribute to
$N^{\mathrm{ov},1}$ and $N^{\mathrm{ov},2}$.

| Asset | Directional limit used by the DC scorer |
|---|---|
| Dangling line | Current limit converted to active power |
| Designated HVDC generator proxy | Declared directional limit |
| Missing directional limit | Unbounded in that direction; no thermal violation can be established |

### Synthetic upper limits for positive-injecting loads

Loads have no published active-power limits. The backend gives every public load
observed injecting positively in the 190 accepted sensitive snapshots the private
upper limit

$$
u_i^{\mathrm{load}}=\max\left(0,\max_{t\in T_i}c_{i,t}^{\ast}\right)+\eta,
$$

where $T_i$ contains snapshots in which load $i$ exists in both the sensitive
snapshot and its corresponding public topology, and
$\eta=10^{-6}\ \mathrm{MW}$ is a numerical safety margin.

| Property | Treatment |
|---|---|
| Positive upper limit | Maximum observed positive injection, plus $\eta$ |
| Lower limit | Not created |
| No observed positive injection | Upper limit zero; no table row required |
| Sign-changing load | Finite synthetic upper limit; unbounded lower direction |
| Publication | Private because the limits derive from sensitive data |

These private limits are included in $U_s$. They therefore increase each
affected substation's positive injection ceiling by the sum of its positive-load
upper limits.

Every public load with $c_i^{\ast}>0$ in a scored snapshot must have exactly one row
in the private table. Otherwise scoring stops with `E_LOAD_LIMIT_TABLE`:

| Feedback | Contents |
|---|---|
| Participant | Competition-side error code and instruction to contact organisers |
| Admin | Snapshot, substation ID, load ID, and missing/duplicate status |

### Substation ceiling and water-filling

For each snapshot,

$$
U_s=\sum_{i\in A_s}u_i,
$$

where $A_s$ contains applicable connected units. It includes connected
zero-reference ordinary generators and boundary assets. A zero-reference load is
excluded from upward capacity while a connected ordinary generator exists.

Water-filling distributes $\hat P_s-P_s^{\ast}$ using fixed weights
$w_i=\lvert c_i^{\ast}\rvert$. A unit reaching its relevant limit is clamped; the remainder is
redistributed over unsaturated nonzero-weight units using the original weights.
If all bounded nonzero-weight units clamp, remaining connected zero-reference
generator and boundary capacity is used before overload, weighted by directional
capacity (`maxP` for generators and the directional thermal limit for boundary
assets). If an eligible zero-reference unit is unbounded in that direction, it
takes the entire remainder and finite-capacity zero-reference units receive none.
Multiple eligible unbounded zero-reference units split that remainder equally.

An unbounded nonzero-weight unit never clamps. It continues receiving its
factor-weighted share and receives the whole remainder after the other
nonzero-weight units clamp; zero-reference capacity then need not be used.

### Positive overflow

| Available route | Treatment |
|---|---|
| Directionally unbounded boundary asset | Continues carrying residual without a thermal violation |
| Finite boundary route | Keep ordinary generators at `maxP`; share residual over the boundary assets by directional thermal limit, producing only $N^{\mathrm{ov},1}$ and $N^{\mathrm{ov},2}$ |
| No boundary route, connected ordinary generators | Share residual over every connected ordinary generator by `maxP`; every generator, including zero-reference generators, adds one to $N^{\mathrm{lim}}$ |
| Neither boundary route nor generator | Share the residual over connected loads in proportion to their synthetic upper limits; if all limits are zero, share it equally. Loads may exceed their synthetic limits without contributing to $N^{\mathrm{lim}}$ |

Finite boundary allocation equalises normalized loading, so all participating
routes enter each thermal-overload band simultaneously.

## Case 1: ordinary injectors only

Applies to nonzero-throughput substations without boundary-transfer assets.

| Regime | Condition | Allocation and scoring |
|---|---|---|
| 1 | Within nonzero-reference range | Water-fill over connected nonzero-reference equipment using $\lvert c_i^{\ast}\rvert$ |
| 2 | Nonzero-reference units saturated, connected capacity remains | Fill connected zero-reference ordinary generators by `maxP`, within their limits |
| 3 | Above all connected upper capacity | Overfill every connected ordinary generator by `maxP`; all generators cross together and each adds one to $N^{\mathrm{lim}}$. Positive loads remain at their synthetic limits unless no generator exists |
| 4 | Below all connected lower capacity | Use negative-capable ordinary units, then positive-capable ordinary units through zero if necessary; every overfilled ordinary generator adds one to $N^{\mathrm{lim}}$ |

## Case 2: zero reference throughput

Applies when

$$
\sum_i\lvert c_i^{\ast}\rvert\leq\varepsilon,
$$

regardless of boundary assets. Since no reference shares exist, allocation uses
declared or synthetic directional capacities:

$$
q_i^{+}=\max(u_i,0),\qquad q_i^{-}=\max(-\ell_i,0).
$$

| Regime | Condition | Allocation and scoring |
|---|---|---|
| 1 | Within connected capacity | Share by $q_i^{+}$ or $q_i^{-}$. Generators use `maxP`; boundary assets use directional thermal capacity. A positive load participates only when no connected ordinary generator exists |
| 2 | Above finite positive capacity | Apply the positive-overflow routing table |
| 3 | Below finite negative capacity | Use negative-capable boundary assets first; otherwise use negative-capable ordinary units, then positive-capable ordinary units through zero. Every overfilled ordinary generator adds one to $N^{\mathrm{lim}}$ |

An unbounded unit in the requested direction absorbs the remaining request and
prevents an overload in that direction.

## Case 3: boundary-transfer assets present

Applies to nonzero-throughput substations with at least one dangling line or
designated HVDC proxy.

| Regime | Condition | Allocation and scoring |
|---|---|---|
| 1 | Within nonzero-reference range | Water-fill over connected nonzero-reference ordinary and boundary units using $\lvert c_i^{\ast}\rvert$. Finite units clamp individually; unbounded units do not clamp |
| 2 | Nonzero-reference units saturated, connected capacity remains | Fill connected zero-reference ordinary generators by `maxP` and boundary assets by directional thermal capacity, within their limits |
| 3 | Above all finite upper limits | Keep generators and positive loads at their limits; share residual over finite positive-direction boundary assets by thermal limit. They enter $N^{\mathrm{ov},1}$ and then $N^{\mathrm{ov},2}$ together. If an unbounded boundary asset exists, it absorbs the residual without a violation |
| 4 | Below all finite lower limits | Keep ordinary units at lower limits; share residual over finite negative-direction boundary assets by thermal limit. They enter $N^{\mathrm{ov},1}$ and then $N^{\mathrm{ov},2}$ together. If an unbounded boundary asset exists, it absorbs the residual without a violation |

If no boundary asset is usable in the overflow direction, the corresponding
Case 1 overflow rule applies. Boundary assets never contribute to $N^{\mathrm{lim}}$.

## Grid setpoints

| Equipment | Written setpoint |
|---|---:|
| Generator | `target_p` $=c_i$ |
| Load | `p0` $=-c_i$ |
| Dangling line | `p0` $=-c_i$ |
