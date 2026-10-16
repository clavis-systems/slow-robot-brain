# I predicted which robot skills break first when the robot's brain is slow. The prediction failed.

*Emanuele Rizzan, independent researcher, October 2026.*

## The question

Robots that use large AI models think slowly. While the model is thinking, the arm keeps moving on the old plan.

I wanted to know if you can predict, **before testing**, which skills suffer most from a slow brain, using only two
cheap measurements of each skill:

- **M, the precision margin.** I shift the robot's sensed hand position by a few centimetres. M is the shift at which
  the skill's success rate falls to half of its rate with no shift.
- **v, the hand speed** near the end of the movement.

The guess, called "Law 1 of freshness", was simple. A skill tolerates a delay of about **T̂ = M / v** steps: the time
the hand needs to drift out of its margin. Skills with a small T̂ should break first.

## How it was tested

**Setup**
- **Robot and tasks:** Hugging Face's SmolVLA policy (`HuggingFaceVLA/smolvla_libero`, revision `6721902b`) on the
  10 LIBERO-goal tasks.
  - Everything ran in simulation on free Kaggle GPUs.
  - Episodes have at most 300 control steps.
- **Slow brain:** the delay is simulated, so real compute time plays no part.
  - The policy's new plan arrives D control steps after the observation it was computed from. Meanwhile the arm keeps
    executing the old plan.
  - With D = 16, after the first plan every action comes from an observation 16 to 31 steps old.

**Phase B: measuring M and v**
- Shifts of 0, 2, 4, 8, 12 and 16 cm, in 5 fixed directions in the horizontal plane, with 5 scenes per shift. These
  scenes are used nowhere else.
- v is the median horizontal hand speed over the 32 steps before success, in successful no-shift episodes.
- **Phase B did not run cleanly in one go.**
  - In the first run the second GPU failed, so it produced data only for skills 1–5.
  - Skills 6–10 were measured in a second run, with slightly newer code.
  - This is recorded as a deviation in the pre-registration.
- Two skills ("top drawer + bowl" and "wine rack") succeeded only once in 5 tries with no shift, so their M rests on
  very little data.
- One skill (wine rack) never fell to half success even at 16 cm. Its M is only a lower bound ("censored").

**The freeze**
- The predicted ranking, the decision rules and the SHA-256 of the analysis code were frozen before the decisive test:
  local git commit `3a96427`, tag `legge1-congelata`, 14 October 2026 at 09:24 CEST.
- Git timestamps are self-reported. As an external anchor, the Kaggle log of the control run prints the hash of the
  freeze record.

**Phase C: the decisive test**
- 20 new scenes per skill, with no delay and with delay 16.
- **Robustness:** R = (successes at delay 16 + ½) / (successes at delay 0 + ½). It is the share of its successes a
  skill keeps under delay. The ½ avoids dividing by zero. Lower R means more fragile.

**Pre-registered rules**
- **Test:** Spearman ρ between T̂ and R, with an exact one-sided permutation test over all 10! orderings.
- **Sensitivity analysis:** the censored skill is moved to the robust end of the predicted ranking.
- **Verdict:**
  - the test counts only if the delay costs at least 10 points of total success;
  - Law 1 is supported if p ≤ 0.05 in both analyses, inconclusive if in one only, not supported if in neither.

## The result

**The delay did real damage, but T̂ did not explain which skills it damaged.**

**Main numbers**
- **Damage:** total success fell from 136/200 to 81/200, a drop of 27.5 points, well above the 10-point minimum.
  Every failure at delay 16, in all 10 skills, was a 300-step timeout.
- **Main analysis:** ρ = 0.37, exact p = 0.148. Bootstrap 95% interval for ρ: −0.38 to 0.90.
- **Sensitivity analysis:** ρ = 0.28, p = 0.214.
- **Verdict: Law 1 is not supported.**
- **One caveat on the verdict:** the written description of the sensitivity analysis in the freeze record can be read
  the other way round (the censored skill at the fragile end). That reading gives ρ = 0.59, p = 0.040, and the verdict
  would be "inconclusive". The frozen code (SHA-256 `f0bddd4d…`) puts it at the robust end, which matches the logic of
  a lower bound, and the frozen code decides.

**Simpler predictors**
- A trivial predictor did better than T̂: success with no shift in phase B alone gives ρ = 0.49.
- M alone gives 0.31, 1/v alone gives 0.07.

**The control, with no delay and the brain re-planning every 16 steps instead of every 8**
- At delay 16 the brain also re-plans only every 16 steps. This control separates "stale plan" from "less frequent
  re-planning".
- Re-planning less often did not hurt: 147/200 successes, against 136/200.
- T̂ did not track this change (ρ = −0.12). The damage comes from stale plans, not from re-planning less often.
- The control ran after the decisive results had been seen, with the frozen code.

| Skill | Predicted rank (1 = most fragile) | T̂ (steps) | Successes of 20, delay 0 | Successes of 20, delay 16 | Observed rank (1 = lowest R) |
|---|---|---|---|---|---|
| open the top drawer and put the bowl inside | 1 | 1.2 | 4 | 2 | 4 |
| put the bowl on the plate | 2 | 3.5 | 17 | 7 | 2 |
| put the bowl on the stove | 3 | 6.5 | 20 | 13 | 7 |
| put the cream cheese in the bowl | 4 | 6.8 | 14 | 8 | 5 |
| put the bowl on top of the cabinet | 5 | 9.2 | 20 | 15 | 9 |
| push the plate to the front of the stove | 6 | 17.0 | 12 | 2 | 1 |
| put the wine bottle on top of the cabinet | 7 | 17.9 | 16 | 10 | 6 |
| open the middle drawer of the cabinet | 8 | 21.1 | 9 | 6 | 8 |
| put the wine bottle on the rack (censored) | 9 | ≥ 23.9 | 5 | 2 | 3 |
| turn on the stove | 10 | 205.9 | 19 | 16 | 10 |

**Hits and misses**
- **Three skills landed exactly on their predicted rank:** the stove knob (most robust), the bowl on the plate and the
  middle drawer. With 10 skills, about one exact match is expected by chance, so this is not evidence for the law.
- **My own intuition was wrong too.** Before any data, I guessed that the knob would break first. It was the most
  robust skill.
- **The two biggest misses** were the wine rack (predicted 9th, observed 3rd) and pushing the plate (predicted 6th,
  observed 1st, from 12 successes to 2).
- **A guess about the plate:** pushing is a continuous contact, so being late may hurt during the whole movement, not
  only near the end, where v was measured. This is a hypothesis, not a finding.

## A mistake the independent check caught

**What we logged.** Two exploratory "mechanism" measures, averaged over the first 6 plan arrivals of each episode.
One of them correlated −0.75 with robustness, and we first read it as support for the next idea.

**What the check found.** An independent recomputation from the raw data showed that most of the signal came from
**episode length**:
- successful episodes often end after only 3–5 plan arrivals, while failed ones always reach 6, so the averages cover
  different parts of the movement;
- using only the first 3 arrivals of every episode, the correlation drops to −0.19.

The pre-registration had already limited the measure to the first 6 arrivals for this reason, and that was not
enough. We report the signal as an artifact.

## Limits

- **Small test, low power.** With 10 skills and 20 scenes each, the pre-registered power was only about 0.52 if the
  law were fully true, and 0.35 if partly true. As the pre-registration says, this null result does not refute the
  law: it fails to support it.
- **Narrow scope:** one policy, one simulator, one kind of delay.
- **What M really measures.** The shift changes only the sensed hand position, while the images stay fresh; the delay
  makes everything stale. So M may measure how much the policy trusts its state, not only geometric precision.
- **Not fully independent checks.** They were done by a fresh instance of Claude, the same model family that wrote the
  code. A check by a different system (Codex) is planned from 10 November.
- **A change after the freeze.** The wording of the readable report was improved after the freeze; the analysis code
  did not change.

## Related work

- **Delay in robot policies is an active topic in 2026.** Recent papers compare ways to make vision-language-action
  policies run asynchronously (for example on LIBERO with delays of up to 20 control steps), or study delay together
  with distribution shift.
- **I did not find any work that tries to predict, before testing, which tasks a delay will hurt most.** That is the
  question here.
- **One link to note.** The delay-and-distribution-shift study reports that longer action queues help. That fits our
  control, where acting on longer chunks without delay did not hurt. Ours is a small simulation result, not a
  confirmation.

## How this was made

**This is my project, and it exists because I started it and drove it.**
- I chose the question and set the rules: write the prediction down before seeing the data, have every result
  rechecked independently, report failures as well as successes.
- At every step I decided what to test, when to stop and what to publish.
- I am not a programmer. I worked with an AI coding agent (Claude Code), which drafted the theory, the
  pre-registration, the code and the analysis under my direction.

## Files

The internal records are in Italian, because that is how I work. The code is commented in Italian.

| Folder | What is inside |
|---|---|
| `preregistration/` | `PREMESSA_LEGGE1.md` (pre-registration v3 and every deviation), `PREVISIONI.md` (predictions written before the data, my intuition included), `CONGELAMENTO_LEGGE1.md` (freeze record with SHA-256 hashes), `RISULTATO_LEGGE1.md` (final record) |
| `code/` | `analisi_legge1.py` (frozen analysis), `cervello_lento.py` (slow-brain wrapper), `organo_tatto.py` (hand shift and measurements), freeze, report and power scripts, tests, `kaggle/` (the Kaggle run script) |
| `data/` | phase B (`b_1`, `b_2`), decisive phase C (`c_1`), control (`c_2`), development curves seen before the predictions (`c_d0`, `c_d8`, `c_d24`), package versions |
| `results/` | readable report, full JSON result, figures |
| `reviews/` | two independent reviews of the pre-registration and the independent recomputation of the verdict |

**To rerun the analysis** (Python 3 with numpy, plus matplotlib and pytest for the report and the tests; the SHA-256 hashes of the data match the freeze record):

```
cd code
python analisi_legge1.py test --c ../data/c_1.jsonl --c ../data/c_2.jsonl --b ../data/b_1.jsonl --b ../data/b_2.jsonl
python -m pytest -q
```

License: Apache-2.0.
