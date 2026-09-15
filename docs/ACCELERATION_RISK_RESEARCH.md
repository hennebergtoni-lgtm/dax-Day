# Existing risk research owners expanded — Step2235

boost001 retains its valid-input bounded-sleeve/IID results and adds explicit FixedCashResearchConfig, simulate_fixed_cash, resample_indices and fixed_cash_tail_research. It is pure offline research and cannot size/admit/submit a runtime order. No new Risk stack/store/lifecycle is introduced.

Existing SleeveConfig accepted NaN/Inf in comparisons; its finite/type validation is hardened without changing valid historical simulation rules. Finite R evidence rejects booleans/strings/overflow. Invalid path/horizon/seed/block labels fail closed.

Resampling modes: IID baseline, chronological circular blocks, contiguous session blocks, contiguous cluster blocks, homogeneous regime runs. Regime runs preserve within-run sequence, not transition probabilities; final declared trade horizon can truncate the last unit and reports that censoring. No bootstrap models unseen shocks. All stresses reuse identical sampled indices. Normal/1.5x/2x require supplied gross-R and explicit per-trade cost-R; aggregate net-R is insufficient.

Fixed cash is capped at declared cash risk and floor headroom. Losses never increase risk above baseline. Floor-hit stops the modeled path; losses below -1R remain visible, including negative hypothetical capital. Floor-hit is model-specific, not universal bankruptcy or account-equity proof. Account margin, intrabar equity, financing and cashflows are not modeled.

failure_analysis reuses finite empirical distribution validation and adds trade_sequence_dna: signed net-R, gross-profit concentration, top1/5/10 winner-removal, additive trade-boundary drawdown episodes, recovery and right-censoring, underwater trade counts and loss streaks. Counts are trades, not elapsed time. Existing pinned-detail historical_risk_envelope is unchanged.

Hand-calculated tests cover floor headroom, adverse beyond -1R, no Martingale, costs/sample alignment, seeded identity and stress, contiguous units/wrap/end censoring, regime recurrence, nonfinite config/R, exact horizon, drawdown recovery and negative-net concentration.

No actual pinned CAND-001 trade/path/cost ledger was found; no Candidate MAE/MFE/P99/ruin/profit number is claimed. Input source SHA is a caller pin, not independent byte validation; complete array/model/seed/label identity is hashed. Existing DetailArtifactPreflight remains the real ledger-byte owner. Exit/stop trailing/MAE/MFE hypotheses remain RESEARCH with conservative intrabar/outcome leakage constraints.
