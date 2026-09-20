# Supplementary methods

## Experiment map

The current unified physical-time experiments are specified in S13–S17; S22 provides the native-resolution policy-fee task and S23 the British operating and trading comparisons; S1–S5 preserve the earlier catalogue and representation experiments used by Tables S1–S43. In particular, the earlier native-grid Greek experiment in S5 and the harmonized 30-min Greek experiment in S13 are distinct experiments. S7 and S11 describe scenario-cost studies, whereas S17 describes observed-price settlement. S6 and S12 now distinguish the earlier 120-region review, the unused v15 collection design, and the received 320-window v19 reference. These experimental cohorts retain their own sampling, normalization and evaluation units. Table S0 gives a compact map from each section to its data, statistical unit, scientific purpose and main-text result; this prevents catalogue, transfer, synthetic and cost populations from being interpreted as one evaluation cohort.

### Table S0. Experiment map

| Section | Data and period | Analysis unit | Scientific purpose | Main-text link | Status in this manuscript |
|:--|:--|:--|:--|:--|:--|
| S1. Archive coverage | Seven archives; primary 2014–2025 periods and external 2020–2021 periods | Turbine × 30-min row; complete 25-point shape | Define eligible records, chronological splits and quality flags | 2.1; Methods 4.1 | Complete |
| S2. Detector protocols | Seven archives; 17 fixed configurations on the harmonized grid | Turbine × detector interval | Construct the protocol-dependent event objects | 2.1–2.2; Methods 4.2 | Complete |
| S3. Matching and summaries | Same archives, detector pairs and IoU thresholds 0.3/0.5/0.7 | One-to-one matched event pair | Measure structural survival together with left/right coverage | 2.2; Methods 4.3 | Complete |
| S4. Representation and perturbation | Pizhou training/holdout plus five-farm transfer; raw, PCA, statistics and angular representations | Event vector × partition | Quantify retained shape information and separate correspondence, order and attribute effects | 2.2–2.3; Methods 4.4 | Complete |
| S5. External representation transfer | Greek January–June 2020 and SDWPF 2020–2021 | Configuration pair × turbine/batch | Test whether frozen or local representations transfer across archives | 2.3 | Complete; support strata retained |
| S6. Human-reviewed regions | Legacy 120-region cohort and v19 eight-archive packet (320 windows × 3 observers) | Window × observer; detector presence per window | Provide an external event-presence and morphology reference | 2.6; Methods 4.6 | Three exports complete; one further review ongoing |
| S7. Forecasting and storage | Pizhou and Yandun chronological forecasts | Issue time × target interval × farm | Test event-aware forecasting and engineering cost scenarios | Supplementary cost context | Complete under stated scenario prices |
| S8. Controlled localization | Synthetic sequences with known episodes and fresh confirmation seeds | Sequence × injected episode | Measure event-level localization and delay under known truth | 2.6; Methods 4.7 | Complete |
| S9. Weather and post-event context | ERA5 panel, NOAA station comparison and Yandun sampling sensitivity | Time anchor × turbine; subsequent event window | Test external-process tracking and post-event association | 2.4 | Exploratory association; causal effect not estimated |
| S10. Table-reading convention | All result populations | Table row with an explicit unit and denominator | Keep structural, physical, forecast and cost estimands distinct | Methods 4.5 | Complete |
| S11. Policy-capacity scenario | Jiangsu-informed engineering scenarios on Pizhou and Yandun | Farm × test interval × storage design | Quantify policy-informed capacity and price sensitivities | Supplementary cost context | Scenario study; not a realized settlement replay |
| S12. Independent collection design | v15 packet specification and annotation interface | Window × observer response | Record provenance and the distinction from the received v19 exports | 2.6; Methods 4.6 | Design archived; received responses reported in S6 |
| S13. Protocol space and hierarchy | Seven archives on the v18 physical-time grid | Protocol tuple π × primitive/composite event | Formalize detection, matching, representation and evaluation layers | Introduction; Methods 4.1–4.3 | Complete |
| S14. Common support and information | Pizhou-fitted representations evaluated on site/configuration pairs | Matched pair × conditioning stratum | Estimate conditional partition information and metric sensitivity | 2.2–2.3 | Complete |
| S15. Physical-process probes | Five primary farms with regional weather targets | Event × site × weather class | Test whether retained shape information tracks an independent process | 2.3–2.4 | Complete for the archived association analysis |
| S16. Hill LiDAR chronology | Hill of Towie T07/T11, 2026 instrument release | Event × instrument × seven-day block | Chronologically test calibrated physical-process discrimination | 2.4 | Complete; instrument and block scope reported |
| S17. Forecast-to-cost replay | Hill of Towie 2020 and GB Elexon half-hour prices | Farm × half-hour settlement interval | Convert high-ramp forecast errors into observed-price exposure and storage replay | Supplementary cost context | GB price replay; native Jiangsu rule test in S22 |
| S18. Output and reproducibility | Versioned public repository and release artifacts | Artifact × protocol/result record | Bind code, tables, figures and validation records to reproducible paths | Data availability; Methods 4.8 | Versioned GitHub repository release |
| S19. Decision-aligned forecast extension | Hill of Towie existing forecast replay; 1/2/4-h horizons | Issue time × target interval × candidate model | Test whether event information can improve error and priced exposure under a fixed validation budget | Results 2.7; Table S56 | Exploratory extension; existing test calendar reused |
| S20. Metered correction | Hill 2020; 58 complete days | Half-hour × schedule × battery | Separate gross debit from signed settlement | Supplementary S23 | Ex-post capability |
| S21. Overlap correspondence | Eight structural populations | Connected overlap component | Resolve splitting, merging and composite episodes | 2.2; Methods 4.3 | Complete |
| S22. Native policy-fee test | Pizhou 2023–2025; held-out late calendar | Native 15-min target × issue horizon | Connect historical shape and issued weather to rule-based charges | 2.7; Methods 4.6 | Complete; 2022-rule simulation |
| S23. British full-income tests | Hill 2020–2021; Elexon prices and vintages | Operating day or scheduled interval | Distinguish exposure, net operating gain and trading income | Discussion; S17–S20 | All outcomes retained |

## S1. Archive coverage and source eligibility

The study contains seven archives and 333 turbines. The primary catalogue contains Pizhou (33), Suining (14), Yandun (117), La Haute Borne (4) and Hill of Towie (21). The Greek monitoring archive adds ten turbines, and SDWPF adds 134. Table 1 in the main text identifies their experimental roles.

A full primary-catalogue boundary check covers 1,984,249 candidate intervals and 1,538,376 complete shapes. All event timestamps agree with their source half-hour indices. Every eligible shape, including four samples before and after the event, remains within its assigned 60%/80% chronological period; the check finds zero boundary violations across 189 turbines.

| Primary site | Half-hour grid rows | Usable rows |
|:--|--:|--:|
| Pizhou | 823,680 | 507,047 |
| Suining | 245,952 | 173,437 |
| Yandun | 1,005,720 | 417,727 |
| La Haute Borne | 140,160 | 108,298 |
| Hill of Towie | 368,949 | 288,832 |

The primary catalogue uses source-specific complete-count eligibility flags. Each event and its context lie within one valid run and one chronological period. The split boundaries occur at 60% and 80% of elapsed archive time; event contexts crossing a boundary are excluded, so no morphology vector spans two splits. Primary amplitude scaling uses nameplate capacity where recorded and early-period q99.5 elsewhere. The data provider identifies the q99.5 upper production level as rated power for the applicable farms; event metadata retain the empirical scaling basis. One-minute Pizhou power records are averaged within each 30-min bin. Ten-minute and 15-min records use the corresponding valid-observation mean. A bin enters the catalogue when the required observations for its complete context are present.

The forecasting analysis uses a distinct signed-observation rule. Every turbine in the fixed fleet supplies the required native observation count. Accepted mean power lies between -5% and 120% of the recorded nameplate or early-period q99.5 scale. This rule retains small negative measurements and preserves the calendar grid.

## S2. Detector configurations

The seventeen primary configurations comprise threshold, financial-tail and mean-shift rules at one, two and four hours, three endpoint corridors, an adaptive corridor, SDA and three OpSDA configurations.

The fixed-change rules use a magnitude threshold of 0.20. The historical-tail rule uses the preceding 48 lagged differences, 5th and 95th percentiles, and a minimum magnitude of 0.10. The reference history ends before the current change. Same-direction overlapping detections are merged.

The fixed endpoint corridors use tolerances 0.025, 0.050 and 0.100. Their chord criterion closes a segment at the previous point when the next endpoint violates the constraint. Adaptive tolerance is fixed at segment start. It combines a 0.025 floor, scaled historical median absolute deviation and a local power-level term.

SDA uses the original boundary-crossing convention [@florita2013]. The conference OpSDA implementation merges eligible SDA segments by dynamic programming and a squared-length objective [@cui2015]. Door tolerance is 0.025 and amplitude threshold is 0.20.

## S3. Shapes, matching and summary units

Each complete shape has 4 + 17 + 4 coordinates: observed pre-event values, normalized event-time values, and observed post-event values. The vector is centered at event-start power and divided by its maximum absolute displacement. Duration, amplitude and other interval statistics remain separate fields.

Within each site, turbine and period, temporal IoU defines candidate correspondence. Greedy selection uses decreasing IoU, start separation and event identifiers. The primary event-matching threshold is 0.5. The additional support-overlap diagnostic tabulates the fraction of detector-occupancy comparisons exceeding 0.3, 0.5 and 0.7. Each event is assigned once per configuration pair. Counts refer separately to detector intervals, pair records and supported configuration comparisons. Pair-weighted NMI and ARI use matched-pair counts as weights. The machine-readable composition table compares events matched to at least one other configuration with events matched to none. It records amplitude, duration, direction, power range and starting power. Table S14 gives matched-count-weighted agreement and catalogue reach.

For event-level sensitivity, each configuration pair is rebuilt from interval endpoints at IoU cutoffs 0.3, 0.5 and 0.7. Greedy ties use start-time separation and event identifiers. Maximum-total-IoU assignment uses zero-reward dummy columns and negative reward for infeasible edges. ID-sorted matrices make repeated optimal assignments deterministic within the fixed solver implementation. All 1,465,997 greedy pairs at IoU 0.5 exactly reproduce the original event identifiers. Table S16 pools labels across turbines within each configuration pair, then reports equal-pair and matched-count-weighted summaries.

NMI uses arithmetic entropy normalization. ARI uses chance-adjusted pairwise partition agreement. Primary site summaries average configuration-pair scores equally. The learned-model site scores use within-site contingency tables. The cross-farm learned summary averages five farms equally and averages the three seeds. SDWPF uncertainty summaries retain seven computational batches within its single farm.

Table S1 contains the full primary representation summary. Table S2 gives the raw25 block-length sensitivity, including the number of occupied blocks and paired records.

The expanded composition analysis evaluates every detector pair and each of its two catalogue sides separately. It compares 526,276 eligible primary test events using duration, signed and absolute amplitude, power range, starting power, upward fraction and earlier turbine wind. Wind is the mean of four complete half-hour bins strictly preceding event start; duplicate source timestamps and incomplete wind bins are excluded. Detailed rows retain event counts, valid-feature counts and quartiles. Table S32 averages feature means over the same supported pair sides in both populations. This pair-specific comparison complements the historical union-of-any-match composition file.

The conditional agreement audit fits quartile boundaries for absolute amplitude, duration and starting power on the Pizhou training event IDs. Each statistic is then computed within a site, detector pair and covariate stratum. A matched pair enters a stratum when both event sides share its covariate code. One-side-constant partitions contribute zero NMI/ARI; both-constant partitions and strata with fewer than two pairs have undefined informative scores. Table S33 reports pair-weighted summaries over defined strata with at least thirty matches, along with the fraction of retained pairs represented by those scores. Temporal-match retention and left/right catalogue coverage have separate denominators. The joint-stratum analysis uses all four variables simultaneously. Its point summaries describe conditional partition agreement.

## S4. Representation fitting and perturbation analysis

Primary representation fitting uses eligible events from the first 26 sorted Pizhou turbines. Seven turbines form the primary holdout. Sampling uses at most 2,500 events per configuration, seed 41, six PCA components and twenty K-means initializations.

The fixed representations are raw25, raw-PCA6, statistics9, GAF-PCA6 and signed-GAF-PCA6. Statistics9 includes duration, signed amplitude, range, total variation, maximum rate, chord residual, curvature and pre/post means. The fixed signed-GAF representation appends the 25 signed coordinates to the flattened 625-value field.

Raw-PCA6 is a compression control for the same 25-point path. Across the three current Pizhou source fits it retains 93.4% of standardized training variance; same-event test partition ARI against raw25 ranges from 0.985 to 0.998. The earlier 0.989 pooled v5 value describes a separate historical experiment. Current cross-protocol comparisons use the frozen v18 models and common supported configuration pairs.

The learned image encoders use two convolutional layers and a six-dimensional latent vector. The signed version adds an orientation channel. TCN uses dilated one-dimensional convolutions. Transformer uses positional features and two attention layers. All four reconstruct the ordered trajectory. Input and latent standardization use the corresponding Pizhou training sample. The primary archived models use fifteen training epochs, validation reconstruction selection and seeds 41, 42 and 43. A completed 100-epoch, three-seed rerun uses the same data, transformations, latent dimension and early-stopping rule. Its assembled metrics are reported as the training-budget sensitivity in Table S12 and Figure 7. Parameter counts are 11,167, 11,311, 4,567 and 15,559 for CNN-GAF, signed-GAF, TCN and Transformer, respectively.

Row permutation reallocates complete event shapes within site and turbine. Coordinate permutation changes order within each event. Conditional comparisons use direction and training-defined amplitude, duration and pre-event-power bins. The complementary perturbations distinguish correspondence, order and coarse event attributes.

Calendar uncertainty uses 2,000 resamples with shared weights across turbines in the same block. Seven-day blocks define the primary estimate, and three- and fourteen-day blocks provide sensitivity checks. The 2.5th and 97.5th percentiles define pointwise intervals. Ten further Pizhou turbine splits use seeds 20260912 through 20260921.

## S5. External representation evaluation

The Greek archive contains ten turbines observed during January-June 2020 [@greece2024]. Its twelve base configurations operate on ten-minute samples with lags of two, four and eight points. The physical lags are twenty, forty and eighty minutes. Four source observations on each side provide forty minutes of context.

SDWPF contains 134 turbines observed during 2020-2021 [@sdwpfdata]. The external pipeline aggregates power to thirty-minute bins and applies the twelve base configurations. Seven batches divide the turbine list for computation. The complete archive has 11,361,190 source records and 134 location entries.

Both external catalogues use a turbine-wide q99.5 amplitude scale. Pizhou supplies the raw25 standardizer and centroids. Saved learned encoders, input scaling and latent scaling provide the SDWPF representations. Learned clusterers use saved Pizhou training latent vectors. The Greek local baseline fits standardization and k=4 K-means on Greek training shapes only, then evaluates the same 62 Greek test configuration pairs. This comparison changes the training population while retaining the event correspondence table.

The TCN adaptation comparison uses one source checkpoint (seed 41), the same 26 source fitting turbines, and the same 17,357 Greek test pairs. A second copy of the checkpoint receives five reconstruction-training epochs on Greek training shapes. Each encoder fits latent scaling and k=4 prototypes on the identical Pizhou training sample. Table S21 reports both models using identical pooled, equal-pair and matched-count-weighted metrics. Greek test shapes are used for evaluation.

Greek configuration pairs are grouped by support: 2-4, 5-9, 10-29, 30-99 and at least 100 matches. Table S3 reports every support stratum. The larger-support median is 0.669. Table S13 contains SDWPF batch-seed results for two, four and six clusters.

## S6. Human-reviewed regions and operating logs

### Earlier focused-region review

One researcher labeled thirty regions from each of Pizhou, Yandun, Greece and SDWPF. The first display provided twelve hours of context with a highlighted central two hours. The researcher identified the highlighted region as the principal target. A second display showed four hours and retained the same two-hour target for 52 refinements.

The merged labels contain 35 downward, 28 sustained-low, 24 upward, 14 V-shaped, 13 inverted-V and six quiet regions. Source submissions are retained separately. The second round supplies the final category for its 52 regions. The review record provides a region category and its display scope.

Catalogue agreement marks a region positive when a same-turbine detector interval overlaps its highlighted period. Precision divides positive-label hits by all flagged regions. Recall divides positive-label hits by all presence-positive regions. F1 summarizes their harmonic balance. Table S10 gives sampling support and Table S11 gives all configuration-level results. The sampling population contains 114 positive and six quiet labels.

Source-clock strings are parsed individually because the review table contains both naive and UTC-tagged timestamps. Every region has a finite anchor before catalogue intersection. The selected population and its clock convention remain attached to the reported metrics.

Greek logs provide generator, run, stop, yaw, reset and oil-flow context. The mapping retains 63,163 records. Event-start proximity uses thirty-minute, one-hour and four-hour neighborhoods within each turbine. The review windows also contain 2,336 source-clock log rows.

### Current eight-archive human reference

The v19 packet contains 320 four-hour windows, with 40 per archive from Pizhou, Suining, Yandun, La Haute Borne, Hill of Towie, Greece, SDWPF and SMARTEOLE. The rated region is the central two hours. Each of the first seven archives contributes 20 random and 20 detector-disagreement windows; the 40 SMARTEOLE windows come from its operating-period sample. Sampling source, detector outputs and other responses are hidden from each observer. The exported packet records presence, dominant morphology, assessability and an optional free-text note.

Three actual identifiers supplied 320 assessments each. R_147f4682 recorded 75 upward, 65 downward, 21 V, 22 inverted-V, 11 oscillatory, 75 quiet and 51 sustained-low regions (194 positive). R_2c332025 recorded 64 upward, 50 downward, 27 V, 21 inverted-V, 34 oscillatory, 104 quiet and 20 sustained-low regions (196 positive). R_29d247dd recorded 46 upward, 39 downward, 52 V, 64 inverted-V, 66 oscillatory, 42 quiet and 11 sustained-low regions (267 positive). All 960 responses were assessable. The exports supply region categories rather than start/end labels and are retained byte-for-byte. The earlier 120-region cohort remains separate.

Nominal Krippendorff’s alpha was 0.528 for presence and 0.476 for morphology. The three-way coincidence calculation retains all available ratings per window; missing ratings would remain missing rather than being imputed. Shared calendar resampling preserves the observer set within each sampled window. Seven-day 95% alpha intervals were 0.455–0.599 and 0.426–0.523. Pairwise Cohen kappa and disagreements are retained in the machine-readable agreement record, without an automatically generated consensus label.

Source recovery links each displayed power sequence to its original site, turbine and relative clock. For 280 inherited windows, missing display metadata were recovered through the original private sampling manifest and exact sequence equality. The 40 SMARTEOLE sequences were checked against the prepared source records at the displayed rounding precision. The distributed packet remains unchanged for additional observers. Absolute geographic clock claims are unnecessary for this within-archive comparison.

Each of the seventeen fixed configurations predicts presence if at least one basic detector interval overlaps the target region. Precision is TP/(TP+FP), recall is TP/(TP+FN), and F1 is 2TP/(2TP+FP+FN). Turning recovery additionally requires a matching V or inverted-V composite with its turning point inside the rated target. Multiple detections in a region count once for presence. This unit differs from the boundary-resolved one-to-one event evaluation in S8.

Aggregate estimates condition on the selected windows, with site and sampling-arm results supplied separately. For uncertainty, 2,000 resamples draw calendar blocks within each site, giving all windows and turbines in a sampled block the same multiplicity. Block lengths are 3, 7 and 14 days; paired detector differences share each draw. The primary seven-day analysis contains 197 occupied farm-blocks. The intervals condition on these observers; agreement was calculated on all 320 windows with three ratings. The packet contains no preassigned label-validation/test split, and none of the detector thresholds was tuned to these ratings. Tables S44–S47 report all three observers and all detector results; Table S54 reports agreement and its block sensitivity.

The received v19 assessment set now contains three observers. The third export is included in the agreement record, detector metrics and Tables S44–S47; all three ratings remain separate and no consensus label is created.

## S7. Forecasting and storage objectives

The forecasting experiment uses fixed fleets of 33 Pizhou turbines and 117 Yandun turbines. A 24-point half-hour history predicts the production interval ending one hour after issue. Each input interval is fully observed by issue time.

The chronological training/validation/test window counts are 6,813/3,173/3,549 in Pizhou and 1,847/375/1,525 in Yandun. Each retained context and target lies within one period and one continuous valid run. Persistence, TCN and TimesNet share the target timestamps.

The learned forecasters use seeds 41, 42 and 43 and up to twenty minibatch epochs. Validation MSE selects the checkpoint. The primary event-weighted training multiplies the squared error by four for training changes above the training q95 magnitude. A sensitivity series uses factors 0, 1, 2, 4 and 8 under the same data split, model, optimizer and event threshold. Factor is the incremental coefficient in 1 + factor × ramp_indicator, giving actual ramp weights 1, 2, 3, 5 and 9. The same observed history supplies every training variant at prediction time.

The capacity grid includes zero storage and twenty-five positive combinations. Power fractions are 0.01, 0.02, 0.04, 0.08 and 0.16. Energy durations are 0.5, 1, 2, 4 and 8 h. Validation selects capacity for each model and cost scenario.

Annual capacity costs are 350 CNY/kW and 1,100 CNY/kWh. Throughput costs 25 CNY/MWh. The low, base and high shortfall/surplus penalties are 150/40, 300/80 and 600/160 CNY/MWh. Results are expressed per one-MW-normalized production scale.

Dispatch uses a 0.92 round-trip efficiency, zero initial stock and zero terminal inventory credit. The calendar includes missing intervals, during which stored energy is carried forward. Capacity cost covers the full test span. Delivery penalties accrue on the common observed targets. Table S7 reports forecast error and Table S8 reports the selected scenario costs.

The paired forecast analysis resamples seven-day calendar blocks 2,000 times. Pizhou has fifteen occupied blocks and Yandun has five. Each bootstrap draw is shared across the fixed model seeds. Positive reported error gains mean lower error under event weighting.

## S8. Controlled episode localization

The generator produces 96-point sequences with smooth background variation and known finite episodes. It supplies 1,600 normal training sequences, 400 labeled validation sequences, 800 labeled test sequences and 800 higher-noise sensitivity sequences. Validation and test sets each contain equal numbers of positive and background sequences.

Episodes have amplitudes 0.08, 0.15, 0.30 or 0.50, positive or negative direction, and trapezoidal or smooth single-turn profiles. Rising/falling spans contain 2, 4, 8 or 16 points. Generator seeds are 9101, 9102, 9103 and 9104 for the four datasets.

TimesNet, KAN-AD, TCN-AE and positional-Transformer-AE reconstruct the normal training sequences [@wu2023timesnet; @zhou2025kanad]. Each run receives thirty full minibatch epochs and 750 parameter updates. Normal validation reconstruction selects a checkpoint. The three initialization seeds are 41, 42 and 43.

The default decision threshold is the training reconstruction-score q99. Threshold-only calibration searches nine validation-score quantiles. Complete protocol calibration also searches low/high ratios 1.0 and 0.5, merge gaps zero and two points, and minimum durations one and three points. Validation event F1 selects the settings.

Greedy one-to-one matching compares fully labeled episodes at IoU 0.3. IoU 0.1 and 0.5 provide sensitivity checks. Table S9 records every seed and decision protocol. Paired intervals resample whole generated sequences 2,000 times, with the same draws across the fixed trained seeds.

A 100-epoch upper-budget rerun uses the same generated sequences, model configurations and three seeds. Validation-only calibration selects the threshold and interval-grouping parameters. Table S22 reports its default and calibrated test F1, precision and recall together with optimizer steps.

The subsequent model-size search evaluates three configurations per neural model, each with seeds 41, 42 and 43 and a maximum of thirty epochs. TimesNet uses d_model 8, 16 and 32; KAN-AD uses Fourier orders 8, 16 and 32. Their learning rates are 0.0005, 0.001 and 0.001 respectively. The sequence autoencoders use (width, latent size, learning rate) combinations (8, 8, 0.0005), (16, 16, 0.001) and (32, 16, 0.001). Adam, batch size 64 and five-epoch early stopping follow the original implementation. Mean validation episode F1 across seeds selects each configuration. The analytic reference selects adjacent-mean windows of 2, 4, 8 or 16 points using validation F1; window 4 is selected. Every candidate uses the same threshold, hysteresis, merge-gap and minimum-duration search.

After selection, all checkpoints and output settings are frozen in the confirmation record. Generator seeds 2026091501 and 2026091502 then supply 1,600 fresh sequences each, half containing episodes. Innovation-noise standard deviations are 0.015 and 0.027; the autoregressive coefficient remains 0.65 and the event generator family is retained. The confirmation evaluates the frozen thresholds directly in both conditions. Tables S29–S30 report mean metrics, between-training-seed SD and 2,000 paired sequence-resampling intervals. The intervals condition on the fixed trained checkpoints; they quantify sequence-sampling variation.

Parameter counts use trainable model tensors and exclude positional and normalization buffers. CPU timing uses an AMD Ryzen 7 9700X under Ubuntu 24.04 / WSL2 with two torch threads. Five repeats follow one warm-up run of 800 sequences. Neural score batches contain 64 sequences; the analytic score uses vectorized NumPy cumulative sums. Table S31 reports normalization and score-generation time, with interval postprocessing excluded.

## S9. Weather and post-event context

The regional ERA5 exposure is an absolute 100-m wind-speed change of at least 1.5 m/s over three hours [@hersbach2020; @era5docs]. Weather timestamps use a fifteen-minute nearest-match tolerance. Outcomes record subsequent threshold-event starts within one, two or four hours.

The archived panel has 21,300 exposed and 84,761 unexposed records. The unadjusted risk differences are 0.0388, 0.0679 and 0.0863. NOAA station 580270 supplies a regional surface comparison with a ninety-minute match tolerance [@noaaisd]. Tables S4 and S5 show the observed risks and shifted-exposure contrasts. Table S15 adds 2,000 calendar-block resamples for 3-, 7- and 14-day blocks. Each resampled block carries all its turbine records, preserving within-block cross-turbine dependence. The main seven-day analysis occupies 31 ERA5 blocks and 27 NOAA blocks.

Yandun sampling sensitivity uses 15-, 30- and 60-min arithmetic-mean grids from the same native records. A four-hour physical lag is 16, 8 and 4 rows respectively; a one-hour lag is 4, 2 and 1. Every bin between the two endpoints is required to be valid. Table S17 reports eligible anchors, threshold-positive anchors and their ratio, both on each grid and at hourly clock times. These are anchor counts before event merging.

The post-event analysis retains 96 eligible events, with 17 exposed and 79 unexposed. Its scaled power-recovery index divides post-end power change by the pre-event-to-end amplitude and clips the index to [-2,2]. The exposed-minus-unexposed contrast is -0.390, with a seven-day block interval [-1.429,0.363]. The residual-power contrast is 191.0 source units with interval [-368.5,645.1]. Table S6 retains both estimates. Their interval widths describe the uncertainty in the recovery contrast.

The adjusted binomial model encodes the outcome numerically as 1 for a subsequent event. Exact joins obtain power, wind speed and direction at t−4 h and power change from t−5 h to t−4 h, preceding the exposure window [t−3 h,t]. Complete cases number 76,538, including 12,011 exposed and 64,527 unexposed records. The same cohort supplies the crude and standardized risk differences. Hour, month and turbine indicators accompany these covariates. Clustered covariance uses 31 seven-day blocks; delta-method intervals use a t critical value with 30 degrees of freedom. Coefficient tables also provide Benjamini–Hochberg adjusted q-values [@bh1995].

## S10. Reading the result tables

Each table identifies its measurement unit. NMI and ARI describe cluster correspondence. Coverage describes how much candidate support enters matching. Human-region precision and recall describe catalogue agreement with the reviewed sample. Synthetic F1 describes episode localization. Forecast nMAE describes error relative to training power scale. Scenario cost prices the corresponding errors under the listed rates.

The five-farm comparison, Greek external result, SDWPF external result, reviewed regions, controlled episodes and forecasting targets remain separate evaluation populations. Their complementary measurements form the evidence chain developed in the main text.

## S11. Policy-capacity storage experiment

The fixed baseline has battery power equal to 10% of wind-farm nameplate capacity and energy equal to two hours of battery power. The source is Jiangsu's 2023 market-connection policy [@jiangsu2023storage], applied here as a historical engineering scenario. The 2025 national tariff reform changes the role of compulsory storage [@ndrc2025market]. The Jiangsu rule supplies a historical engineering scenario. Yandun is an analogous Xinjiang archive, and the same technical design serves as an engineering comparator in this study.

Pizhou nameplate capacity is 87.45 MW according to the supplied data description; the sum of the 117 Yandun metadata capacities is 200.5 MW. Forecasts are converted from their original training-scale normalization to MW before dispatch. Costs are reported per installed MW over 2,496 test-calendar hours at Pizhou and 914 hours at Yandun, with missing intervals retained. These units differ from the earlier normalized-reference-MW tables.

The policy-capacity study reuses the original MSE models and the models with ramp sample weight four. The full capacity grid contains a zero-storage option and power fractions 0.05, 0.10 and 0.20 at durations 1, 2 and 4 h. Online dispatch charges during positive delivery deviations and discharges during negative deviations, with SOC limits 10%–90%, initial SOC 50% and round-trip efficiency 92%. Candidate reserve fractions are 0, 0.25 and 0.5 of usable energy; severe deviations above 20% of farm capacity release the reserve. Selection uses validation costs only. Terminal inventory is valued at an assumed 300 CNY/MWh, with initial inventory valued identically.

Assumed upfront power/energy costs are 350 CNY/kW and 1,100 CNY/kWh. A ten-year life and 8% discount rate give the capital-recovery factor; fixed annual maintenance is 2% of upfront cost. This replaces the earlier convention that treated those amounts as annual capacity charges. Shortfall/surplus prices are 150/40, 300/80 and 600/160 CNY/MWh. Additional premiums of 0, 1,000 and 5,000 CNY/MWh apply only to remaining deviations above 20% of installed wind capacity. These prices define scenario sensitivities; comparison with individual farm settlements remains a separate validation task.

The unconstrained design and the design requiring at least 10% power and 2 h duration are selected separately on validation records. A sparse linear program solves a perfect-information cost bound at fixed 10%/2 h capacity. It uses the complete realized residual path, so its cost is a perfect-information lower bound. The online policy uses validation-selected reserves and delivery-time deviations. Positive/negative-deviation-specific charging bounds prevent simultaneous charging and discharging. SOC conservation, feasibility and the oracle-versus-online inequality are checked in tests. Tables S23–S25 report the capacity-price surface, selected designs and cost bounds.

## S12. Independent multirater collection

This section records the earlier v15 collection design. The current submitted file was recognized by its internal v19 schema and packet identifier, despite its filename retaining the v15 prefix; its actual sampling and results are described in S6.

The v15 collection packet contains 200 real SCADA windows, with fifty from each of Pizhou, Yandun, Greece and SDWPF. Each site contributes twenty steady-screen, five rising-screen, five falling-screen, ten turning-screen and ten random-screen windows. These strata balance the sampling design; the human class distribution is determined by new responses. Four hours are displayed and only the central two hours are rated. Detector identities, sampling strata and earlier human answers are hidden in the interface.

Each participant uses an anonymous identifier and exports a versioned JSON file. Duplicate exports from the same identifier are merged by response timestamp; changed target regions are rejected. Cohen's kappa is calculated on shared assessable windows for each rater pair, and nominal Krippendorff alpha uses units with at least two available ratings. Uncertain and data-quality responses are tabulated separately. Constant-category cases return an undefined chance-corrected coefficient. Multirater coefficients will be calculated after independent responses are collected.

The collection interface is available at https://longjingpy.github.io/wind-power-event-protocol-audit/annotation/ . It works offline and stores answers locally. The v15 definition records sustained low production as a state and assigns transitions to their dynamic categories, so its responses remain distinct from the original v9 review labels.

## S13. v18 protocol space and event hierarchy

The v18 protocol is π=(Q,D,M,F,C), where Q specifies the observation clock, sampling, quality and amplitude calibration; D constructs intervals; M establishes correspondence; F encodes trajectories; and C assigns structure. The main grid is 30 min, with 60-, 120- and 240-min detector horizons, a 24-h historical window and 120-min context on each side. All transformations and scales are fitted on the chronological training population. The primary structural estimand is evaluated on matched, encodable events; weather and cost estimands use their eligible calendar populations.

Primitive detector intervals and composite V or inverted-V intervals are separate event levels. A composite joins opposite legs within 30 min and 240 min total duration, retains both child event IDs and stores the observed internal turning index. Primitive candidates describe detector intervals and orientation; they are not assumed to be monotonic physical trajectories.

## S14. v18 common-support matrix and conditional information

### Terminology and support units

An event pair consists of one interval from each detector configuration. A supported configuration pair contains at least 100 matched events; informative summaries additionally require nonconstant partitions. Coverage uses unique eligible events on each side. A nat is the natural-log information unit: 1 nat = 1/ln(2) bits. ARI is chance-adjusted partition agreement with 1 for identical partitions, 0 at the random-label expectation, and possible negative values.


For positive-duration intervals \(I_a=[s_a,e_a)\) and \(I_b=[s_b,e_b)\), let \(J=\max(0,\min(e_a,e_b)-\max(s_a,s_b))\) and \(U=(e_a-s_a)+(e_b-s_b)-J\). The intersection over union (IoU) is

\[
\operatorname{IoU}(I_a,I_b)=J/U,\qquad U>0.
\]

The implementation rejects zero-duration and reversed intervals (e≤s) before overlap calculation. A zero union is an invalid comparison and receives no score or edge. Empty catalogues contain no matches and their coverage is undefined; intervals touching only at an endpoint have IoU=0. For overlapping valid intervals, U equals the enclosing duration used by the implemented candidate-edge calculation. Matches share site, turbine, split and hierarchy. Greedy assignment sorts feasible edges by descending IoU with deterministic tie rules, using IoU ≥ 0.5. If N_a and N_b are the eligible event counts and M is the number of one-to-one matches, left and right coverage are M/N_a and M/N_b. Primary summaries use supported, informative configuration pairs common to all six representations and three seeds, first taking the median across seeds within each pair and then across pairs. ARI [@hubert1985] and normalized mutual information (NMI) quantify partition agreement. Constant partitions and pairs with fewer than 100 matches remain in separate support tables.

The common-support matrix intersects informative configuration pairs supported by raw25, statistics9, raw-PCA6, GAF-PCA6, signed-GAF-PCA6 and protected-polarity representations across seeds. Within a configuration pair, seed values are summarized by their median; site values are medians across the common intersection. The principal IoU threshold is 0.5; 0.3 and 0.7 are sensitivity values. Maximum-total-IoU assignment is an additional matching sensitivity. Pairs with fewer than 100 matches and constant partitions remain in the machine-readable output and are excluded from the primary informative median.

For matched partition labels \(L_a,L_b\) and conditioning stratum \(W\), conditional mutual information is \(I(L_a;L_b\mid W)=H(L_a\mid W)-H(L_a\mid L_b,W)\), using natural logarithms and empirical frequencies weighted by stratum size. The reported excess subtracts the mean of 100 within-stratum, within-turbine permutations. Individual descriptor analyses use training terciles; the joint analysis uses median splits of amplitude, duration and starting power together with both event directions. Cut points are fitted on Pizhou training events. Each stratum contains at least 30 matched pairs. Calendar uncertainty is reported separately from the permutation reference.

An additional metric analysis reuses the Pizhou-frozen K-means models with k=4 and seed 41 for raw25, GAF-PCA6 and protected-polarity GAF. Adjusted mutual information (AMI), Fowlkes–Mallows index and variation of information (VI) complement ARI and NMI. VI equals \(H(L_a)+H(L_b)-2I(L_a;L_b)\), in nats; lower values indicate closer partitions. All five metrics use identical basic-event test matches. Summaries intersect configuration pairs with at least 100 matches and nonconstant labels in all three representations, and then take the median over configurations. This single-seed, three-representation sensitivity has a different common-support intersection from the primary three-seed, six-representation analysis. Table S48 preserves that distinction.

## S15. v18 representation and physical-process probes

The primary analysis fixes K-means at k=4, with k=2 and k=6 sensitivities shown explicitly in Table S57. All three clustering algorithms retain their original training budgets. For the finite signed unit-domain vector x, set \(c_i=\sqrt{1-x_i^2}\ge0\). The Gramian angular summation field (GASF), the GAF variant used here, is \(G=xx^T-cc^T\) [@wang2015gaf], equivalent to \(G_{ij}=\cos(\arccos x_i+\arccos x_j)\). For an exact, uncompressed full field, its diagonal yields \(|x_i|=\sqrt{(G_{ii}+1)/2}\), and \(G+cc^T=xx^T\). Choose an anchor r with \(|x_r|>0\); the sign bit \(b=\operatorname{sgn}(x_r)\) gives \(x_r=b\sqrt{(G_{rr}+1)/2}\) and \(x_i=(G+cc^T)_{ir}/x_r\). The deterministic largest-magnitude anchor, with the first index breaking ties, is recoverable from the diagonal. The all-zero path is already determined, although constant supports are excluded by preprocessing. This recovers the normalized trajectory; restoring absolute power also requires its offset and scale. PCA retains only part of the field, so GAF/PCA5 plus polarity is an empirical six-dimensional representation, not an exact-inversion guarantee. It preserves the anchor sign explicitly and is evaluated on held-out clustering and physical targets.

The protected polarity coordinate contributes at most about 0.225% of the six-dimensional PCA variance in the primary fit. It therefore changes the physical-readout interface more strongly than the Euclidean cluster geometry. This is the reason the structural ARI of GAF+polarity can remain close to ordinary GAF while its external directional AUROC changes substantially.

Hourly ERA5 wind, temperature, pressure and related surface fields provide regional context for five geographically aligned archives [@hersbach2020; @era5docs]. The event-level physical target is \(\Delta u=u_{100}(e)-u_{100}(s)\), classified as decrease for \(\Delta u\le-1.5\) m s−1, increase for \(\Delta u\ge1.5\) m s−1, and small net change otherwise; event duration satisfies \(0<e-s\le4\) h. The ±1.5 m s−1 cutoffs are study-defined symmetric contrast levels, fixed for the regional probe before the later LiDAR transfer. They provide a common operational definition of a substantial endpoint wind-speed tendency, rather than a turbine cut-in/cut-out boundary or a universal meteorological ramp threshold. The four-hour limit matches the longest principal detector horizon and the composite-event window used in this study, focusing the probe on intraday dynamics. It does not require every wind change to span four hours: the same endpoint contrast may occur over a shorter event. A V-shaped excursion may return to small net change while retaining substantial internal variation, which is evaluated through event morphology and the overlap analysis. NOAA Integrated Surface Database (ISD) observations are archived with variable-level quality codes and precipitation accumulation duration [@noaaisd]; independent LiDAR supplies the local-wind test.

## S16. v18 Hill LiDAR confirmation and chronology

The Hill of Towie v2.1.0 release supplies 2026 Wind10 aggregates. T11 uses ZX300 unit 2428 horizontal speed near 58 m; T07 uses the available ZXTM unit 5060 fit-derived hub-height speed at 208 m. Positive packets and wind values in the physical range define valid measurements. Missing intervals remain missing. Endpoint clock offsets of −10, 0 and +10 min are reported. Frozen Hill-2020 physical heads and Pizhou representation transforms are applied before reading the 2026 scores.

A separate chronological calibration fits multinomial logistic calibration to source log probabilities. Calibration training ends before 14 March 2026, validation ends before 7 April and later events form the test period. Regularization C is selected from 0.1, 1 and 10 on validation. The field test reports AUROC, Brier score, signed log loss and seven-day block intervals. It is an external chronological probability test and does not change the frozen structural matrix.

## S17. v18 forecast-to-cost and storage replay

Elexon prices specify observed half-hour imbalance settlement [@elexonsettlement]. Here \(S_t\) is the experimental scheduled power position in MW for delivery interval t; its definition depends on the comparison. In the forecast-exposure experiment, \(S_t=\widehat P^{(m)}_{t\mid o}\) is model m's prediction issued at o. In the common-commitment storage experiment, every information arm shares the one-hour persistence schedule from the last completed observation; missing forecasts command zero desired correction while preserving inventory restoration. In the ex-post capability experiment, each model retains its own issued schedule across battery sizes, with persistence used where that model's forecast is unavailable. Thus schedules are fixed across capacities within a model, and shared across models only in the common-commitment arm. For metered delivery \(P_t\), interval duration \(\Delta t\) in hours, and buy/sell prices \(p_t^b,p_t^s\) in GBP MWh−1, the signed settlement cost is

\[
C_t=\max(S_t-P_t,0)\Delta t\,p_t^b-\max(P_t-S_t,0)\Delta t\,p_t^s.
\]

Hill aggregate power uses 21 turbines and a 48.3-MW reference capacity. Six information variants are persistence, power plus calendar, observed wind, historical event structure and two three-expert ramp mixtures. Event features become available at event end plus 150 min. Forecast horizons are 1, 2 and 4 h and target a 30-min interval. Elexon half-hour buy and sell prices score signed energy deviations. Gross debit is the positive part of the interval cashflow; net cashflow retains both deficit purchases and surplus settlement.

The common-commitment storage arm holds the persistence schedule fixed across information variants when an issued forecast is available; unavailable-forecast intervals use the documented zero-correction fallback. Battery power is 0%, 5%, 10% or 20% of fleet capacity, with two-hour energy capacity, 10–90% state-of-charge bounds, 50% initial and terminal inventory, and 0.92 charge/discharge efficiencies. The issued-forecast controller uses current inventory and a reachable terminal-inventory band; it does not use future power or future prices. Throughput sensitivities are 0, 10 and 30 GBP MWh−1. Validation selects capacity before the test replay.

The v20 Jiangsu duplicated-slot screen is a historical scenario recorded under `outputs/protocol_benchmark_v20/economics/jiangsu_counterfactual/`. It applies a medium/short-term allowance to simulated slots and does not evaluate the native ultra-short-term accuracy component. S22 supersedes it for that question using actual quarter-hour points and the 97%/87% rule. The French transfer design still requires historical RTE prices and a specified responsible-party perimeter. Table S55 separates these policy components.

## S18. Output and reproducibility map

The v18 event engine and unit-explicit economic functions are in `src/wind_events/`. Structural, physical, LiDAR, threshold, weather, forecast and storage outputs are under `outputs/protocol_benchmark_v18/`. Independent SVG, PDF, PNG and data-table sources are under `manuscript/figures_v18/`. The static support-aware benchmark index is under `outputs/protocol_benchmark_v18/leaderboard/`. The package wheel, isolated demo and unit tests are recorded under `outputs/protocol_benchmark_v18/package/`. The complete v18 input, transformation and evaluation record is `docs/V18_CURRENT_EXECUTION.md`.
The v19 manifest records the multirater and SMARTEOLE stages. Current v21/v22 representation, sampling and economic tables remain under their versioned output folders. The v23 extension adds `outputs/protocol_benchmark_v23/cluster_count_common_support.csv` and the `many_to_many/` directory: `configuration_pairs.csv`, `site_summary.csv`, `verification.json` and `coverage_aggregation_reconciliation.csv`. The last table verifies the equal-configuration versus pooled-coverage distinction against the original one-to-one counts. Supplementary Tables S57–S58 and Fig. S1 summarize these additions. The v24 native economic task adds Tables S59–S64, S22–S23 methods and the model-input replication bundle. The public v0.6.0 release mirrors aggregate outputs under `results/`, contains the current manuscript and editable Fig. 1, and links the de-identified processed-data release. The detailed local component ledger retains internal event clocks; public tables use aggregate counts. The SMARTEOLE support diagnostic remains `outputs/protocol_benchmark_v19/smarteole/diagnostic/report.json`, with the supported-row median, all-row and pair-weighted summaries.

## S19. Decision-aligned forecast extension

The extension fits residual power targets (future 30-min power minus issue-time power) using two feature arms: past weather and past weather plus frozen historical raw25 event features. The fixed candidate matrix crosses absolute- and squared-error losses, 7/15 leaf budgets, ramp weights 1/4 and persistence blends 0/0.25/0.5/0.75/1, giving 240 candidate predictions across 1-, 2- and 4-h horizons. Validation selects the primary nMAE candidate and a separate gross-debit candidate; no future prices or target power enter model actions. The test period is the previously used calendar and is labelled exploratory. Paired 3/7/14-day farm-block resampling supplies uncertainty. The 2-h event-aware selected model reduces gross debit by 16.51% relative to the legacy historical-event ramp mixture, with a seven-day interval of 11.39–22.31%; its nMAE reduction is 0.79 percentage points (0.40–1.22). Complete candidate rows, selections and effect intervals are under `outputs/protocol_benchmark_v20/economics/`.

## S20. Full settlement and online metered correction

The v22 economic extension is a separate 58-complete-day capability arm after the common-commitment forecast-only arm. It writes the battery action back to delivered power before applying the observed Elexon single-price settlement formula. Gross debit is the positive part of signed settlement cost, including negative-price periods; it is not the absolute sum of purchase and sale legs. The forecast-only arm keeps a persistence commitment, uses the issued forecast, current state of charge and a daily terminal-inventory constraint, and reports the capacity frontier for 0%, 5%, 10% and 20% of the 48.3-MW farm capacity. The separate ex-post capability arm uses the current half-hour power measurement in `planned_inventory_step`, includes settlement of the restoration actions required to return terminal inventory, and reports gross and signed settlement separately under the same 10–90% state-of-charge bounds. The buy-side and sell-side price columns are both present and identical in this archived calendar. The metered balance allows negative delivery when charging exceeds wind generation; this represents grid import. Extra export headroom and grid charging are assumed engineering permissions, and terminal-restoration actions are settled. It evaluates 1-, 2- and 4-h schedules and retains 3-, 7- and 14-day block intervals. At the two-hour horizon, the 20% battery paired with the selected weather-plus-event schedule reduces test gross debit from GBP 223,345 to GBP 162,784 (27.1%; seven-day block interval 23.95–30.73%) over 58 complete days; the accompanying signed settlement cashflow is GBP 57,195 before and GBP 71,075 after correction. Machine-readable outputs are `outputs/protocol_benchmark_v22/economics/capability_daily.csv`, `capability_frontier.csv` and `capability_intervals.csv`.

## S21. Many-to-many correspondence and hierarchy

The many-to-many extension builds a bipartite graph for each site, turbine, test split and configuration pair. All edges satisfying IoU ≥ 0.5 are retained, with 0.3/0.7 sensitivities. Connected components classify one-to-one, one-to-many, many-to-one and many-to-many correspondence. A primitive-only arm keeps the original event population; a hierarchy-inclusive arm allows primitive intervals to correspond to composite V/inverted-V episodes. Coverage counts unique connected nodes on each side, never edge multiplicity. Each component receives one vote when comparing label composition: if p_a and p_b are its four-class frequency vectors, composition overlap is sum_j min(p_aj,p_bj). This descriptive score preserves mixture proportions, while within-component temporal order is represented by the stored intervals and turning points. It is distinct from ARI. A separate containment sensitivity uses intersection/minimum duration ≥ 0.5, allowing a short leg to belong to a longer episode. Components longer than four hours remain explicitly counted as linked measurement supports. Shared seven-day calendar blocks anchor each component at its earliest start; 2,000 draws quantify conditional temporal variation. Per-event predictions use the frozen Pizhou raw25 k=4 seed-41 model.

Configuration names fix the left/right order lexicographically. A supported component pair contains at least 100 connected components; this count is descriptive and does not filter the all-configuration site summary. Site composition scores and topology proportions weight components equally across all 136 configuration pairs. Pooled coverage divides total unique connected nodes by total eligible nodes across those comparisons; an event can contribute once within each comparison. The main one-to-one coverage table instead averages the 136 configuration-specific fractions equally. An exact count reconciliation confirms identical primitive populations and one-to-one matches under both summaries (coverage_aggregation_reconciliation.csv).

## S22. Native-resolution rule-based accuracy-charge experiment

### Data, operational clock and weather inputs

The v24 cost experiment is a new task on the existing Pizhou archive. The two source batches contain 33 turbines and overlap by 90,720 minute records per turbine; overlapping power values were checked before merging. The provider-supplied capacity note reports 87.45 MW. Source times use Asia/Shanghai and are converted to UTC internally. The aggregate grid contains 49,920 quarter-hour timestamps and 48,206 complete target points. Target power is measured at the quarter-hour timestamp; input features use samples at least one minute before issue. Neither target values nor quarter-hour inputs are replicated from the main half-hour catalogue. Daily and monthly eligibility counts accompany the results. The chronological split ends training at 2024-07-08 16:00 UTC and validation at 2024-10-20 16:00 UTC. Test targets extend through 2025-02-01 15:45 UTC. Fifteen-minute and four-hour tests contain 9,450 and 9,345 eligible targets; models within a horizon share the same targets.

Causal prefixes comprise nine observations spanning two hours for the 15-min forecast and seventeen observations spanning four hours for the four-hour forecast. Interpolation produces 25 coordinates. These prefixes are wholly historical, in contrast to the event-centred 4+17+4 shapes used in structural and physical analyses. Shape encoders and standardizers are fitted on training prefixes, with a maximum of 10,000 training samples for representation fitting. Scalar descriptors include available power, the preceding 15-min mean, wind, range, total variation and calendar fields. The five feature arms are scalar only, raw25, raw/PCA6, GAF/PCA6 and GAF/PCA5 plus a protected sign coordinate; all representation arms also receive the common scalar descriptors.

Weather inputs use the Open-Meteo Previous Runs API, fixed previous_day1 forecasts from JMA GSM and GFS Global [@openmeteo_previous]. JMA 10-m wind covers the full September 2023–February 2025 study window (12,504 hourly values); GFS 100-m wind begins in February 2024 (8,466 values). Wind speed/direction are converted to u/v before time interpolation; missing hourly support is not bridged. The queried administrative proxy is 34.3403 degrees N, 118.0068 degrees E. The nominal fixed-lead vintages precede issue by at least 19 h 15 min, allowing for the upper hourly endpoint used to interpolate a quarter-hour target. These are archived forecast lead times rather than station-level receipt logs. Consecutive valid times may originate from different numerical-model cycles. Three arms use no numerical weather, JMA, or JMA plus GFS. Their test and validation targets are identical; GFS availability shortens its training support. Accordingly, weather-arm differences include both information and source-coverage effects. Source response files and their availability record are archived with the experiment.

### Prediction, selection and policy calculation

The probability model is an ExtraTrees classifier with 150 trees, maximum depth 16, seed 41 and minimum leaf sizes 8/32. Normalized power is binned in 0.01-capacity increments over the implemented 0–1.20 range. Candidate outputs are conditional mean, conditional median and the centre maximizing predictive mass in the admissible error band. Forecasts are blended with persistence using weights 0/0.25/0.5/0.75/1 and clipped to 0–1 nameplate capacity. Validation ranks failed-point count, then nMAE, then the smaller model weight. Five representations, two leaf sizes, three actions, five blends and two horizons produce 300 candidate rows per weather arm and 900 total correlated scoring rows. The primary and scalar-control selections across weather arms are saved in pipeline_selection_before_weather_test.json before the new weather test scores are read. The already examined no-weather task and the use of an existing research archive are retained in the experiment's exploratory identity. The nMAE-selected reference is a separate selection rule on the same candidate pool.

For a predictive distribution \(q_j\) over normalized power-bin centres \(y_j\), the band action was \(a^*=\arg\max_a\sum_jq_j\mathbf{1}\{|y_j-a|\le\tau\}\), evaluated over the implemented candidate values \(a\) at normalized tolerance \(\tau\). This action targets the expected number of failed accuracy points. The primary four-hour selection uses a median action, JMA/GFS inputs, protected-polarity angular coordinates, minimum leaf size 32 and model blend 0.75. The 15-min selection uses raw/PCA6, no numerical weather, minimum leaf size 8, median action and blend 0.75. The separate same-model action ablation uses no-weather raw25, leaf size 32 and blend 0.75; only conditional mean versus band action changes.

The policy source is the official Jiangsu 2022 No. 53, Article 44(II), printed pages 19–20 [@jiangsu2022accuracy]. Its ultra-short-term point accuracy is 100(1-|actual-forecast|/capacity); the qualification thresholds are 97% at 15 min and 87% at four hours. A failed point costs CNY 4 per 10 MW, or CNY 34.98 at 87.45 MW. Equality at the threshold qualifies. The medium/short-term 2% monthly allowance is not used for this distinct accuracy component. Costs aggregate the observed eligible points; exemptions, reporting failures and contractual purchase/sale income are outside this component. This is a 2022-rule simulation on the observed power calendar, not a reconstruction of a contemporaneous invoice.

Paired nonoverlapping calendar blocks are anchored to UTC epoch boundaries, with seven days primary and three/fourteen days as sensitivities. Two thousand multinomial block resamples preserve the model/baseline pair. The test occupies 35, 16 and 9 blocks, respectively. Intervals are percentile intervals of the relative fee reduction. They quantify temporal variation conditional on the selected training models; seeds 42 and 43 separately refit classifiers with the transformations and selected settings fixed. Sensitivity rescales the assumed capacity by 0.95/1/1.05 while preserving MW predictions. Discrete point charges can yield identical totals for distinct forecasts: the table of equal-fee pairs reports prediction equality and differing exceedance timestamps rather than interpreting a fee tie as duplicated data.

### Reproduction and relation to earlier cost experiments

Machine-readable results are under outputs/protocol_benchmark_v24/economics. Primary tables, all 3/7/14-day intervals, model-seed checks, ramp attribution and selection-objective comparisons are retained. The economic replication bundle includes de-identified model-input arrays, selected estimators, environment versions and six exact-output reproduction cases. It reproduces these model-level tests from transformed inputs; the private original-clock minute archive remains a distinct upstream preparation stage. The v20 duplicated-slot screen is superseded for the ultra-short-term question by this native point-level experiment. The historical screen remains a record of an earlier scenario, not evidence for the Article 44(II) charges.

## S23. British economic comparisons and the scope of monetary benefit

### Preserved observed-price and metered-correction results

The earlier main-text British forecast and storage results are retained here alongside their methods (S17 and S19–S20) and full tables (S51–S52 and S56). The original 2020 forecasting experiment evaluates persistence, power/calendar, completed turbine wind, historical raw25-cluster inputs and two ramp-mixture variants. At two hours, the matched historical-event addition changes nMAE from 14.69% to 14.47% and gross imbalance debits from GBP 292,263 to GBP 279,178. The later fixed-matrix extension reduces debits to GBP 233,084 on that reused test period. These are gross-exposure comparisons; signed settlement includes the associated credits. Figures S2–S4 retain the original ramp-concentration, forecast and storage views.

The common-commitment forecast-only controller selects zero additional storage on validation for every information arm. The separate 58-day, ex-post metered-correction arm reduces two-hour event-schedule gross debits from GBP 223,345 to GBP 162,784, while credits decrease from GBP 166,150 to GBP 91,709 and signed settlement cost rises from GBP 57,195 to GBP 71,075. This result concerns the stated controller, commitment and settlement service. It is not an estimate of whether a farm should own storage for all possible services. It remains part of the evidence rather than being reclassified as a net-profit gain.

### Forecast-only price-driven storage and complete trading income

The v24 wind-storage controller optimizes forecast operating revenue over a receding horizon. It can charge only from wind, respects an assumed 48.3-MW export limit, uses charge/discharge efficiencies of 0.92 and keeps SOC within 10–90%. Initial and terminal daily SOC are both 10%; inventory restoration is settled. Battery power is 0/5/10/20% of farm capacity with two-hour energy capacity. An explicit GBP 10 per MWh AC-throughput charge represents wear. Past price features respect a gate of max(publication time, interval end) plus five minutes; archived national WINDFOR vintages respect publication time plus five minutes. The latter is a national generation forecast rather than a local weather observation. Training ends before August 2020, validation uses the remaining specified 2020 calendar, and frozen settings are applied to 2021 January–June. Ninety-one complete eligible days enter scoring. Realized half-hour wind constrains physical wind-only charging and export after planning; future realized power and prices do not enter the planner.

For a battery power equal to 10% of farm capacity, the event-information arm gains GBP 5,986.77 relative to no storage after the assumed wear charge; the market-information arm gains GBP 7,168.89 and the weather arm GBP 6,413.51. At 20%, the corresponding gains are GBP 8,763.00, GBP 12,287.43 and GBP 11,503.57. These demonstrate operating gains for the tested assets; the event arm is not the best information arm. Capital costs and contractual service payments are separate investment quantities. The full per-day outcomes, capacity frontier and block intervals accompany the package.

A separate complete-income experiment includes market-index reference revenue, signed imbalance settlement and an assumed GBP 0.5/MWh scheduled trading fee. Forecasts and bounded schedule adjustments are selected on 2021 April–June validation, with July–December reserved for this test. The observed market index is an execution-price reference rather than a transaction record. Test revenue differences for the event arm relative to passive persistence are GBP -19,829.64, -21,721.27 and -26,310.43 at 1/2/4 h; weather-only differences are GBP -16,311.56, -22,117.41 and -25,991.07. These complete-income results prevent the gross-debit improvements from being interpreted as a general trading-profit advantage. They concern a different task, jurisdiction, period and objective from the positive Jiangsu accuracy-charge simulation.

## Supplementary result tables

### Table S1. Primary representation comparison (k = 4)

| Site/group | Representation | NMI | ARI | Agreement |
| --- | --- | --- | --- | --- |
| Hill of Towie | event row permutation | 0.024 | -0.007 | 0.366 |
| La Haute Borne | event row permutation | 0.067 | 0.023 | 0.402 |
| Pizhou | event row permutation | 0.055 | 0.025 | 0.367 |
| pizhou_seen | event row permutation | 0.048 | 0.022 | 0.370 |
| pizhou_unseen | event row permutation | 0.102 | 0.051 | 0.364 |
| Suining | event row permutation | 0.037 | -0.011 | 0.364 |
| Yandun | event row permutation | 0.026 | 0.006 | 0.340 |
| Hill of Towie | gaf pca6 | 0.272 | 0.242 | 0.567 |
| La Haute Borne | gaf pca6 | 0.301 | 0.238 | 0.574 |
| Pizhou | gaf pca6 | 0.273 | 0.252 | 0.556 |
| pizhou_seen | gaf pca6 | 0.275 | 0.248 | 0.560 |
| pizhou_unseen | gaf pca6 | 0.313 | 0.268 | 0.568 |
| Suining | gaf pca6 | 0.301 | 0.259 | 0.580 |
| Yandun | gaf pca6 | 0.269 | 0.254 | 0.563 |
| Hill of Towie | gaf signed pca6 | 0.276 | 0.245 | 0.568 |
| La Haute Borne | gaf signed pca6 | 0.289 | 0.234 | 0.575 |
| Pizhou | gaf signed pca6 | 0.275 | 0.255 | 0.558 |
| pizhou_seen | gaf signed pca6 | 0.277 | 0.251 | 0.562 |
| pizhou_unseen | gaf signed pca6 | 0.316 | 0.274 | 0.570 |
| Suining | gaf signed pca6 | 0.302 | 0.261 | 0.583 |
| Yandun | gaf signed pca6 | 0.271 | 0.259 | 0.567 |
| Hill of Towie | raw25 | 0.601 | 0.622 | 0.736 |
| La Haute Borne | raw25 | 0.698 | 0.687 | 0.776 |
| Pizhou | raw25 | 0.643 | 0.664 | 0.739 |
| pizhou_seen | raw25 | 0.651 | 0.674 | 0.747 |
| pizhou_unseen | raw25 | 0.682 | 0.684 | 0.751 |
| Suining | raw25 | 0.615 | 0.630 | 0.731 |
| Yandun | raw25 | 0.590 | 0.626 | 0.717 |
| Hill of Towie | raw pca6 | 0.597 | 0.618 | 0.734 |
| La Haute Borne | raw pca6 | 0.696 | 0.686 | 0.776 |
| Pizhou | raw pca6 | 0.639 | 0.660 | 0.736 |
| pizhou_seen | raw pca6 | 0.648 | 0.669 | 0.744 |
| pizhou_unseen | raw pca6 | 0.677 | 0.679 | 0.749 |
| Suining | raw pca6 | 0.614 | 0.629 | 0.729 |
| Yandun | raw pca6 | 0.588 | 0.624 | 0.716 |
| Hill of Towie | statistics9 | 0.474 | 0.453 | 0.742 |
| La Haute Borne | statistics9 | 0.475 | 0.517 | 0.819 |
| Pizhou | statistics9 | 0.518 | 0.500 | 0.742 |
| pizhou_seen | statistics9 | 0.514 | 0.493 | 0.746 |
| pizhou_unseen | statistics9 | 0.537 | 0.509 | 0.726 |
| Suining | statistics9 | 0.527 | 0.517 | 0.768 |
| Yandun | statistics9 | 0.473 | 0.482 | 0.743 |
| Hill of Towie | within event time permutation | 0.489 | 0.594 | 0.731 |
| La Haute Borne | within event time permutation | 0.601 | 0.660 | 0.749 |
| Pizhou | within event time permutation | 0.532 | 0.644 | 0.719 |
| pizhou_seen | within event time permutation | 0.536 | 0.648 | 0.727 |
| pizhou_unseen | within event time permutation | 0.572 | 0.651 | 0.725 |
| Suining | within event time permutation | 0.513 | 0.612 | 0.732 |
| Yandun | within event time permutation | 0.438 | 0.580 | 0.687 |


### Table S2. Raw25 block-length sensitivity

| Site/group | Days | Occupied blocks | Paired records | NMI [95% interval] |
| --- | --- | --- | --- | --- |
| Hill of Towie | 3 | 26 | 243684 | 0.601 [0.589, 0.628] |
| Hill of Towie | 7 | 12 | 243684 | 0.601 [0.592, 0.630] |
| Hill of Towie | 14 | 6 | 243684 | 0.601 [0.591, 0.639] |
| La Haute Borne | 3 | 45 | 34042 | 0.698 [0.690, 0.742] |
| La Haute Borne | 7 | 21 | 34042 | 0.698 [0.691, 0.744] |
| La Haute Borne | 14 | 12 | 34042 | 0.698 [0.696, 0.748] |
| Pizhou | 3 | 34 | 274570 | 0.643 [0.633, 0.676] |
| Pizhou | 7 | 16 | 274570 | 0.643 [0.631, 0.676] |
| Pizhou | 14 | 9 | 274570 | 0.643 [0.636, 0.667] |
| Suining | 3 | 24 | 102248 | 0.615 [0.615, 0.664] |
| Suining | 7 | 11 | 102248 | 0.615 [0.613, 0.663] |
| Suining | 14 | 6 | 102248 | 0.615 [0.613, 0.671] |
| Yandun | 3 | 15 | 811453 | 0.590 [0.567, 0.625] |
| Yandun | 7 | 7 | 811453 | 0.590 [0.574, 0.620] |
| Yandun | 14 | 4 | 811453 | 0.590 [0.576, 0.624] |
| pizhou_seen | 3 | 34 | 214524 | 0.651 [0.644, 0.684] |
| pizhou_seen | 7 | 16 | 214524 | 0.651 [0.647, 0.683] |
| pizhou_seen | 14 | 9 | 214524 | 0.651 [0.651, 0.677] |
| pizhou_unseen | 3 | 34 | 60046 | 0.682 [0.672, 0.725] |
| pizhou_unseen | 7 | 16 | 60046 | 0.682 [0.674, 0.728] |
| pizhou_unseen | 14 | 9 | 60046 | 0.682 [0.676, 0.723] |


### Table S3. Greek configuration-pair support strata

| Matches per pair | Configuration pairs | Median NMI | Minimum | Maximum |
| --- | --- | --- | --- | --- |
| 2-4 | 1 | 1.000 | 1.000 | 1.000 |
| 5-9 | 3 | 0.858 | 0.643 | 1.000 |
| 10-29 | 7 | 0.724 | 0.136 | 0.865 |
| 30-99 | 9 | 0.710 | 0.526 | 0.817 |
| >=100 | 42 | 0.669 | 0.385 | 0.961 |


### Table S4. Descriptive weather contrasts

| Source | Horizon (h) | Exposed n | Control n | Risk exposed | Risk control | Difference |
| --- | --- | --- | --- | --- | --- | --- |
| ERA5 | 1 | 21300 | 84761 | 0.230 | 0.191 | 0.039 |
| ERA5 | 2 | 21300 | 84761 | 0.398 | 0.331 | 0.068 |
| ERA5 | 4 | 21300 | 84761 | 0.572 | 0.486 | 0.086 |
| NOAA proxy | 1 | 41163 | 19668 | 0.201 | 0.202 | -0.001 |
| NOAA proxy | 2 | 41163 | 19668 | 0.350 | 0.342 | 0.009 |
| NOAA proxy | 4 | 41163 | 19668 | 0.514 | 0.492 | 0.022 |


### Table S5. Archived time-displacement diagnostics (4 h outcome)

| Displacement | Exposed n | Control n | Risk difference |
| --- | --- | --- | --- |
| shift-24h | 22083 | 83978 | -0.007 |
| shift-6h | 21603 | 84458 | 0.050 |
| shift+6h | 20159 | 85902 | 0.038 |
| shift+24h | 21409 | 84652 | -0.004 |


### Table S6. Scaled post-event power index and residual-power contrasts

| Measure | Events | Exposed minus control | 95% block interval |
| --- | --- | --- | --- |
| Absolute power response | 96 | 52.959 | [-347.182, 453.980] |
| Scaled post-event power index | 96 | -0.390 | [-1.429, 0.363] |
| Residual power | 96 | 191.034 | [-368.477, 645.136] |


### Table S7. Forecasts on common chronological targets

| Site | Model | Training | Subset | n | nMAE (%) |
| --- | --- | --- | --- | --- | --- |
| pizhou | persistence | none | all | 3549 | 7.754 |
| pizhou | persistence | none | training threshold ramp | 189 | 37.730 |
| pizhou | tcn | event weighted | all | 3549 | 8.413 |
| pizhou | tcn | event weighted | training threshold ramp | 189 | 33.186 |
| pizhou | tcn | mse | all | 3549 | 7.738 |
| pizhou | tcn | mse | training threshold ramp | 189 | 35.449 |
| pizhou | timesnet | event weighted | all | 3549 | 8.502 |
| pizhou | timesnet | event weighted | training threshold ramp | 189 | 35.507 |
| pizhou | timesnet | mse | all | 3549 | 7.771 |
| pizhou | timesnet | mse | training threshold ramp | 189 | 36.155 |
| yandun | persistence | none | all | 1525 | 7.424 |
| yandun | persistence | none | training threshold ramp | 78 | 38.868 |
| yandun | tcn | event weighted | all | 1525 | 9.724 |
| yandun | tcn | event weighted | training threshold ramp | 78 | 33.833 |
| yandun | tcn | mse | all | 1525 | 8.364 |
| yandun | tcn | mse | training threshold ramp | 78 | 36.515 |
| yandun | timesnet | event weighted | all | 1525 | 8.857 |
| yandun | timesnet | event weighted | training threshold ramp | 78 | 37.074 |
| yandun | timesnet | mse | all | 1525 | 7.735 |
| yandun | timesnet | mse | training threshold ramp | 78 | 36.698 |


### Table S8. Storage costs under the legacy annual-charge assumptions

| Site | Model | Training | Scenario | P (MW/MW) | E (MWh/MW) | Cost (CNY per norm. MW) |
| --- | --- | --- | --- | --- | --- | --- |
| pizhou | persistence | none | base | 0.000 | 0.000 | 25837.708 |
| pizhou | persistence | none | high | 0.000 | 0.000 | 51675.415 |
| pizhou | persistence | none | low | 0.000 | 0.000 | 12918.854 |
| pizhou | tcn | event weighted | base | 0.000 | 0.000 | 29630.118 |
| pizhou | tcn | event weighted | high | 0.000 | 0.000 | 59260.236 |
| pizhou | tcn | event weighted | low | 0.000 | 0.000 | 14815.059 |
| pizhou | tcn | mse | base | 0.000 | 0.000 | 25098.126 |
| pizhou | tcn | mse | high | 0.000 | 0.000 | 50196.252 |
| pizhou | tcn | mse | low | 0.000 | 0.000 | 12549.063 |
| pizhou | timesnet | event weighted | base | 0.000 | 0.000 | 26388.821 |
| pizhou | timesnet | event weighted | high | 0.000 | 0.000 | 52777.642 |
| pizhou | timesnet | event weighted | low | 0.000 | 0.000 | 13194.410 |
| pizhou | timesnet | mse | base | 0.000 | 0.000 | 24212.394 |
| pizhou | timesnet | mse | high | 0.000 | 0.000 | 48424.787 |
| pizhou | timesnet | mse | low | 0.000 | 0.000 | 12106.197 |
| yandun | persistence | none | base | 0.000 | 0.000 | 10751.779 |
| yandun | persistence | none | high | 0.000 | 0.000 | 21503.559 |
| yandun | persistence | none | low | 0.000 | 0.000 | 5375.890 |
| yandun | tcn | event weighted | base | 0.000 | 0.000 | 16643.238 |
| yandun | tcn | event weighted | high | 0.000 | 0.000 | 33286.477 |
| yandun | tcn | event weighted | low | 0.000 | 0.000 | 8321.619 |
| yandun | tcn | mse | base | 0.000 | 0.000 | 12661.780 |
| yandun | tcn | mse | high | 0.000 | 0.000 | 25323.560 |
| yandun | tcn | mse | low | 0.000 | 0.000 | 6330.890 |
| yandun | timesnet | event weighted | base | 0.000 | 0.000 | 12633.754 |
| yandun | timesnet | event weighted | high | 0.000 | 0.000 | 25267.507 |
| yandun | timesnet | event weighted | low | 0.000 | 0.000 | 6316.877 |
| yandun | timesnet | mse | base | 0.000 | 0.000 | 10648.952 |
| yandun | timesnet | mse | high | 0.000 | 0.000 | 21297.904 |
| yandun | timesnet | mse | low | 0.000 | 0.000 | 5324.476 |


### Table S9. Controlled synthetic event detection (IoU >= 0.3)

| Model | Seed | Policy | Precision | Recall | F1 |
| --- | --- | --- | --- | --- | --- |
| rate_rule | 0 | default | 0.056 | 0.210 | 0.088 |
| rate_rule | 0 | threshold only | 0.099 | 0.175 | 0.126 |
| rate_rule | 0 | full protocol | 0.439 | 0.435 | 0.437 |
| mean_rule | 0 | default | 0.255 | 0.752 | 0.381 |
| mean_rule | 0 | threshold only | 0.364 | 0.568 | 0.444 |
| mean_rule | 0 | full protocol | 0.742 | 0.740 | 0.741 |
| tcn_ae | 41 | default | 0.118 | 0.802 | 0.206 |
| tcn_ae | 41 | threshold only | 0.582 | 0.383 | 0.462 |
| tcn_ae | 41 | full protocol | 0.575 | 0.667 | 0.618 |
| tcn_ae | 42 | default | 0.118 | 0.810 | 0.206 |
| tcn_ae | 42 | threshold only | 0.557 | 0.365 | 0.441 |
| tcn_ae | 42 | full protocol | 0.584 | 0.657 | 0.619 |
| tcn_ae | 43 | default | 0.117 | 0.807 | 0.204 |
| tcn_ae | 43 | threshold only | 0.578 | 0.372 | 0.453 |
| tcn_ae | 43 | full protocol | 0.567 | 0.662 | 0.611 |
| transformer_ae | 41 | default | 0.064 | 0.640 | 0.116 |
| transformer_ae | 41 | threshold only | 0.398 | 0.330 | 0.361 |
| transformer_ae | 41 | full protocol | 0.833 | 0.425 | 0.563 |
| transformer_ae | 42 | default | 0.059 | 0.652 | 0.109 |
| transformer_ae | 42 | threshold only | 0.434 | 0.328 | 0.373 |
| transformer_ae | 42 | full protocol | 0.879 | 0.417 | 0.566 |
| transformer_ae | 43 | default | 0.060 | 0.645 | 0.110 |
| transformer_ae | 43 | threshold only | 0.379 | 0.310 | 0.341 |
| transformer_ae | 43 | full protocol | 0.828 | 0.432 | 0.568 |
| timesnet | 41 | default | 0.172 | 0.580 | 0.266 |
| timesnet | 41 | threshold only | 0.536 | 0.448 | 0.488 |
| timesnet | 41 | full protocol | 0.685 | 0.522 | 0.593 |
| timesnet | 42 | default | 0.195 | 0.610 | 0.296 |
| timesnet | 42 | threshold only | 0.522 | 0.438 | 0.476 |
| timesnet | 42 | full protocol | 0.729 | 0.537 | 0.619 |
| timesnet | 43 | default | 0.144 | 0.537 | 0.227 |
| timesnet | 43 | threshold only | 0.689 | 0.260 | 0.377 |
| timesnet | 43 | full protocol | 0.811 | 0.495 | 0.615 |
| kanad | 41 | default | 0.149 | 0.680 | 0.244 |
| kanad | 41 | threshold only | 0.464 | 0.305 | 0.368 |
| kanad | 41 | full protocol | 0.718 | 0.445 | 0.549 |
| kanad | 42 | default | 0.196 | 0.735 | 0.309 |
| kanad | 42 | threshold only | 0.455 | 0.455 | 0.455 |
| kanad | 42 | full protocol | 0.683 | 0.677 | 0.680 |
| kanad | 43 | default | 0.244 | 0.710 | 0.363 |
| kanad | 43 | threshold only | 0.668 | 0.477 | 0.557 |
| kanad | 43 | full protocol | 0.665 | 0.730 | 0.696 |


### Table S10. Human-review sampling support

| Site | Sampling stratum | Windows |
| --- | --- | --- |
| pizhou | downward | 6 |
| pizhou | upward | 6 |
| pizhou | low output | 6 |
| pizhou | screen disagreement | 6 |
| pizhou | random control | 6 |
| yandun | downward | 6 |
| yandun | upward | 6 |
| yandun | low output | 6 |
| yandun | screen disagreement | 6 |
| yandun | random control | 6 |
| greece | downward | 6 |
| greece | upward | 6 |
| greece | low output | 6 |
| greece | screen disagreement | 6 |
| greece | random control | 6 |
| sdwpf | downward | 6 |
| sdwpf | upward | 6 |
| sdwpf | low output | 6 |
| sdwpf | screen disagreement | 6 |
| sdwpf | random control | 6 |


### Table S11. Human-labelled centre-region detector agreement

| Site | Detector | Windows | TP | FP | FN | Precision | Recall | F1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| greece | Corridor 0.025 | 30 | 8 | 1 | 21 | 0.889 | 0.276 | 0.421 |
| greece | Corridor 0.050 | 30 | 13 | 1 | 16 | 0.929 | 0.448 | 0.605 |
| greece | Corridor 0.100 | 30 | 14 | 1 | 15 | 0.933 | 0.483 | 0.636 |
| greece | Tail 20 min | 30 | 15 | 1 | 14 | 0.938 | 0.517 | 0.667 |
| greece | Tail 40 min | 30 | 13 | 1 | 16 | 0.929 | 0.448 | 0.605 |
| greece | Tail 80 min | 30 | 19 | 1 | 10 | 0.950 | 0.655 | 0.776 |
| greece | Mean shift 20 min | 30 | 8 | 1 | 21 | 0.889 | 0.276 | 0.421 |
| greece | Mean shift 40 min | 30 | 14 | 1 | 15 | 0.933 | 0.483 | 0.636 |
| greece | Mean shift 80 min | 30 | 15 | 1 | 14 | 0.938 | 0.517 | 0.667 |
| greece | Threshold 20 min | 30 | 13 | 1 | 16 | 0.929 | 0.448 | 0.605 |
| greece | Threshold 40 min | 30 | 16 | 1 | 13 | 0.941 | 0.552 | 0.696 |
| greece | Threshold 80 min | 30 | 19 | 1 | 10 | 0.950 | 0.655 | 0.776 |
| pizhou | Adaptive corridor | 30 | 20 | 0 | 8 | 1.000 | 0.714 | 0.833 |
| pizhou | Corridor 0.025 | 30 | 17 | 0 | 11 | 1.000 | 0.607 | 0.756 |
| pizhou | Corridor 0.050 | 30 | 19 | 0 | 9 | 1.000 | 0.679 | 0.809 |
| pizhou | Corridor 0.100 | 30 | 20 | 0 | 8 | 1.000 | 0.714 | 0.833 |
| pizhou | Tail 1h | 30 | 3 | 0 | 25 | 1.000 | 0.107 | 0.194 |
| pizhou | Tail 2h | 30 | 3 | 0 | 25 | 1.000 | 0.107 | 0.194 |
| pizhou | Tail 4h | 30 | 2 | 0 | 26 | 1.000 | 0.071 | 0.133 |
| pizhou | Mean shift 1h | 30 | 17 | 1 | 11 | 0.944 | 0.607 | 0.739 |
| pizhou | Mean shift 2h | 30 | 18 | 2 | 10 | 0.900 | 0.643 | 0.750 |
| pizhou | Mean shift 4h | 30 | 18 | 1 | 10 | 0.947 | 0.643 | 0.766 |
| pizhou | OpSDA 1h 0.025 | 30 | 12 | 1 | 16 | 0.923 | 0.429 | 0.585 |
| pizhou | OpSDA 2h 0.025 | 30 | 16 | 1 | 12 | 0.941 | 0.571 | 0.711 |
| pizhou | OpSDA 4h 0.025 | 30 | 18 | 1 | 10 | 0.947 | 0.643 | 0.766 |
| pizhou | SDA 0.025 | 30 | 16 | 1 | 12 | 0.941 | 0.571 | 0.711 |
| pizhou | Threshold 1h | 30 | 20 | 1 | 8 | 0.952 | 0.714 | 0.816 |
| pizhou | Threshold 2h | 30 | 21 | 2 | 7 | 0.913 | 0.750 | 0.824 |
| pizhou | Threshold 4h | 30 | 20 | 2 | 8 | 0.909 | 0.714 | 0.800 |
| sdwpf | Corridor 0.025 | 30 | 6 | 0 | 23 | 1.000 | 0.207 | 0.343 |
| sdwpf | Corridor 0.050 | 30 | 12 | 0 | 17 | 1.000 | 0.414 | 0.585 |
| sdwpf | Corridor 0.100 | 30 | 16 | 0 | 13 | 1.000 | 0.552 | 0.711 |
| sdwpf | Tail 1h | 30 | 14 | 0 | 15 | 1.000 | 0.483 | 0.651 |
| sdwpf | Tail 2h | 30 | 14 | 0 | 15 | 1.000 | 0.483 | 0.651 |
| sdwpf | Tail 4h | 30 | 18 | 0 | 11 | 1.000 | 0.621 | 0.766 |
| sdwpf | Mean shift 1h | 30 | 18 | 0 | 11 | 1.000 | 0.621 | 0.766 |
| sdwpf | Mean shift 2h | 30 | 21 | 0 | 8 | 1.000 | 0.724 | 0.840 |
| sdwpf | Mean shift 4h | 30 | 20 | 0 | 9 | 1.000 | 0.690 | 0.816 |
| sdwpf | Threshold 1h | 30 | 19 | 0 | 10 | 1.000 | 0.655 | 0.792 |
| sdwpf | Threshold 2h | 30 | 20 | 0 | 9 | 1.000 | 0.690 | 0.816 |
| sdwpf | Threshold 4h | 30 | 24 | 0 | 5 | 1.000 | 0.828 | 0.906 |
| yandun | Adaptive corridor | 30 | 17 | 2 | 11 | 0.895 | 0.607 | 0.723 |
| yandun | Corridor 0.025 | 30 | 16 | 2 | 12 | 0.889 | 0.571 | 0.696 |
| yandun | Corridor 0.050 | 30 | 17 | 2 | 11 | 0.895 | 0.607 | 0.723 |
| yandun | Corridor 0.100 | 30 | 17 | 2 | 11 | 0.895 | 0.607 | 0.723 |
| yandun | Tail 1h | 30 | 14 | 2 | 14 | 0.875 | 0.500 | 0.636 |
| yandun | Tail 2h | 30 | 16 | 2 | 12 | 0.889 | 0.571 | 0.696 |
| yandun | Tail 4h | 30 | 19 | 2 | 9 | 0.905 | 0.679 | 0.776 |
| yandun | Mean shift 1h | 30 | 18 | 2 | 10 | 0.900 | 0.643 | 0.750 |
| yandun | Mean shift 2h | 30 | 22 | 2 | 6 | 0.917 | 0.786 | 0.846 |
| yandun | Mean shift 4h | 30 | 25 | 2 | 3 | 0.926 | 0.893 | 0.909 |
| yandun | OpSDA 1h 0.025 | 30 | 11 | 2 | 17 | 0.846 | 0.393 | 0.537 |
| yandun | OpSDA 2h 0.025 | 30 | 15 | 2 | 13 | 0.882 | 0.536 | 0.667 |
| yandun | OpSDA 4h 0.025 | 30 | 19 | 2 | 9 | 0.905 | 0.679 | 0.776 |
| yandun | SDA 0.025 | 30 | 17 | 2 | 11 | 0.895 | 0.607 | 0.723 |
| yandun | Threshold 1h | 30 | 18 | 2 | 10 | 0.900 | 0.643 | 0.750 |
| yandun | Threshold 2h | 30 | 21 | 2 | 7 | 0.913 | 0.750 | 0.824 |
| yandun | Threshold 4h | 30 | 25 | 2 | 3 | 0.926 | 0.893 | 0.909 |


### Table S12. Learned representations by farm, averaged over three seeds (k = 4)

| Representation | Farm | NMI | ARI |
| --- | --- | --- | --- |
| cnn gaf | Hill of Towie | 0.199 | 0.305 |
| cnn gaf | La Haute Borne | 0.183 | 0.280 |
| cnn gaf | Pizhou | 0.193 | 0.289 |
| cnn gaf | Suining | 0.194 | 0.295 |
| cnn gaf | Yandun | 0.210 | 0.308 |
| cnn signed gaf | Hill of Towie | 0.695 | 0.807 |
| cnn signed gaf | La Haute Borne | 0.739 | 0.836 |
| cnn signed gaf | Pizhou | 0.732 | 0.832 |
| cnn signed gaf | Suining | 0.713 | 0.815 |
| cnn signed gaf | Yandun | 0.667 | 0.786 |
| tcn | Hill of Towie | 0.719 | 0.815 |
| tcn | La Haute Borne | 0.763 | 0.840 |
| tcn | Pizhou | 0.754 | 0.840 |
| tcn | Suining | 0.744 | 0.834 |
| tcn | Yandun | 0.689 | 0.787 |
| transformer | Hill of Towie | 0.691 | 0.756 |
| transformer | La Haute Borne | 0.729 | 0.774 |
| transformer | Pizhou | 0.722 | 0.781 |
| transformer | Suining | 0.705 | 0.767 |
| transformer | Yandun | 0.659 | 0.745 |


### Table S13. SDWPF learned-model transfer across seven batches and three seeds

| Representation | k | Runs | Mean NMI | SD NMI | Mean ARI |
| --- | --- | --- | --- | --- | --- |
| tcn | 2 | 21 | 0.856 | 0.043 | 0.918 |
| tcn | 4 | 21 | 0.626 | 0.076 | 0.693 |
| tcn | 6 | 21 | 0.520 | 0.006 | 0.493 |
| transformer | 2 | 21 | 0.848 | 0.041 | 0.913 |
| transformer | 4 | 21 | 0.589 | 0.049 | 0.651 |
| transformer | 6 | 21 | 0.521 | 0.009 | 0.516 |


### Table S14. Matched-count-weighted agreement and detector-occupancy overlap

| Site | Weighted NMI | Weighted ARI | Pairs | Left cov. | Right cov. | IoU >= 0.3 | IoU >= 0.5 | IoU >= 0.7 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Hill of Towie | 0.684 | 0.738 | 243684 | 0.384 | 0.352 | 0.754 | 0.218 | 0.014 |
| La Haute Borne | 0.754 | 0.781 | 34042 | 0.356 | 0.340 | 0.445 | 0.071 | 0.000 |
| Pizhou | 0.722 | 0.782 | 274570 | 0.375 | 0.326 | 0.783 | 0.260 | 0.043 |
| Suining | 0.705 | 0.765 | 102248 | 0.381 | 0.348 | 0.784 | 0.240 | 0.029 |
| Yandun | 0.671 | 0.727 | 811453 | 0.370 | 0.368 | 0.548 | 0.261 | 0.080 |


### Table S15. Observational weather contrasts with shared calendar-block intervals

| Source | Horizon (h) | Block days | Blocks | Risk difference | 95% interval |
| --- | --- | --- | --- | --- | --- |
| ERA5 | 1 | 3 | 73 | 0.039 | [0.016, 0.062] |
| ERA5 | 1 | 7 | 31 | 0.039 | [0.014, 0.064] |
| ERA5 | 1 | 14 | 16 | 0.039 | [0.014, 0.061] |
| ERA5 | 2 | 3 | 73 | 0.068 | [0.036, 0.100] |
| ERA5 | 2 | 7 | 31 | 0.068 | [0.029, 0.107] |
| ERA5 | 2 | 14 | 16 | 0.068 | [0.033, 0.099] |
| ERA5 | 4 | 3 | 73 | 0.086 | [0.045, 0.124] |
| ERA5 | 4 | 7 | 31 | 0.086 | [0.040, 0.134] |
| ERA5 | 4 | 14 | 16 | 0.086 | [0.041, 0.125] |
| NOAA | 1 | 3 | 59 | -0.001 | [-0.028, 0.026] |
| NOAA | 1 | 7 | 27 | -0.001 | [-0.030, 0.027] |
| NOAA | 1 | 14 | 14 | -0.001 | [-0.027, 0.026] |
| NOAA | 2 | 3 | 59 | 0.009 | [-0.034, 0.050] |
| NOAA | 2 | 7 | 27 | 0.009 | [-0.037, 0.054] |
| NOAA | 2 | 14 | 14 | 0.009 | [-0.037, 0.053] |
| NOAA | 4 | 3 | 59 | 0.022 | [-0.029, 0.072] |
| NOAA | 4 | 7 | 27 | 0.022 | [-0.038, 0.080] |
| NOAA | 4 | 14 | 14 | 0.022 | [-0.033, 0.077] |


### Table S16. Event-level IoU and matching-strategy sensitivity

| Site | IoU | Matcher | Pairs | NMI | ARI | W. NMI | W. ARI | Left cov. | Right cov. |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Hill of Towie | 0.3 | Greedy | 307826 | 0.533 | 0.567 | 0.629 | 0.682 | 0.468 | 0.437 |
| Hill of Towie | 0.3 | Max. IoU | 308389 | 0.526 | 0.561 | 0.620 | 0.676 | 0.469 | 0.438 |
| Hill of Towie | 0.5 | Greedy | 243684 | 0.601 | 0.622 | 0.684 | 0.738 | 0.353 | 0.324 |
| Hill of Towie | 0.5 | Max. IoU | 243833 | 0.595 | 0.617 | 0.677 | 0.734 | 0.353 | 0.324 |
| Hill of Towie | 0.7 | Greedy | 111656 | 0.763 | 0.747 | 0.892 | 0.908 | 0.164 | 0.133 |
| Hill of Towie | 0.7 | Max. IoU | 111656 | 0.763 | 0.747 | 0.892 | 0.908 | 0.164 | 0.133 |
| La Haute Borne | 0.3 | Greedy | 43890 | 0.638 | 0.632 | 0.707 | 0.728 | 0.430 | 0.416 |
| La Haute Borne | 0.3 | Max. IoU | 43921 | 0.638 | 0.637 | 0.705 | 0.728 | 0.430 | 0.416 |
| La Haute Borne | 0.5 | Greedy | 34042 | 0.698 | 0.687 | 0.754 | 0.781 | 0.327 | 0.312 |
| La Haute Borne | 0.5 | Max. IoU | 34055 | 0.697 | 0.688 | 0.753 | 0.781 | 0.327 | 0.312 |
| La Haute Borne | 0.7 | Greedy | 16527 | 0.858 | 0.849 | 0.899 | 0.914 | 0.162 | 0.139 |
| La Haute Borne | 0.7 | Max. IoU | 16527 | 0.858 | 0.849 | 0.899 | 0.914 | 0.162 | 0.139 |
| Pizhou | 0.3 | Greedy | 348190 | 0.582 | 0.615 | 0.672 | 0.731 | 0.473 | 0.419 |
| Pizhou | 0.3 | Max. IoU | 348609 | 0.578 | 0.612 | 0.667 | 0.729 | 0.474 | 0.419 |
| Pizhou | 0.5 | Greedy | 274570 | 0.643 | 0.664 | 0.722 | 0.782 | 0.350 | 0.305 |
| Pizhou | 0.5 | Max. IoU | 274716 | 0.639 | 0.662 | 0.718 | 0.780 | 0.350 | 0.305 |
| Pizhou | 0.7 | Greedy | 125508 | 0.814 | 0.807 | 0.892 | 0.914 | 0.161 | 0.124 |
| Pizhou | 0.7 | Max. IoU | 125508 | 0.814 | 0.807 | 0.892 | 0.914 | 0.161 | 0.124 |
| Suining | 0.3 | Greedy | 128928 | 0.548 | 0.583 | 0.650 | 0.712 | 0.462 | 0.430 |
| Suining | 0.3 | Max. IoU | 129077 | 0.542 | 0.577 | 0.645 | 0.707 | 0.463 | 0.430 |
| Suining | 0.5 | Greedy | 102248 | 0.615 | 0.630 | 0.705 | 0.765 | 0.350 | 0.320 |
| Suining | 0.5 | Max. IoU | 102293 | 0.612 | 0.628 | 0.700 | 0.762 | 0.350 | 0.320 |
| Suining | 0.7 | Greedy | 47316 | 0.794 | 0.798 | 0.899 | 0.918 | 0.163 | 0.132 |
| Suining | 0.7 | Max. IoU | 47316 | 0.794 | 0.798 | 0.899 | 0.917 | 0.163 | 0.132 |
| Yandun | 0.3 | Greedy | 1082770 | 0.522 | 0.570 | 0.610 | 0.662 | 0.479 | 0.484 |
| Yandun | 0.3 | Max. IoU | 1085302 | 0.512 | 0.560 | 0.598 | 0.652 | 0.481 | 0.485 |
| Yandun | 0.5 | Greedy | 811453 | 0.590 | 0.626 | 0.671 | 0.727 | 0.351 | 0.349 |
| Yandun | 0.5 | Max. IoU | 812076 | 0.581 | 0.618 | 0.661 | 0.720 | 0.351 | 0.350 |
| Yandun | 0.7 | Greedy | 353527 | 0.763 | 0.778 | 0.867 | 0.886 | 0.157 | 0.139 |
| Yandun | 0.7 | Max. IoU | 353527 | 0.763 | 0.777 | 0.867 | 0.886 | 0.157 | 0.139 |

Max. IoU denotes maximum-total-IoU assignment. NMI and ARI are equal-configuration-pair means over pairs with matched events; W. NMI and W. ARI are weighted by matched-event counts. Left and right coverage are mean matched fractions of the respective detector catalogues across all configuration pairs.


### Table S17. Yandun physical-horizon and sampling sensitivity

| Minutes | Horizon (h) | Clock | Eligible anchors | Positive anchors | Positive rate |
| --- | --- | --- | --- | --- | --- |
| 15 | 1 | common hourly clock | 196458 | 38174 | 0.194 |
| 15 | 1 | native grid | 785688 | 152383 | 0.194 |
| 15 | 4 | common hourly clock | 165650 | 59359 | 0.358 |
| 15 | 4 | native grid | 662573 | 237724 | 0.359 |
| 30 | 1 | common hourly clock | 194166 | 34850 | 0.179 |
| 30 | 1 | native grid | 388019 | 69862 | 0.180 |
| 30 | 4 | common hourly clock | 164112 | 57838 | 0.352 |
| 30 | 4 | native grid | 328086 | 116004 | 0.354 |
| 60 | 1 | common hourly clock | 188305 | 28732 | 0.153 |
| 60 | 1 | native grid | 188305 | 28732 | 0.153 |
| 60 | 4 | common hourly clock | 160194 | 55441 | 0.346 |
| 60 | 4 | native grid | 160194 | 55441 | 0.346 |


### Table S18. Event-weight sensitivity under the legacy annual-charge assumptions

| Site | Factor | Ramp weight | All nMAE (%) | Ramp nMAE (%) | Base cost |
| --- | --- | --- | --- | --- | --- |
| pizhou | 0 | 1 | 7.738 | 35.449 | 25098.126 |
| pizhou | 1 | 2 | 7.842 | 34.405 | 25973.479 |
| pizhou | 2 | 3 | 7.974 | 33.759 | 25931.902 |
| pizhou | 4 | 5 | 8.629 | 32.570 | 30883.870 |
| pizhou | 8 | 9 | 10.284 | 31.794 | 36692.052 |
| yandun | 0 | 1 | 8.364 | 36.515 | 12661.780 |
| yandun | 1 | 2 | 8.830 | 35.491 | 14184.366 |
| yandun | 2 | 3 | 9.154 | 34.723 | 15004.582 |
| yandun | 4 | 5 | 10.084 | 33.212 | 17460.744 |
| yandun | 8 | 9 | 11.705 | 30.846 | 21481.776 |


### Table S19. Adjusted weather association model

| Records | Blocks | Risk difference | 95% interval | Odds ratio | OR interval |
| --- | --- | --- | --- | --- | --- |
| 76538 | 31 | 0.074 | [0.023, 0.125] | 1.394 | [1.103, 1.762] |


### Table S20. Greek local-training and frozen-transfer comparison

| Training population | Config. pairs | NMI | ARI | Agreement |
| --- | --- | --- | --- | --- |
| Greek local | 62 | 0.596 | 0.536 | 0.668 |
| Pizhou frozen | 62 | 0.679 | 0.662 | 0.767 |


### Table S21. Same-encoder Greek frozen and adapted TCN comparison

| Mode | Pairs | Equal NMI | Equal ARI | Pooled NMI | Pooled ARI | Weighted NMI | Weighted ARI |
| --- | --- | --- | --- | --- | --- | --- | --- |
| frozen | 17357 | 0.625 | 0.614 | 0.547 | 0.596 | 0.607 | 0.628 |
| target finetuned | 17357 | 0.629 | 0.624 | 0.552 | 0.609 | 0.611 | 0.639 |


### Table S22. 100-epoch upper-budget controlled detection sensitivity

| Model | Protocol | Precision | Recall | F1 | Optimizer steps |
| --- | --- | --- | --- | --- | --- |
| kanad | calibrated | 0.706 | 0.632 | 0.657 | 1725.000 |
| kanad | default | 0.181 | 0.740 | 0.289 | 1725.000 |
| mean_rule | calibrated | 0.742 | 0.740 | 0.741 | 0.000 |
| mean_rule | default | 0.255 | 0.752 | 0.381 | 0.000 |
| rate_rule | calibrated | 0.439 | 0.435 | 0.437 | 0.000 |
| rate_rule | default | 0.056 | 0.210 | 0.088 | 0.000 |
| tcn_ae | calibrated | 0.583 | 0.397 | 0.465 | 2425.000 |
| tcn_ae | default | 0.068 | 0.542 | 0.121 | 2425.000 |
| timesnet | calibrated | 0.760 | 0.533 | 0.623 | 1841.667 |
| timesnet | default | 0.135 | 0.578 | 0.219 | 1841.667 |
| transformer_ae | calibrated | 0.814 | 0.363 | 0.501 | 1975.000 |
| transformer_ae | default | 0.050 | 0.499 | 0.091 | 1975.000 |


### Table S23. Fixed 10%-power and 2-hour storage costs normalized by test-calendar hours

| Site | Model | Prices | Tail premium | Calendar h | MSE CNY/MW/h | Event-weighted CNY/MW/h | Difference |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pizhou | tcn | base | 0.0 | 2496.000 | 11.490 | 13.782 | 2.292 |
| pizhou | tcn | base | 1000.0 | 2496.000 | 15.360 | 17.577 | 2.217 |
| pizhou | tcn | base | 5000.0 | 2496.000 | 30.840 | 32.685 | 1.845 |
| pizhou | tcn | high | 0.0 | 2496.000 | 17.521 | 22.169 | 4.649 |
| pizhou | tcn | high | 1000.0 | 2496.000 | 21.391 | 25.878 | 4.487 |
| pizhou | tcn | high | 5000.0 | 2496.000 | 36.871 | 40.916 | 4.045 |
| pizhou | tcn | low | 0.0 | 2496.000 | 8.474 | 9.588 | 1.114 |
| pizhou | tcn | low | 1000.0 | 2496.000 | 12.344 | 13.335 | 0.991 |
| pizhou | tcn | low | 5000.0 | 2496.000 | 27.824 | 28.390 | 0.566 |
| pizhou | timesnet | base | 0.0 | 2496.000 | 11.102 | 12.181 | 1.079 |
| pizhou | timesnet | base | 1000.0 | 2496.000 | 16.022 | 18.251 | 2.229 |
| pizhou | timesnet | base | 5000.0 | 2496.000 | 35.700 | 42.532 | 6.832 |
| pizhou | timesnet | high | 0.0 | 2496.000 | 16.742 | 18.925 | 2.183 |
| pizhou | timesnet | high | 1000.0 | 2496.000 | 21.661 | 24.995 | 3.334 |
| pizhou | timesnet | high | 5000.0 | 2496.000 | 41.339 | 49.276 | 7.937 |
| pizhou | timesnet | low | 0.0 | 2496.000 | 8.282 | 8.808 | 0.526 |
| pizhou | timesnet | low | 1000.0 | 2496.000 | 13.202 | 14.879 | 1.677 |
| pizhou | timesnet | low | 5000.0 | 2496.000 | 32.880 | 39.160 | 6.280 |
| yandun | tcn | base | 0.0 | 914.000 | 14.675 | 19.834 | 5.159 |
| yandun | tcn | base | 1000.0 | 914.000 | 19.627 | 24.137 | 4.511 |
| yandun | tcn | base | 5000.0 | 914.000 | 39.434 | 41.352 | 1.918 |
| yandun | tcn | high | 0.0 | 914.000 | 23.764 | 34.207 | 10.443 |
| yandun | tcn | high | 1000.0 | 914.000 | 28.716 | 38.511 | 9.795 |
| yandun | tcn | high | 5000.0 | 914.000 | 48.523 | 55.726 | 7.202 |
| yandun | tcn | low | 0.0 | 914.000 | 10.130 | 12.647 | 2.516 |
| yandun | tcn | low | 1000.0 | 914.000 | 15.082 | 16.951 | 1.868 |
| yandun | tcn | low | 5000.0 | 914.000 | 34.889 | 34.165 | -0.724 |
| yandun | timesnet | base | 0.0 | 914.000 | 12.060 | 14.501 | 2.441 |
| yandun | timesnet | base | 1000.0 | 914.000 | 17.453 | 21.762 | 4.309 |
| yandun | timesnet | base | 5000.0 | 914.000 | 39.027 | 51.347 | 12.320 |
| yandun | timesnet | high | 0.0 | 914.000 | 18.469 | 23.394 | 4.925 |
| yandun | timesnet | high | 1000.0 | 914.000 | 23.863 | 30.655 | 6.793 |
| yandun | timesnet | high | 5000.0 | 914.000 | 45.437 | 60.427 | 14.991 |
| yandun | timesnet | low | 0.0 | 914.000 | 8.855 | 10.055 | 1.199 |
| yandun | timesnet | low | 1000.0 | 914.000 | 14.249 | 17.456 | 3.208 |
| yandun | timesnet | low | 5000.0 | 914.000 | 35.823 | 46.807 | 10.985 |

Table S23 compares training objectives within each site. Calendar-hour normalization makes Pizhou and Yandun exposure lengths explicit; all estimated contrasts are within-site.


### Table S24. Validation-selected storage designs across model-seed-price configurations

| Design regime | Power fraction | Duration (h) | Configurations |
| --- | --- | --- | --- |
| at least 10pct 2h | 0.1 | 2.0 | 154 |
| at least 10pct 2h | 0.2 | 2.0 | 61 |
| at least 10pct 2h | 0.2 | 4.0 | 1 |
| unconstrained | 0.0 | 0.0 | 97 |
| unconstrained | 0.05 | 1.0 | 13 |
| unconstrained | 0.05 | 2.0 | 2 |
| unconstrained | 0.1 | 1.0 | 20 |
| unconstrained | 0.1 | 2.0 | 9 |
| unconstrained | 0.2 | 1.0 | 14 |
| unconstrained | 0.2 | 2.0 | 60 |
| unconstrained | 0.2 | 4.0 | 1 |


### Table S25. Perfect-information and feasible online operating costs per installed MW

| Site | Model | Training | Prices | Oracle bound | Online control |
| --- | --- | --- | --- | --- | --- |
| pizhou | tcn | event weighted | base | 22113.263 | 22117.362 |
| pizhou | tcn | event weighted | high | 43053.035 | 43053.035 |
| pizhou | tcn | mse | base | 16395.128 | 16396.626 |
| pizhou | tcn | mse | high | 31449.965 | 31449.965 |
| pizhou | timesnet | event weighted | base | 18118.671 | 18121.488 |
| pizhou | timesnet | event weighted | high | 34955.351 | 34955.351 |
| pizhou | timesnet | mse | base | 15428.404 | 15429.524 |
| pizhou | timesnet | mse | high | 29506.511 | 29506.511 |
| yandun | tcn | event weighted | base | 13625.019 | 13630.816 |
| yandun | tcn | event weighted | high | 26768.344 | 26768.344 |
| yandun | tcn | mse | base | 8909.956 | 8915.752 |
| yandun | tcn | mse | high | 17223.279 | 17223.279 |
| yandun | timesnet | event weighted | base | 8751.009 | 8756.806 |
| yandun | timesnet | event weighted | high | 16884.979 | 16884.979 |
| yandun | timesnet | mse | base | 6519.700 | 6525.497 |
| yandun | timesnet | mse | high | 12383.639 | 12383.639 |


### Table S26. Exploratory test-grid cells with lower event-weighted storage cost

| Site | Model | Prices | Tail premium | Power fraction | Duration (h) | Mean difference | Seeds better |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pizhou | tcn | low | 5000.0 | 0.0 | 0.0 | -2099.370 | 2/3 |
| yandun | tcn | low | 5000.0 | 0.0 | 0.0 | -1480.504 | 3/3 |
| pizhou | tcn | low | 5000.0 | 0.05 | 1.0 | -1477.668 | 2/3 |
| yandun | tcn | low | 5000.0 | 0.05 | 1.0 | -1092.228 | 2/3 |
| yandun | tcn | low | 5000.0 | 0.05 | 2.0 | -923.508 | 2/3 |
| yandun | tcn | low | 5000.0 | 0.1 | 1.0 | -901.205 | 2/3 |
| yandun | tcn | low | 5000.0 | 0.05 | 4.0 | -779.969 | 2/3 |
| yandun | tcn | low | 5000.0 | 0.1 | 2.0 | -661.939 | 2/3 |
| pizhou | tcn | low | 5000.0 | 0.05 | 2.0 | -636.519 | 2/3 |
| pizhou | tcn | low | 5000.0 | 0.1 | 1.0 | -581.737 | 2/3 |
| yandun | tcn | low | 5000.0 | 0.2 | 2.0 | -523.860 | 3/3 |
| yandun | tcn | low | 5000.0 | 0.2 | 1.0 | -486.951 | 2/3 |
| pizhou | tcn | low | 5000.0 | 0.05 | 4.0 | -327.066 | 2/3 |
| yandun | tcn | low | 5000.0 | 0.1 | 4.0 | -261.756 | 1/3 |

Mean difference is event-weighted minus MSE total cost in CNY per installed MW, averaged over three seeds. These cells are a post-hoc diagnostic over the test grid; validation-selected policy comparisons appear in Table S37.


### Table S27. Controlled detection compute budget and model size

| Model | Seeds | Parameters | Max steps | Max epochs | Test n | CKPT bytes |
| --- | --- | --- | --- | --- | --- | --- |
| Mean rule | 1 | 0 | 0 | 0 | 800 | 0 |
| TimesNet | 3 | 37297 | 2200 | 88 | 800 | 479161 |
| KAN-AD | 3 | 9845 | 2225 | 89 | 800 | 48673 |
| TCN-AE | 3 | 15928 | 2500 | 100 | 800 | 68229 |
| Transformer-AE | 3 | 59920 | 2075 | 83 | 800 | 252208 |

Optimizer steps, epochs and checkpoint sizes are recorded from the upper-budget benchmark; the mean-change rule is analytic and has no fitted parameters.


### Table S28. Validation-selected detection hyperparameters and held-out performance

| Model | Selected size | Validation F1 | Test F1 (SD) | Precision | Recall | Delay | Seeds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TimesNet | size 8 | 0.681 | 0.631 (0.024) | 0.680 | 0.589 | 3.089 | 3 |
| KAN-AD | size 16 | 0.824 | 0.795 (0.097) | 0.829 | 0.765 | 1.870 | 3 |
| TCN-AE | width 8, z 8 | 0.757 | 0.729 (0.007) | 0.716 | 0.743 | 1.578 | 3 |
| Trans.-AE | width 8, z 8 | 0.718 | 0.660 (0.019) | 0.600 | 0.735 | 0.561 | 3 |
| Mean rule | window 4 | 0.774 | 0.741 | 0.742 | 0.740 | 1.162 | 1 |

Trans.-AE denotes the positional Transformer autoencoder. Size denotes TimesNet d_model or KAN-AD Fourier order; width and z are encoder width and latent size for the sequence autoencoders. SD is across training seeds. Model selection uses mean validation F1; the simple rule selects its mean window on the same validation population.


### Table S29. Fresh post-selection synthetic confirmation

| Condition | Model | Seeds | F1 (SD) | Precision | Recall | Delay |
| --- | --- | --- | --- | --- | --- | --- |
| higher noise | KAN-AD | 3 | 0.646 (0.098) | 0.545 | 0.796 | 1.746 |
| higher noise | Mean rule | 1 | 0.367 | 0.242 | 0.759 | 0.264 |
| higher noise | TCN-AE | 3 | 0.577 (0.011) | 0.457 | 0.783 | 1.376 |
| higher noise | TimesNet | 3 | 0.533 (0.026) | 0.547 | 0.520 | 3.069 |
| higher noise | Transformer-AE | 3 | 0.474 (0.015) | 0.343 | 0.770 | 0.528 |
| same family | KAN-AD | 3 | 0.793 (0.089) | 0.847 | 0.747 | 1.922 |
| same family | Mean rule | 1 | 0.732 | 0.718 | 0.748 | 1.294 |
| same family | TCN-AE | 3 | 0.716 (0.005) | 0.702 | 0.731 | 1.430 |
| same family | TimesNet | 3 | 0.604 (0.025) | 0.661 | 0.557 | 3.132 |
| same family | Transformer-AE | 3 | 0.650 (0.003) | 0.583 | 0.735 | 1.070 |

Each condition contains 1,600 fresh sequences, including 800 episodes. Delay is in generator steps, and SD summarizes the three frozen training seeds.


### Table S30. Paired F1 differences from the validation-selected mean rule

| Condition | Model | F1 difference | 95% interval |
| --- | --- | --- | --- |
| same family | TimesNet | -0.128 | [-0.154, -0.101] |
| same family | KAN-AD | 0.061 | [0.040, 0.082] |
| same family | TCN-AE | -0.016 | [-0.038, 0.007] |
| same family | Transformer-AE | -0.083 | [-0.105, -0.059] |
| higher noise | TimesNet | 0.165 | [0.138, 0.195] |
| higher noise | KAN-AD | 0.279 | [0.259, 0.299] |
| higher noise | TCN-AE | 0.210 | [0.188, 0.232] |
| higher noise | Transformer-AE | 0.107 | [0.089, 0.126] |

Intervals use 2,000 shared resamples of complete synthetic sequences, conditional on the frozen trained models. They characterize sampling uncertainty separately from between-seed variation.


### Table S31. CPU score-generation cost of the selected configurations

| Model | Parameters | Median ms/sequence | Range | Batch |
| --- | --- | --- | --- | --- |
| TimesNet | 18697 | 0.089122 | [0.082926, 0.102622] | 64 |
| KAN-AD | 16013 | 0.017341 | [0.017034, 0.017404] | 64 |
| TCN-AE | 10944 | 0.003181 | [0.003084, 0.003642] | 64 |
| Transformer-AE | 18856 | 0.070616 | [0.070247, 0.088320] | 64 |
| Mean rule | 0 | 0.000402 | [0.000384, 0.000453] | 800 |

Timing uses an AMD Ryzen 7 9700X under WSL2, two CPU threads, one warm-up and five runs of 800 sequences. Normalization and score generation are timed; interval postprocessing is excluded. The simple rule uses a NumPy cumulative-sum implementation.


### Table S32. Matched and unmatched composition within detector-pair sides

| Site | Feature | Sides used / all | Matched mean | Unmatched mean | Difference |
| --- | --- | --- | --- | --- | --- |
| Hill of Towie | Abs. change | 249/272 | 0.390 | 0.360 | 0.030 |
| Hill of Towie | Signed change | 249/272 | -0.016 | -0.009 | -0.008 |
| Hill of Towie | Duration (h) | 249/272 | 2.649 | 2.717 | -0.068 |
| Hill of Towie | Power range | 249/272 | 0.464 | 0.432 | 0.032 |
| Hill of Towie | Start power | 249/272 | 0.509 | 0.506 | 0.003 |
| Hill of Towie | Upward share | 249/272 | 0.491 | 0.492 | -0.001 |
| Hill of Towie | Wind (m/s) | 249/272 | 9.254 | 9.195 | 0.059 |
| La Haute Borne | Abs. change | 249/272 | 0.314 | 0.282 | 0.032 |
| La Haute Borne | Signed change | 249/272 | 0.010 | -0.001 | 0.011 |
| La Haute Borne | Duration (h) | 249/272 | 2.598 | 2.655 | -0.056 |
| La Haute Borne | Power range | 249/272 | 0.361 | 0.323 | 0.038 |
| La Haute Borne | Start power | 249/272 | 0.420 | 0.425 | -0.005 |
| La Haute Borne | Upward share | 249/272 | 0.512 | 0.498 | 0.014 |
| La Haute Borne | Wind (m/s) | 249/272 | 7.748 | 7.822 | -0.073 |
| Pizhou | Abs. change | 253/272 | 0.410 | 0.379 | 0.031 |
| Pizhou | Signed change | 253/272 | -0.022 | -0.012 | -0.010 |
| Pizhou | Duration (h) | 253/272 | 2.754 | 2.737 | 0.017 |
| Pizhou | Power range | 253/272 | 0.477 | 0.445 | 0.032 |
| Pizhou | Start power | 253/272 | 0.549 | 0.545 | 0.004 |
| Pizhou | Upward share | 253/272 | 0.477 | 0.483 | -0.006 |
| Pizhou | Wind (m/s) | 253/272 | 6.374 | 6.372 | 0.001 |
| Suining | Abs. change | 249/272 | 0.380 | 0.350 | 0.030 |
| Suining | Signed change | 249/272 | -0.004 | -0.000 | -0.003 |
| Suining | Duration (h) | 249/272 | 2.623 | 2.668 | -0.044 |
| Suining | Power range | 249/272 | 0.440 | 0.412 | 0.028 |
| Suining | Start power | 249/272 | 0.499 | 0.493 | 0.006 |
| Suining | Upward share | 249/272 | 0.496 | 0.500 | -0.005 |
| Suining | Wind (m/s) | 249/272 | 6.308 | 6.225 | 0.083 |
| Yandun | Abs. change | 257/272 | 0.429 | 0.387 | 0.042 |
| Yandun | Signed change | 257/272 | -0.023 | 0.000 | -0.023 |
| Yandun | Duration (h) | 257/272 | 2.790 | 2.810 | -0.020 |
| Yandun | Power range | 257/272 | 0.514 | 0.477 | 0.038 |
| Yandun | Start power | 257/272 | 0.358 | 0.347 | 0.011 |
| Yandun | Upward share | 257/272 | 0.471 | 0.495 | -0.024 |
| Yandun | Wind (m/s) | 257/272 | 5.646 | 5.649 | -0.003 |

Means give equal weight to supported detector-pair sides with available feature values in both populations. Power and amplitude use the archived normalization; direction is the fraction of upward events. Earlier wind averages four complete half-hour bins strictly before event start. The detailed companion CSV includes population sizes, valid wind counts and quartiles for every side.


### Table S33. Conditional raw25 agreement and retained support

| Site | Conditioning | Retained / original | Catalogue cov. L | Catalogue cov. R | Scored fraction | W. NMI | W. ARI |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Hill of Towie | amplitude_abs | 151847/243684 | 0.206 | 0.226 | 0.992 | 0.814 | 0.855 |
| Hill of Towie | direction | 239933/243684 | 0.326 | 0.358 | 0.999 | 0.275 | 0.335 |
| Hill of Towie | duration_hours | 131317/243684 | 0.178 | 0.196 | 0.998 | 0.837 | 0.853 |
| Hill of Towie | joint_all_four | 104335/243684 | 0.142 | 0.155 | 0.600 | 0.830 | 0.845 |
| Hill of Towie | power_start | 214671/243684 | 0.291 | 0.320 | 0.995 | 0.633 | 0.660 |
| La Haute Borne | amplitude_abs | 20627/34042 | 0.192 | 0.196 | 0.871 | 0.877 | 0.909 |
| La Haute Borne | direction | 33848/34042 | 0.315 | 0.322 | 0.787 | 0.173 | 0.225 |
| La Haute Borne | duration_hours | 20098/34042 | 0.187 | 0.191 | 0.982 | 0.844 | 0.851 |
| La Haute Borne | joint_all_four | 14783/34042 | 0.138 | 0.141 | 0.097 | 0.964 | 0.973 |
| La Haute Borne | power_start | 30788/34042 | 0.286 | 0.293 | 0.892 | 0.688 | 0.711 |
| Pizhou | amplitude_abs | 169991/274570 | 0.197 | 0.208 | 0.992 | 0.837 | 0.876 |
| Pizhou | direction | 271655/274570 | 0.315 | 0.333 | 0.998 | 0.289 | 0.363 |
| Pizhou | duration_hours | 151737/274570 | 0.176 | 0.186 | 0.998 | 0.843 | 0.865 |
| Pizhou | joint_all_four | 117670/274570 | 0.137 | 0.144 | 0.587 | 0.790 | 0.809 |
| Pizhou | power_start | 238656/274570 | 0.277 | 0.293 | 0.992 | 0.638 | 0.673 |
| Suining | amplitude_abs | 63990/102248 | 0.207 | 0.221 | 0.977 | 0.833 | 0.872 |
| Suining | direction | 100804/102248 | 0.325 | 0.349 | 0.994 | 0.296 | 0.359 |
| Suining | duration_hours | 56265/102248 | 0.182 | 0.195 | 0.995 | 0.846 | 0.864 |
| Suining | joint_all_four | 44368/102248 | 0.143 | 0.154 | 0.372 | 0.847 | 0.859 |
| Suining | power_start | 89315/102248 | 0.288 | 0.309 | 0.963 | 0.655 | 0.683 |
| Yandun | amplitude_abs | 558155/811453 | 0.235 | 0.260 | 0.999 | 0.783 | 0.826 |
| Yandun | direction | 791342/811453 | 0.333 | 0.369 | 1.000 | 0.295 | 0.356 |
| Yandun | duration_hours | 438801/811453 | 0.184 | 0.205 | 1.000 | 0.800 | 0.813 |
| Yandun | joint_all_four | 347316/811453 | 0.146 | 0.162 | 0.786 | 0.712 | 0.732 |
| Yandun | power_start | 723809/811453 | 0.304 | 0.337 | 0.998 | 0.631 | 0.644 |

Conditional raw25 scores are computed within detector-pair strata. Direction retains most temporal matches and gives lower information agreement. Amplitude and duration conditioning retain higher within-stratum agreement at lower support. Both-constant strata are excluded from informative scores, and one-side-constant strata contribute zero. Scored fractions refer to retained pairs in defined strata with at least 30 matches.


### Table S34. Test-label oracle ceilings for adjacent-mean windows

| Condition | Window grid | Oracle mode | Window | F1 | Label access |
| --- | --- | --- | --- | --- | --- |
| same family | original four windows | oracle window only | 4 | 0.732 | test-label oracle |
| same family | original four windows | oracle window and protocol | 4 | 0.732 | test-label oracle |
| same family | expanded twelve windows | oracle window only | 4 | 0.732 | test-label oracle |
| same family | expanded twelve windows | oracle window and protocol | 4 | 0.732 | test-label oracle |
| higher noise | original four windows | oracle window only | 16 | 0.501 | test-label oracle |
| higher noise | original four windows | oracle window and protocol | 4 | 0.588 | test-label oracle |
| higher noise | expanded twelve windows | oracle window only | 6 | 0.642 | test-label oracle |
| higher noise | expanded twelve windows | oracle window and protocol | 6 | 0.648 | test-label oracle |


### Table S35. Equal-validation noise calibration on a fresh high-noise draw

| Model | Policy | F1 | F1 SD | Precision | Recall | Seeds |
| --- | --- | --- | --- | --- | --- | --- |
| KAN-AD | source frozen | 0.641 | 0.109 | 0.538 | 0.796 | 3 |
| KAN-AD | target validation | 0.723 | 0.107 | 0.755 | 0.695 | 3 |
| Mean rule | source frozen | 0.380 | - | 0.251 | 0.777 | 1 |
| Mean rule | target validation | 0.626 | - | 0.606 | 0.646 | 1 |
| TCN-AE | source frozen | 0.579 | 0.005 | 0.458 | 0.789 | 3 |
| TCN-AE | target validation | 0.653 | 0.003 | 0.790 | 0.577 | 3 |
| TimesNet | source frozen | 0.536 | 0.023 | 0.555 | 0.520 | 3 |
| TimesNet | target validation | 0.570 | 0.011 | 0.602 | 0.540 | 3 |
| Transformer-AE | source frozen | 0.488 | 0.021 | 0.354 | 0.789 | 3 |
| Transformer-AE | target validation | 0.623 | 0.022 | 0.766 | 0.525 | 3 |


### Table S36. Paired gains after source or target-noise calibration

| Model | Policy | F1 gain | 95% interval |
| --- | --- | --- | --- |
| TimesNet | source frozen | 0.156 | [0.127, 0.185] |
| TimesNet | target validation | -0.056 | [-0.083, -0.030] |
| KAN-AD | source frozen | 0.261 | [0.241, 0.281] |
| KAN-AD | target validation | 0.098 | [0.074, 0.121] |
| TCN-AE | source frozen | 0.199 | [0.178, 0.223] |
| TCN-AE | target validation | 0.027 | [0.005, 0.049] |
| Transformer-AE | source frozen | 0.108 | [0.090, 0.127] |
| Transformer-AE | target validation | -0.003 | [-0.026, 0.021] |


### Table S37. Validation-selected policy cost comparison

| Site | Model | Prices | Tail | Regime | MSE CNY/MW/h | Event-weighted CNY/MW/h | Difference | Lower EW / seeds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pizhou | tcn | base | 0.0 | at least 10pct 2h | 11.490 | 13.782 | 2.292 | 0/3 |
| pizhou | tcn | base | 0.0 | unconstrained | 10.055 | 11.871 | 1.816 | 0/3 |
| pizhou | tcn | base | 1000.0 | at least 10pct 2h | 15.360 | 17.577 | 2.217 | 0/3 |
| pizhou | tcn | base | 1000.0 | unconstrained | 15.659 | 17.586 | 1.927 | 0/3 |
| pizhou | tcn | base | 5000.0 | at least 10pct 2h | 25.529 | 29.576 | 4.047 | 0/3 |
| pizhou | tcn | base | 5000.0 | unconstrained | 25.529 | 29.576 | 4.047 | 0/3 |
| pizhou | tcn | high | 0.0 | at least 10pct 2h | 17.521 | 22.169 | 4.649 | 0/3 |
| pizhou | tcn | high | 0.0 | unconstrained | 17.797 | 22.057 | 4.261 | 0/3 |
| pizhou | tcn | high | 1000.0 | at least 10pct 2h | 21.391 | 25.878 | 4.487 | 0/3 |
| pizhou | tcn | high | 1000.0 | unconstrained | 21.689 | 26.365 | 4.676 | 0/3 |
| pizhou | tcn | high | 5000.0 | at least 10pct 2h | 29.511 | 35.943 | 6.431 | 0/3 |
| pizhou | tcn | high | 5000.0 | unconstrained | 29.511 | 35.943 | 6.431 | 0/3 |
| pizhou | tcn | low | 0.0 | at least 10pct 2h | 8.474 | 9.588 | 1.114 | 0/3 |
| pizhou | tcn | low | 0.0 | unconstrained | 5.028 | 5.935 | 0.908 | 0/3 |
| pizhou | tcn | low | 1000.0 | at least 10pct 2h | 12.344 | 13.335 | 0.991 | 0/3 |
| pizhou | tcn | low | 1000.0 | unconstrained | 11.675 | 12.233 | 0.558 | 0/3 |
| pizhou | tcn | low | 5000.0 | at least 10pct 2h | 23.538 | 26.807 | 3.269 | 0/3 |
| pizhou | tcn | low | 5000.0 | unconstrained | 23.538 | 28.661 | 5.124 | 0/3 |
| pizhou | timesnet | base | 0.0 | at least 10pct 2h | 11.102 | 12.181 | 1.079 | 0/3 |
| pizhou | timesnet | base | 0.0 | unconstrained | 9.700 | 10.572 | 0.872 | 0/3 |
| pizhou | timesnet | base | 1000.0 | at least 10pct 2h | 16.022 | 18.251 | 2.229 | 0/3 |
| pizhou | timesnet | base | 1000.0 | unconstrained | 16.269 | 18.443 | 2.174 | 0/3 |
| pizhou | timesnet | base | 5000.0 | at least 10pct 2h | 31.143 | 37.745 | 6.603 | 0/3 |
| pizhou | timesnet | base | 5000.0 | unconstrained | 31.143 | 37.745 | 6.603 | 0/3 |
| pizhou | timesnet | high | 0.0 | at least 10pct 2h | 16.742 | 18.925 | 2.183 | 0/3 |
| pizhou | timesnet | high | 0.0 | unconstrained | 17.035 | 19.133 | 2.098 | 0/3 |
| pizhou | timesnet | high | 1000.0 | at least 10pct 2h | 21.661 | 24.995 | 3.334 | 0/3 |
| pizhou | timesnet | high | 1000.0 | unconstrained | 22.008 | 25.372 | 3.364 | 0/3 |
| pizhou | timesnet | high | 5000.0 | at least 10pct 2h | 34.746 | 42.453 | 7.707 | 0/3 |
| pizhou | timesnet | high | 5000.0 | unconstrained | 34.746 | 42.453 | 7.707 | 0/3 |
| pizhou | timesnet | low | 0.0 | at least 10pct 2h | 8.282 | 8.808 | 0.526 | 0/3 |
| pizhou | timesnet | low | 0.0 | unconstrained | 4.850 | 5.286 | 0.436 | 0/3 |
| pizhou | timesnet | low | 1000.0 | at least 10pct 2h | 13.202 | 14.879 | 1.677 | 0/3 |
| pizhou | timesnet | low | 1000.0 | unconstrained | 12.434 | 13.984 | 1.549 | 0/3 |
| pizhou | timesnet | low | 5000.0 | at least 10pct 2h | 29.341 | 35.392 | 6.050 | 0/3 |
| pizhou | timesnet | low | 5000.0 | unconstrained | 29.341 | 35.392 | 6.050 | 0/3 |
| yandun | tcn | base | 0.0 | at least 10pct 2h | 14.675 | 19.834 | 5.159 | 0/3 |
| yandun | tcn | base | 0.0 | unconstrained | 13.840 | 18.191 | 4.352 | 0/3 |
| yandun | tcn | base | 1000.0 | at least 10pct 2h | 19.627 | 24.137 | 4.511 | 0/3 |
| yandun | tcn | base | 1000.0 | unconstrained | 22.823 | 26.416 | 3.593 | 0/3 |
| yandun | tcn | base | 5000.0 | at least 10pct 2h | 32.400 | 41.352 | 8.952 | 0/3 |
| yandun | tcn | base | 5000.0 | unconstrained | 32.400 | 41.352 | 8.952 | 0/3 |
| yandun | tcn | high | 0.0 | at least 10pct 2h | 23.764 | 34.207 | 10.443 | 0/3 |
| yandun | tcn | high | 0.0 | unconstrained | 27.679 | 36.383 | 8.704 | 0/3 |
| yandun | tcn | high | 1000.0 | at least 10pct 2h | 28.716 | 38.511 | 9.795 | 0/3 |
| yandun | tcn | high | 1000.0 | unconstrained | 32.942 | 44.607 | 11.665 | 0/3 |
| yandun | tcn | high | 5000.0 | at least 10pct 2h | 39.148 | 49.955 | 10.807 | 0/3 |
| yandun | tcn | high | 5000.0 | unconstrained | 39.148 | 49.955 | 10.807 | 0/3 |
| yandun | tcn | low | 0.0 | at least 10pct 2h | 10.130 | 12.647 | 2.516 | 0/3 |
| yandun | tcn | low | 0.0 | unconstrained | 6.920 | 9.096 | 2.176 | 0/3 |
| yandun | tcn | low | 1000.0 | at least 10pct 2h | 15.082 | 16.951 | 1.868 | 0/3 |
| yandun | tcn | low | 1000.0 | unconstrained | 15.903 | 17.320 | 1.417 | 0/3 |
| yandun | tcn | low | 5000.0 | at least 10pct 2h | 30.986 | 34.165 | 3.179 | 0/3 |
| yandun | tcn | low | 5000.0 | unconstrained | 30.986 | 34.165 | 3.179 | 0/3 |
| yandun | timesnet | base | 0.0 | at least 10pct 2h | 12.060 | 14.501 | 2.441 | 0/3 |
| yandun | timesnet | base | 0.0 | unconstrained | 11.639 | 13.809 | 2.169 | 0/3 |
| yandun | timesnet | base | 1000.0 | at least 10pct 2h | 17.453 | 21.762 | 4.309 | 0/3 |
| yandun | timesnet | base | 1000.0 | unconstrained | 20.601 | 24.891 | 4.290 | 0/3 |
| yandun | timesnet | base | 5000.0 | at least 10pct 2h | 30.617 | 42.579 | 11.962 | 0/3 |
| yandun | timesnet | base | 5000.0 | unconstrained | 30.617 | 42.579 | 11.962 | 0/3 |
| yandun | timesnet | high | 0.0 | at least 10pct 2h | 18.469 | 23.394 | 4.925 | 0/3 |
| yandun | timesnet | high | 0.0 | unconstrained | 23.279 | 27.618 | 4.339 | 0/3 |
| yandun | timesnet | high | 1000.0 | at least 10pct 2h | 23.863 | 30.655 | 6.793 | 0/3 |
| yandun | timesnet | high | 1000.0 | unconstrained | 28.470 | 34.745 | 6.275 | 0/3 |
| yandun | timesnet | high | 5000.0 | at least 10pct 2h | 34.641 | 45.037 | 10.396 | 0/3 |
| yandun | timesnet | high | 5000.0 | unconstrained | 34.641 | 45.037 | 10.396 | 0/3 |
| yandun | timesnet | low | 0.0 | at least 10pct 2h | 8.855 | 10.055 | 1.199 | 0/3 |
| yandun | timesnet | low | 0.0 | unconstrained | 5.820 | 6.904 | 1.085 | 0/3 |
| yandun | timesnet | low | 1000.0 | at least 10pct 2h | 14.249 | 17.456 | 3.208 | 0/3 |
| yandun | timesnet | low | 1000.0 | unconstrained | 14.782 | 17.987 | 3.205 | 0/3 |
| yandun | timesnet | low | 5000.0 | at least 10pct 2h | 28.605 | 42.921 | 14.315 | 0/3 |
| yandun | timesnet | low | 5000.0 | unconstrained | 28.605 | 42.921 | 14.315 | 0/3 |


### Table S38. Representative validation-selected cost decomposition

| Site | Training | Prices | Tail | Capital | Throughput | Short | Surplus | Tail cost | Inventory | Total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pizhou | mse | low | 0.0 | 4.920 | 0.539 | 2.215 | 0.740 | 0.000 | -0.004 | 8.410 |
| pizhou | mse | low | 5000.0 | 9.841 | 0.810 | 1.438 | 0.513 | 11.115 | -0.013 | 23.705 |
| pizhou | mse | base | 0.0 | 4.920 | 0.539 | 4.429 | 1.480 | 0.000 | -0.004 | 11.365 |
| pizhou | mse | base | 5000.0 | 9.841 | 0.810 | 2.876 | 1.027 | 11.115 | -0.013 | 25.656 |
| pizhou | mse | high | 0.0 | 4.920 | 0.539 | 8.858 | 2.959 | 0.000 | -0.004 | 17.273 |
| pizhou | mse | high | 5000.0 | 9.841 | 0.810 | 5.753 | 2.054 | 11.115 | -0.013 | 29.560 |
| pizhou | event weighted | low | 0.0 | 4.920 | 0.450 | 3.748 | 0.682 | 0.000 | 0.010 | 9.811 |
| pizhou | event weighted | low | 5000.0 | 9.841 | 0.618 | 3.267 | 0.543 | 11.620 | 0.010 | 25.898 |
| pizhou | event weighted | base | 0.0 | 4.920 | 0.450 | 7.496 | 1.365 | 0.000 | 0.010 | 14.242 |
| pizhou | event weighted | base | 5000.0 | 9.841 | 0.618 | 6.534 | 1.086 | 11.620 | 0.010 | 29.708 |
| pizhou | event weighted | high | 0.0 | 4.920 | 0.450 | 14.993 | 2.730 | 0.000 | 0.010 | 23.103 |
| pizhou | event weighted | high | 5000.0 | 9.841 | 0.680 | 12.352 | 1.965 | 10.838 | 0.011 | 35.687 |
| yandun | mse | low | 0.0 | 4.920 | 0.638 | 4.045 | 0.776 | 0.000 | 0.026 | 10.405 |
| yandun | mse | low | 5000.0 | 4.920 | 0.638 | 4.045 | 0.776 | 26.179 | 0.026 | 36.584 |
| yandun | mse | base | 0.0 | 4.920 | 0.638 | 8.089 | 1.551 | 0.000 | 0.026 | 15.225 |
| yandun | mse | base | 5000.0 | 9.841 | 0.953 | 6.267 | 1.030 | 16.214 | 0.049 | 34.354 |
| yandun | mse | high | 0.0 | 4.920 | 0.638 | 16.178 | 3.103 | 0.000 | 0.026 | 24.865 |
| yandun | mse | high | 5000.0 | 9.841 | 0.953 | 12.535 | 2.059 | 16.214 | 0.049 | 41.651 |
| yandun | event weighted | low | 0.0 | 4.920 | 0.527 | 6.329 | 0.747 | 0.000 | 0.026 | 12.550 |
| yandun | event weighted | low | 5000.0 | 4.920 | 0.527 | 6.329 | 0.747 | 24.167 | 0.026 | 36.717 |
| yandun | event weighted | base | 0.0 | 4.920 | 0.527 | 12.659 | 1.494 | 0.000 | 0.026 | 19.627 |
| yandun | event weighted | base | 5000.0 | 4.920 | 0.527 | 12.659 | 1.494 | 24.167 | 0.026 | 43.793 |
| yandun | event weighted | high | 0.0 | 4.920 | 0.527 | 25.317 | 2.988 | 0.000 | 0.026 | 33.779 |
| yandun | event weighted | high | 5000.0 | 4.920 | 0.527 | 25.317 | 2.988 | 24.167 | 0.026 | 57.946 |


### Table S39. Real fixed 10%-power/2-hour online and LP traces

| Site | Training | Scenario | Calendar h | Online CNY/MW/h | LP CNY/MW/h | LP minus online | Online severe steps | LP severe steps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pizhou | mse | base | 2496.000 | 11.365 | 11.364 | -0.001 | 184 | 188 |
| pizhou | mse | high | 2496.000 | 17.273 | 17.273 | 0.000 | 184 | 190 |
| pizhou | mse | low_tail5000 | 2496.000 | 27.560 | 21.927 | -5.633 | 184 | 118 |
| pizhou | event weighted | base | 2496.000 | 14.242 | 14.239 | -0.002 | 198 | 220 |
| pizhou | event weighted | high | 2496.000 | 23.103 | 23.103 | 0.000 | 198 | 220 |
| pizhou | event weighted | low_tail5000 | 2496.000 | 26.945 | 21.215 | -5.730 | 198 | 107 |
| yandun | mse | base | 914.000 | 15.225 | 15.219 | -0.006 | 84 | 84 |
| yandun | mse | high | 914.000 | 24.865 | 24.865 | 0.000 | 84 | 84 |
| yandun | mse | low_tail5000 | 914.000 | 36.584 | 30.776 | -5.808 | 84 | 67 |
| yandun | event weighted | base | 914.000 | 19.627 | 19.620 | -0.006 | 84 | 90 |
| yandun | event weighted | high | 914.000 | 33.779 | 33.779 | 0.000 | 84 | 90 |
| yandun | event weighted | low_tail5000 | 914.000 | 36.717 | 31.327 | -5.390 | 84 | 66 |


### Table S40. Weather association model diagnostics

| Observations | Blocks | IRLS iterations | Converged | Exposure estimate | Cluster SE | Block-t p | BH q |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 76538 | 31 | 22 | True | 0.332 | 0.115 | 0.007 | 0.023 |


### Table S41. All neural model-size validation and test curves

| Model | Configuration | Validation F1 | Validation SD | Test F1 | Test SD |
| --- | --- | --- | --- | --- | --- |
| TimesNet | h08_z08 | 0.681 | 0.033 | 0.631 | 0.024 |
| TimesNet | h16_z16 | 0.662 | 0.013 | 0.609 | 0.014 |
| TimesNet | h32_z16 | 0.632 | 0.008 | 0.615 | 0.007 |
| KAN-AD | h08_z08 | 0.737 | 0.085 | 0.710 | 0.096 |
| KAN-AD | h16_z16 | 0.824 | 0.065 | 0.795 | 0.097 |
| KAN-AD | h32_z16 | 0.796 | 0.018 | 0.751 | 0.015 |
| TCN-AE | sequence_h08_z08 | 0.757 | 0.009 | 0.729 | 0.007 |
| TCN-AE | sequence_h16_z16 | 0.660 | 0.006 | 0.618 | 0.012 |
| TCN-AE | sequence_h32_z16 | 0.647 | 0.022 | 0.601 | 0.021 |
| Transformer-AE | sequence_h08_z08 | 0.718 | 0.021 | 0.660 | 0.019 |
| Transformer-AE | sequence_h16_z16 | 0.634 | 0.002 | 0.587 | 0.009 |
| Transformer-AE | sequence_h32_z16 | 0.609 | 0.015 | 0.560 | 0.012 |


### Table S42. All adjacent-mean candidate curves

| Condition | Window | Validation F1 | Frozen test F1 | Oracle test F1 |
| --- | --- | --- | --- | --- |
| same family | 1 | 0.492 | 0.448 | 0.448 |
| same family | 2 | 0.627 | 0.563 | 0.566 |
| same family | 3 | 0.678 | 0.639 | 0.644 |
| same family | 4 | 0.774 | 0.732 | 0.732 |
| same family | 5 | 0.763 | 0.729 | 0.729 |
| same family | 6 | 0.719 | 0.698 | 0.698 |
| same family | 8 | 0.701 | 0.694 | 0.720 |
| same family | 10 | 0.628 | 0.621 | 0.628 |
| same family | 12 | 0.596 | 0.596 | 0.596 |
| same family | 16 | 0.484 | 0.522 | 0.522 |
| same family | 24 | 0.208 | 0.255 | 0.255 |
| same family | 32 | 0.130 | 0.170 | 0.170 |
| higher noise | 1 | 0.492 | 0.158 | 0.295 |
| higher noise | 2 | 0.627 | 0.243 | 0.438 |
| higher noise | 3 | 0.678 | 0.221 | 0.517 |
| higher noise | 4 | 0.774 | 0.367 | 0.588 |
| higher noise | 5 | 0.763 | 0.558 | 0.621 |
| higher noise | 6 | 0.719 | 0.642 | 0.648 |
| higher noise | 8 | 0.701 | 0.300 | 0.563 |
| higher noise | 10 | 0.628 | 0.425 | 0.522 |
| higher noise | 12 | 0.596 | 0.504 | 0.539 |
| higher noise | 16 | 0.484 | 0.501 | 0.501 |
| higher noise | 24 | 0.208 | 0.282 | 0.284 |
| higher noise | 32 | 0.130 | 0.165 | 0.165 |

All candidate rows in S41 and S42 remain available in CSV form with their full selection settings. Oracle rows use test labels and provide an upper-bound diagnostic. Deployable selection uses validation labels. S37 uses validation-selected storage designs; S26 remains a post-hoc test-grid diagnostic. Cost components are in CNY per installed MW per test-calendar hour; unrounded values remain in the source CSV.


### Table S43. Yandun raw25 agreement across native and aggregated resolutions

| Left min | Right min | Left test | Right test | Pairs | Left cov. | Right cov. | NMI | ARI |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 15 | 30 | 19635 | 12328 | 10828 | 0.551 | 0.878 | 0.326 | 0.354 |
| 15 | 60 | 19635 | 7169 | 5126 | 0.261 | 0.715 | 0.257 | 0.257 |
| 30 | 60 | 12328 | 7169 | 6087 | 0.494 | 0.849 | 0.339 | 0.368 |

Each resolution fits its own training standardizer and k=4 prototypes. Test intervals match within turbine and split at IoU 0.5. The source is Yandun's native 15-min SCADA; 30- and 60-min series use complete arithmetic means and preserve missing-bin boundaries.

### Table S44. Received human-reference morphology by archive


Three observers; central two-hour regions displayed with four hours of context. Observer 1 = R_147f4682; Observer 2 = R_29d247dd; Observer 3 = R_2c332025. V and inverted V are listed separately; quiet and sustained-low are presence-negative.


| Observer | Archive | Rise | Fall | V | Inv. V | Osc. | Quiet | Low |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Observer 1 | greece | 14 | 7 | 2 | 1 | 0 | 11 | 5 |
| Observer 1 | hill | 4 | 5 | 8 | 6 | 2 | 9 | 6 |
| Observer 1 | lahaute | 6 | 8 | 3 | 2 | 1 | 10 | 10 |
| Observer 1 | pizhou | 12 | 13 | 4 | 0 | 1 | 10 | 0 |
| Observer 1 | sdwpf | 13 | 7 | 2 | 2 | 1 | 9 | 6 |
| Observer 1 | smarteole | 8 | 10 | 0 | 2 | 2 | 8 | 10 |
| Observer 1 | suining | 9 | 8 | 2 | 4 | 2 | 13 | 2 |
| Observer 1 | yandun | 9 | 7 | 0 | 5 | 2 | 5 | 12 |
| Observer 2 | greece | 11 | 5 | 3 | 7 | 6 | 8 | 0 |
| Observer 2 | hill | 1 | 5 | 11 | 9 | 7 | 6 | 1 |
| Observer 2 | lahaute | 3 | 4 | 10 | 8 | 10 | 4 | 1 |
| Observer 2 | pizhou | 8 | 7 | 8 | 7 | 7 | 3 | 0 |
| Observer 2 | sdwpf | 9 | 5 | 6 | 5 | 11 | 3 | 1 |
| Observer 2 | smarteole | 4 | 4 | 5 | 8 | 8 | 7 | 4 |
| Observer 2 | suining | 4 | 6 | 8 | 11 | 8 | 3 | 0 |
| Observer 2 | yandun | 6 | 3 | 1 | 9 | 9 | 8 | 4 |
| Observer 3 | greece | 14 | 5 | 2 | 1 | 1 | 16 | 1 |
| Observer 3 | hill | 0 | 7 | 9 | 5 | 6 | 12 | 1 |
| Observer 3 | lahaute | 5 | 5 | 4 | 2 | 5 | 17 | 2 |
| Observer 3 | pizhou | 12 | 10 | 2 | 1 | 6 | 9 | 0 |
| Observer 3 | sdwpf | 10 | 3 | 4 | 1 | 5 | 17 | 0 |
| Observer 3 | smarteole | 9 | 9 | 1 | 2 | 3 | 8 | 8 |
| Observer 3 | suining | 5 | 8 | 5 | 6 | 3 | 13 | 0 |
| Observer 3 | yandun | 9 | 3 | 0 | 3 | 5 | 12 | 8 |

### Table S45. All fixed detectors on the received real-window reference


Presence scoring on 320 selected windows; seven-day shared-block 95% intervals. The prespecified 120-min threshold is the reference for paired contrasts. Each observer contributes a separate reference; intervals condition on that observer.


| Observer | Detector | Precision | Recall | F1 | F1 interval |
| --- | --- | --- | --- | --- | --- |
| Observer 1 | adaptive corridor | 0.825 | 0.680 | 0.746 | 0.690–0.794 |
| Observer 1 | endpoint corridor 0.025 | 0.914 | 0.546 | 0.684 | 0.625–0.737 |
| Observer 1 | endpoint corridor 0.050 | 0.858 | 0.686 | 0.762 | 0.711–0.809 |
| Observer 1 | endpoint corridor 0.100 | 0.858 | 0.809 | 0.833 | 0.791–0.872 |
| Observer 1 | financial tail 120min | 0.825 | 0.268 | 0.405 | 0.321–0.483 |
| Observer 1 | financial tail 240min | 0.713 | 0.294 | 0.416 | 0.338–0.488 |
| Observer 1 | financial tail 60min | 0.825 | 0.242 | 0.375 | 0.291–0.450 |
| Observer 1 | mean shift 120min | 0.757 | 0.691 | 0.722 | 0.671–0.771 |
| Observer 1 | mean shift 240min | 0.716 | 0.727 | 0.721 | 0.668–0.768 |
| Observer 1 | mean shift 60min | 0.880 | 0.567 | 0.690 | 0.631–0.742 |
| Observer 1 | opsda cui2015 120min 0.025 | 0.867 | 0.603 | 0.711 | 0.660–0.757 |
| Observer 1 | opsda cui2015 240min 0.025 | 0.804 | 0.825 | 0.814 | 0.774–0.852 |
| Observer 1 | opsda cui2015 60min 0.025 | 0.931 | 0.278 | 0.429 | 0.352–0.494 |
| Observer 1 | sda florita2013 0.025 | 0.877 | 0.552 | 0.677 | 0.621–0.726 |
| Observer 1 | threshold 120min | 0.781 | 0.866 | 0.822 | 0.781–0.857 |
| Observer 1 | threshold 240min | 0.700 | 0.938 | 0.802 | 0.763–0.838 |
| Observer 1 | threshold 60min | 0.897 | 0.675 | 0.771 | 0.720–0.816 |
| Observer 3 | adaptive corridor | 0.844 | 0.689 | 0.758 | 0.704–0.805 |
| Observer 3 | endpoint corridor 0.025 | 0.948 | 0.561 | 0.705 | 0.649–0.756 |
| Observer 3 | endpoint corridor 0.050 | 0.871 | 0.689 | 0.769 | 0.720–0.813 |
| Observer 3 | endpoint corridor 0.100 | 0.891 | 0.832 | 0.860 | 0.820–0.896 |
| Observer 3 | financial tail 120min | 0.778 | 0.250 | 0.378 | 0.294–0.450 |
| Observer 3 | financial tail 240min | 0.662 | 0.270 | 0.384 | 0.308–0.454 |
| Observer 3 | financial tail 60min | 0.877 | 0.255 | 0.395 | 0.313–0.464 |
| Observer 3 | mean shift 120min | 0.740 | 0.668 | 0.702 | 0.643–0.754 |
| Observer 3 | mean shift 240min | 0.701 | 0.704 | 0.702 | 0.646–0.752 |
| Observer 3 | mean shift 60min | 0.880 | 0.561 | 0.685 | 0.626–0.740 |
| Observer 3 | opsda cui2015 120min 0.025 | 0.859 | 0.592 | 0.701 | 0.646–0.751 |
| Observer 3 | opsda cui2015 240min 0.025 | 0.794 | 0.806 | 0.800 | 0.752–0.840 |
| Observer 3 | opsda cui2015 60min 0.025 | 0.966 | 0.286 | 0.441 | 0.364–0.513 |
| Observer 3 | sda florita2013 0.025 | 0.893 | 0.556 | 0.686 | 0.629–0.737 |
| Observer 3 | threshold 120min | 0.772 | 0.847 | 0.808 | 0.765–0.849 |
| Observer 3 | threshold 240min | 0.704 | 0.934 | 0.803 | 0.759–0.841 |
| Observer 3 | threshold 60min | 0.918 | 0.684 | 0.784 | 0.734–0.827 |

### Table S46. Human-reference calendar-block sensitivity


All 17 configurations at 3, 7 and 14 days; 2,000 resamples per block length.


| Observer | Detector | Days | Farm-blocks | F1 interval |
| --- | --- | --- | --- | --- |
| Observer 1 | adaptive corridor | 3 | 248 | 0.693–0.796 |
| Observer 1 | endpoint corridor 0.025 | 3 | 248 | 0.623–0.743 |
| Observer 1 | endpoint corridor 0.050 | 3 | 248 | 0.708–0.812 |
| Observer 1 | endpoint corridor 0.100 | 3 | 248 | 0.791–0.871 |
| Observer 1 | financial tail 120min | 3 | 248 | 0.318–0.480 |
| Observer 1 | financial tail 240min | 3 | 248 | 0.335–0.488 |
| Observer 1 | financial tail 60min | 3 | 248 | 0.288–0.452 |
| Observer 1 | mean shift 120min | 3 | 248 | 0.667–0.774 |
| Observer 1 | mean shift 240min | 3 | 248 | 0.672–0.770 |
| Observer 1 | mean shift 60min | 3 | 248 | 0.633–0.744 |
| Observer 1 | opsda cui2015 120min 0.025 | 3 | 248 | 0.659–0.762 |
| Observer 1 | opsda cui2015 240min 0.025 | 3 | 248 | 0.773–0.854 |
| Observer 1 | opsda cui2015 60min 0.025 | 3 | 248 | 0.356–0.496 |
| Observer 1 | sda florita2013 0.025 | 3 | 248 | 0.621–0.732 |
| Observer 1 | threshold 120min | 3 | 248 | 0.779–0.859 |
| Observer 1 | threshold 240min | 3 | 248 | 0.762–0.839 |
| Observer 1 | threshold 60min | 3 | 248 | 0.723–0.815 |
| Observer 1 | adaptive corridor | 7 | 197 | 0.690–0.794 |
| Observer 1 | endpoint corridor 0.025 | 7 | 197 | 0.625–0.737 |
| Observer 1 | endpoint corridor 0.050 | 7 | 197 | 0.711–0.809 |
| Observer 1 | endpoint corridor 0.100 | 7 | 197 | 0.791–0.872 |
| Observer 1 | financial tail 120min | 7 | 197 | 0.321–0.483 |
| Observer 1 | financial tail 240min | 7 | 197 | 0.338–0.488 |
| Observer 1 | financial tail 60min | 7 | 197 | 0.291–0.450 |
| Observer 1 | mean shift 120min | 7 | 197 | 0.671–0.771 |
| Observer 1 | mean shift 240min | 7 | 197 | 0.668–0.768 |
| Observer 1 | mean shift 60min | 7 | 197 | 0.631–0.742 |
| Observer 1 | opsda cui2015 120min 0.025 | 7 | 197 | 0.660–0.757 |
| Observer 1 | opsda cui2015 240min 0.025 | 7 | 197 | 0.774–0.852 |
| Observer 1 | opsda cui2015 60min 0.025 | 7 | 197 | 0.352–0.494 |
| Observer 1 | sda florita2013 0.025 | 7 | 197 | 0.621–0.726 |
| Observer 1 | threshold 120min | 7 | 197 | 0.781–0.857 |
| Observer 1 | threshold 240min | 7 | 197 | 0.763–0.838 |
| Observer 1 | threshold 60min | 7 | 197 | 0.720–0.816 |
| Observer 1 | adaptive corridor | 14 | 140 | 0.693–0.793 |
| Observer 1 | endpoint corridor 0.025 | 14 | 140 | 0.625–0.741 |
| Observer 1 | endpoint corridor 0.050 | 14 | 140 | 0.709–0.809 |
| Observer 1 | endpoint corridor 0.100 | 14 | 140 | 0.791–0.873 |
| Observer 1 | financial tail 120min | 14 | 140 | 0.309–0.498 |
| Observer 1 | financial tail 240min | 14 | 140 | 0.331–0.493 |
| Observer 1 | financial tail 60min | 14 | 140 | 0.283–0.455 |
| Observer 1 | mean shift 120min | 14 | 140 | 0.670–0.772 |
| Observer 1 | mean shift 240min | 14 | 140 | 0.674–0.768 |
| Observer 1 | mean shift 60min | 14 | 140 | 0.632–0.743 |
| Observer 1 | opsda cui2015 120min 0.025 | 14 | 140 | 0.665–0.754 |
| Observer 1 | opsda cui2015 240min 0.025 | 14 | 140 | 0.774–0.849 |
| Observer 1 | opsda cui2015 60min 0.025 | 14 | 140 | 0.351–0.498 |
| Observer 1 | sda florita2013 0.025 | 14 | 140 | 0.622–0.726 |
| Observer 1 | threshold 120min | 14 | 140 | 0.784–0.855 |
| Observer 1 | threshold 240min | 14 | 140 | 0.764–0.839 |
| Observer 1 | threshold 60min | 14 | 140 | 0.720–0.816 |
| Observer 3 | adaptive corridor | 3 | 248 | 0.706–0.809 |
| Observer 3 | endpoint corridor 0.025 | 3 | 248 | 0.649–0.763 |
| Observer 3 | endpoint corridor 0.050 | 3 | 248 | 0.717–0.817 |
| Observer 3 | endpoint corridor 0.100 | 3 | 248 | 0.823–0.897 |
| Observer 3 | financial tail 120min | 3 | 248 | 0.293–0.449 |
| Observer 3 | financial tail 240min | 3 | 248 | 0.307–0.451 |
| Observer 3 | financial tail 60min | 3 | 248 | 0.312–0.471 |
| Observer 3 | mean shift 120min | 3 | 248 | 0.645–0.753 |
| Observer 3 | mean shift 240min | 3 | 248 | 0.650–0.753 |
| Observer 3 | mean shift 60min | 3 | 248 | 0.629–0.739 |
| Observer 3 | opsda cui2015 120min 0.025 | 3 | 248 | 0.644–0.751 |
| Observer 3 | opsda cui2015 240min 0.025 | 3 | 248 | 0.755–0.843 |
| Observer 3 | opsda cui2015 60min 0.025 | 3 | 248 | 0.368–0.506 |
| Observer 3 | sda florita2013 0.025 | 3 | 248 | 0.627–0.738 |
| Observer 3 | threshold 120min | 3 | 248 | 0.766–0.850 |
| Observer 3 | threshold 240min | 3 | 248 | 0.759–0.841 |
| Observer 3 | threshold 60min | 3 | 248 | 0.734–0.829 |
| Observer 3 | adaptive corridor | 7 | 197 | 0.704–0.805 |
| Observer 3 | endpoint corridor 0.025 | 7 | 197 | 0.649–0.756 |
| Observer 3 | endpoint corridor 0.050 | 7 | 197 | 0.720–0.813 |
| Observer 3 | endpoint corridor 0.100 | 7 | 197 | 0.820–0.896 |
| Observer 3 | financial tail 120min | 7 | 197 | 0.294–0.450 |
| Observer 3 | financial tail 240min | 7 | 197 | 0.308–0.454 |
| Observer 3 | financial tail 60min | 7 | 197 | 0.313–0.464 |
| Observer 3 | mean shift 120min | 7 | 197 | 0.643–0.754 |
| Observer 3 | mean shift 240min | 7 | 197 | 0.646–0.752 |
| Observer 3 | mean shift 60min | 7 | 197 | 0.626–0.740 |
| Observer 3 | opsda cui2015 120min 0.025 | 7 | 197 | 0.646–0.751 |
| Observer 3 | opsda cui2015 240min 0.025 | 7 | 197 | 0.752–0.840 |
| Observer 3 | opsda cui2015 60min 0.025 | 7 | 197 | 0.364–0.513 |
| Observer 3 | sda florita2013 0.025 | 7 | 197 | 0.629–0.737 |
| Observer 3 | threshold 120min | 7 | 197 | 0.765–0.849 |
| Observer 3 | threshold 240min | 7 | 197 | 0.759–0.841 |
| Observer 3 | threshold 60min | 7 | 197 | 0.734–0.827 |
| Observer 3 | adaptive corridor | 14 | 140 | 0.706–0.810 |
| Observer 3 | endpoint corridor 0.025 | 14 | 140 | 0.642–0.758 |
| Observer 3 | endpoint corridor 0.050 | 14 | 140 | 0.715–0.818 |
| Observer 3 | endpoint corridor 0.100 | 14 | 140 | 0.821–0.899 |
| Observer 3 | financial tail 120min | 14 | 140 | 0.285–0.471 |
| Observer 3 | financial tail 240min | 14 | 140 | 0.298–0.465 |
| Observer 3 | financial tail 60min | 14 | 140 | 0.308–0.479 |
| Observer 3 | mean shift 120min | 14 | 140 | 0.646–0.755 |
| Observer 3 | mean shift 240min | 14 | 140 | 0.649–0.750 |
| Observer 3 | mean shift 60min | 14 | 140 | 0.623–0.743 |
| Observer 3 | opsda cui2015 120min 0.025 | 14 | 140 | 0.642–0.755 |
| Observer 3 | opsda cui2015 240min 0.025 | 14 | 140 | 0.753–0.843 |
| Observer 3 | opsda cui2015 60min 0.025 | 14 | 140 | 0.360–0.515 |
| Observer 3 | sda florita2013 0.025 | 14 | 140 | 0.627–0.738 |
| Observer 3 | threshold 120min | 14 | 140 | 0.767–0.847 |
| Observer 3 | threshold 240min | 14 | 140 | 0.764–0.839 |
| Observer 3 | threshold 60min | 14 | 140 | 0.732–0.830 |

### Table S47. Prespecified detector by archive


Threshold at 120 min; all forty reviewed windows per archive are retained.


| Observer | Archive | N | TP | FP | FN | Precision | Recall | F1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Observer 1 | greece | 40 | 22 | 3 | 2 | 0.880 | 0.917 | 0.898 |
| Observer 1 | hill | 40 | 24 | 7 | 1 | 0.774 | 0.960 | 0.857 |
| Observer 1 | lahaute | 40 | 15 | 6 | 5 | 0.714 | 0.750 | 0.732 |
| Observer 1 | pizhou | 40 | 25 | 5 | 5 | 0.833 | 0.833 | 0.833 |
| Observer 1 | sdwpf | 40 | 23 | 10 | 2 | 0.697 | 0.920 | 0.793 |
| Observer 1 | smarteole | 40 | 15 | 1 | 7 | 0.938 | 0.682 | 0.789 |
| Observer 1 | suining | 40 | 22 | 8 | 3 | 0.733 | 0.880 | 0.800 |
| Observer 1 | yandun | 40 | 22 | 7 | 1 | 0.759 | 0.957 | 0.846 |
| Observer 2 | greece | 40 | 23 | 2 | 9 | 0.920 | 0.719 | 0.807 |
| Observer 2 | hill | 40 | 30 | 1 | 3 | 0.968 | 0.909 | 0.938 |
| Observer 2 | lahaute | 40 | 20 | 1 | 15 | 0.952 | 0.571 | 0.714 |
| Observer 2 | pizhou | 40 | 30 | 0 | 7 | 1.000 | 0.811 | 0.896 |
| Observer 2 | sdwpf | 40 | 30 | 3 | 6 | 0.909 | 0.833 | 0.870 |
| Observer 2 | smarteole | 40 | 15 | 1 | 14 | 0.938 | 0.517 | 0.667 |
| Observer 2 | suining | 40 | 28 | 2 | 9 | 0.933 | 0.757 | 0.836 |
| Observer 2 | yandun | 40 | 26 | 3 | 2 | 0.897 | 0.929 | 0.912 |
| Observer 3 | greece | 40 | 21 | 4 | 2 | 0.840 | 0.913 | 0.875 |
| Observer 3 | hill | 40 | 25 | 6 | 2 | 0.806 | 0.926 | 0.862 |
| Observer 3 | lahaute | 40 | 16 | 5 | 5 | 0.762 | 0.762 | 0.762 |
| Observer 3 | pizhou | 40 | 27 | 3 | 4 | 0.900 | 0.871 | 0.885 |
| Observer 3 | sdwpf | 40 | 20 | 13 | 3 | 0.606 | 0.870 | 0.714 |
| Observer 3 | smarteole | 40 | 15 | 1 | 9 | 0.938 | 0.625 | 0.750 |
| Observer 3 | suining | 40 | 23 | 7 | 4 | 0.767 | 0.852 | 0.807 |
| Observer 3 | yandun | 40 | 19 | 10 | 1 | 0.655 | 0.950 | 0.776 |

### Table S48. Independent partition-metric sensitivity


Pizhou-frozen K-means, k=4, seed 41; three representations on common supported basic-event test pairs. Higher AMI, Fowlkes–Mallows and NMI, and lower VI indicate closer partitions. These are single-seed sensitivity summaries, distinct from the primary three-seed common-support table.


| Archive | Representation | Pairs | AMI | FM | VI (nats) | NMI |
| --- | --- | --- | --- | --- | --- | --- |
| greece | gaf bit6 | 66 | 0.195 | 0.506 | 1.745 | 0.209 |
| greece | gaf pca6 | 66 | 0.192 | 0.503 | 1.752 | 0.208 |
| greece | raw25 | 66 | 0.862 | 0.956 | 0.213 | 0.864 |
| hill | gaf bit6 | 105 | 0.202 | 0.451 | 1.976 | 0.205 |
| hill | gaf pca6 | 105 | 0.204 | 0.451 | 1.982 | 0.206 |
| hill | raw25 | 105 | 0.751 | 0.900 | 0.412 | 0.751 |
| hill_2021 | gaf bit6 | 112 | 0.206 | 0.452 | 1.970 | 0.208 |
| hill_2021 | gaf pca6 | 112 | 0.207 | 0.451 | 1.980 | 0.209 |
| hill_2021 | raw25 | 112 | 0.763 | 0.913 | 0.399 | 0.763 |
| lahaute | gaf bit6 | 90 | 0.208 | 0.458 | 1.899 | 0.222 |
| lahaute | gaf pca6 | 90 | 0.210 | 0.456 | 1.901 | 0.218 |
| lahaute | raw25 | 90 | 0.886 | 0.962 | 0.181 | 0.887 |
| pizhou | gaf bit6 | 105 | 0.216 | 0.480 | 1.878 | 0.217 |
| pizhou | gaf pca6 | 105 | 0.216 | 0.480 | 1.880 | 0.218 |
| pizhou | raw25 | 105 | 0.828 | 0.944 | 0.276 | 0.828 |
| sdwpf | gaf bit6 | 119 | 0.227 | 0.468 | 1.892 | 0.227 |
| sdwpf | gaf pca6 | 119 | 0.223 | 0.468 | 1.903 | 0.224 |
| sdwpf | raw25 | 119 | 0.809 | 0.939 | 0.309 | 0.810 |
| suining | gaf bit6 | 98 | 0.230 | 0.461 | 1.903 | 0.233 |
| suining | gaf pca6 | 98 | 0.227 | 0.462 | 1.928 | 0.234 |
| suining | raw25 | 98 | 0.808 | 0.941 | 0.301 | 0.810 |
| yandun | gaf bit6 | 119 | 0.211 | 0.445 | 1.989 | 0.213 |
| yandun | gaf pca6 | 119 | 0.215 | 0.448 | 1.995 | 0.217 |
| yandun | raw25 | 119 | 0.734 | 0.897 | 0.475 | 0.734 |

### Table S49. Signed-weather log-loss decomposition


Occurrence and probability-weighted conditional-direction components sum to the three-class log loss. The conditional-direction contribution is averaged over all evaluated events. Lower scores are better.


| Archive | Input | Events | Occurrence | Direction | Total |
| --- | --- | --- | --- | --- | --- |
| hill | standalone gaf pca6 | 79436 | 0.3066 | 0.0727 | 0.3793 |
| hill | standalone gaf bit6 | 79436 | 0.3111 | 0.0340 | 0.3451 |
| hill | standalone raw pca6 | 79436 | 0.3028 | 0.0231 | 0.3259 |
| hill | controlled raw25 | 79436 | 0.2594 | 0.0220 | 0.2813 |
| hill | scalar controls5 | 79436 | 0.2601 | 0.0310 | 0.2911 |
| lahaute | standalone gaf pca6 | 12534 | 0.2870 | 0.0537 | 0.3407 |
| lahaute | standalone gaf bit6 | 12534 | 0.2856 | 0.0412 | 0.3269 |
| lahaute | standalone raw pca6 | 12534 | 0.2834 | 0.0391 | 0.3225 |
| lahaute | controlled raw25 | 12534 | 0.2615 | 0.0376 | 0.2991 |
| lahaute | scalar controls5 | 12534 | 0.2680 | 0.0448 | 0.3128 |
| pizhou | standalone gaf pca6 | 94534 | 0.2250 | 0.0452 | 0.2702 |
| pizhou | standalone gaf bit6 | 94534 | 0.2232 | 0.0234 | 0.2466 |
| pizhou | standalone raw pca6 | 94534 | 0.2203 | 0.0207 | 0.2410 |
| pizhou | controlled raw25 | 94534 | 0.1867 | 0.0203 | 0.2070 |
| pizhou | scalar controls5 | 94534 | 0.1915 | 0.0214 | 0.2129 |
| suining | standalone gaf pca6 | 33617 | 0.3171 | 0.0698 | 0.3869 |
| suining | standalone gaf bit6 | 33617 | 0.3199 | 0.0534 | 0.3733 |
| suining | standalone raw pca6 | 33617 | 0.3138 | 0.0546 | 0.3685 |
| suining | controlled raw25 | 33617 | 0.2859 | 0.0543 | 0.3402 |
| suining | scalar controls5 | 33617 | 0.2834 | 0.0599 | 0.3433 |
| yandun | standalone gaf pca6 | 238131 | 0.5553 | 0.1775 | 0.7328 |
| yandun | standalone gaf bit6 | 238131 | 0.5567 | 0.1717 | 0.7284 |
| yandun | standalone raw pca6 | 238131 | 0.5326 | 0.1680 | 0.7006 |
| yandun | controlled raw25 | 238131 | 0.4879 | 0.1743 | 0.6622 |
| yandun | scalar controls5 | 238131 | 0.4982 | 0.1837 | 0.6820 |

### Table S50. Chronologically calibrated LiDAR direction discrimination


AUROC uses the increase/decrease subset (705 and 285 events); the complete three-class test has 1,064 and 444 events. Intervals use 2,000 seven-day block draws. All three reported feature sets are retained.


| Turbine | Input | Events | Blocks | AUROC | 95% interval |
| --- | --- | --- | --- | --- | --- |
| T11 | standalone gaf pca6 | 705 | 4 | 0.494 | 0.468–0.544 |
| T11 | standalone gaf bit6 | 705 | 4 | 0.890 | 0.822–0.974 |
| T11 | scalar controls5 | 705 | 4 | 0.858 | 0.815–0.928 |
| T07 | standalone gaf pca6 | 285 | 4 | 0.477 | 0.321–0.599 |
| T07 | standalone gaf bit6 | 285 | 4 | 0.905 | 0.808–0.947 |
| T07 | scalar controls5 | 285 | 4 | 0.887 | 0.847–0.964 |

### Table S51. All forecast variants under observed Elexon prices


Each forecast supplies its own scheduled position in this exposure comparison. Gross debits sum positive interval costs; signed cashflow costs include credits. Monetary values are GBP; contractual revenue and capital are separate.


| Lead (h) | Variant | Intervals | nMAE | Gross debit | Signed cost |
| --- | --- | --- | --- | --- | --- |
| 1 | persistence | 2780 | 11.04% | 166,615 | 10,748 |
| 1 | power calendar | 2780 | 11.65% | 223,715 | 101,168 |
| 1 | observed weather | 2780 | 11.69% | 223,348 | 99,634 |
| 1 | historical events | 2780 | 11.95% | 230,987 | 106,175 |
| 1 | predicted ramp observed weather | 2780 | 11.49% | 211,164 | 80,727 |
| 1 | predicted ramp historical events | 2780 | 11.53% | 211,837 | 80,228 |
| 2 | persistence | 2768 | 13.66% | 206,169 | 14,447 |
| 2 | power calendar | 2768 | 14.95% | 312,174 | 173,238 |
| 2 | observed weather | 2768 | 14.61% | 294,259 | 152,092 |
| 2 | historical events | 2768 | 14.62% | 294,141 | 151,947 |
| 2 | predicted ramp observed weather | 2768 | 14.69% | 292,263 | 144,143 |
| 2 | predicted ramp historical events | 2768 | 14.47% | 279,178 | 128,456 |
| 4 | persistence | 2746 | 17.53% | 262,275 | 19,510 |
| 4 | power calendar | 2746 | 19.23% | 428,284 | 264,869 |
| 4 | observed weather | 2746 | 19.28% | 427,257 | 263,841 |
| 4 | historical events | 2746 | 19.05% | 421,364 | 260,805 |
| 4 | predicted ramp observed weather | 2746 | 19.34% | 430,049 | 267,500 |
| 4 | predicted ramp historical events | 2746 | 19.29% | 427,108 | 264,663 |

### Table S52. Common-commitment capacity and operating-cost decomposition


All arms use the same one-hour persistence commitment over 3,504 test half-hours when the issued forecast is available; unavailable-forecast intervals use the controller's zero-correction fallback. Future-outcome completeness is excluded from action readiness. Gain is relative to zero storage; net operating gain subtracts throughput times the stated cycling-cost sensitivity. Capital is excluded. Validation selects zero power for all six information variants and all three cost sensitivities. Negative gains at positive capacities explain that decision under this controller.


| Variant | Power fraction | GBP/MWh | Cashflow gain | MWh | Net gain |
| --- | --- | --- | --- | --- | --- |
| historical events | 0% | 0 | 0 | 0.0 | 0 |
| historical events | 0% | 10 | 0 | 0.0 | 0 |
| historical events | 0% | 30 | 0 | 0.0 | 0 |
| historical events | 5% | 0 | -2,799 | 727.5 | -2,799 |
| historical events | 5% | 10 | -2,799 | 727.5 | -10,074 |
| historical events | 5% | 30 | -2,799 | 727.5 | -24,625 |
| historical events | 10% | 0 | -4,903 | 1,226.2 | -4,903 |
| historical events | 10% | 10 | -4,903 | 1,226.2 | -17,165 |
| historical events | 10% | 30 | -4,903 | 1,226.2 | -41,689 |
| historical events | 20% | 0 | -7,630 | 1,952.0 | -7,630 |
| historical events | 20% | 10 | -7,630 | 1,952.0 | -27,150 |
| historical events | 20% | 30 | -7,630 | 1,952.0 | -66,191 |
| observed weather | 0% | 0 | 0 | 0.0 | 0 |
| observed weather | 0% | 10 | 0 | 0.0 | 0 |
| observed weather | 0% | 30 | 0 | 0.0 | 0 |
| observed weather | 5% | 0 | -2,696 | 748.4 | -2,696 |
| observed weather | 5% | 10 | -2,696 | 748.4 | -10,180 |
| observed weather | 5% | 30 | -2,696 | 748.4 | -25,147 |
| observed weather | 10% | 0 | -4,067 | 1,209.1 | -4,067 |
| observed weather | 10% | 10 | -4,067 | 1,209.1 | -16,158 |
| observed weather | 10% | 30 | -4,067 | 1,209.1 | -40,341 |
| observed weather | 20% | 0 | -7,292 | 1,890.5 | -7,292 |
| observed weather | 20% | 10 | -7,292 | 1,890.5 | -26,197 |
| observed weather | 20% | 30 | -7,292 | 1,890.5 | -64,008 |
| persistence | 0% | 0 | 0 | 0.0 | 0 |
| persistence | 0% | 10 | 0 | 0.0 | 0 |
| persistence | 0% | 30 | 0 | 0.0 | 0 |
| persistence | 5% | 0 | 0 | 0.0 | 0 |
| persistence | 5% | 10 | 0 | 0.0 | 0 |
| persistence | 5% | 30 | 0 | 0.0 | 0 |
| persistence | 10% | 0 | 0 | 0.0 | 0 |
| persistence | 10% | 10 | 0 | 0.0 | 0 |
| persistence | 10% | 30 | 0 | 0.0 | 0 |
| persistence | 20% | 0 | 0 | 0.0 | 0 |
| persistence | 20% | 10 | 0 | 0.0 | 0 |
| persistence | 20% | 30 | 0 | 0.0 | 0 |
| power calendar | 0% | 0 | 0 | 0.0 | 0 |
| power calendar | 0% | 10 | 0 | 0.0 | 0 |
| power calendar | 0% | 30 | 0 | 0.0 | 0 |
| power calendar | 5% | 0 | -2,637 | 756.0 | -2,637 |
| power calendar | 5% | 10 | -2,637 | 756.0 | -10,197 |
| power calendar | 5% | 30 | -2,637 | 756.0 | -25,316 |
| power calendar | 10% | 0 | -4,590 | 1,220.6 | -4,590 |
| power calendar | 10% | 10 | -4,590 | 1,220.6 | -16,796 |
| power calendar | 10% | 30 | -4,590 | 1,220.6 | -41,209 |
| power calendar | 20% | 0 | -7,697 | 1,874.9 | -7,697 |
| power calendar | 20% | 10 | -7,697 | 1,874.9 | -26,445 |
| power calendar | 20% | 30 | -7,697 | 1,874.9 | -63,942 |
| predicted ramp historical events | 0% | 0 | 0 | 0.0 | 0 |
| predicted ramp historical events | 0% | 10 | 0 | 0.0 | 0 |
| predicted ramp historical events | 0% | 30 | 0 | 0.0 | 0 |
| predicted ramp historical events | 5% | 0 | -2,910 | 754.0 | -2,910 |
| predicted ramp historical events | 5% | 10 | -2,910 | 754.0 | -10,449 |
| predicted ramp historical events | 5% | 30 | -2,910 | 754.0 | -25,529 |
| predicted ramp historical events | 10% | 0 | -5,354 | 1,211.2 | -5,354 |
| predicted ramp historical events | 10% | 10 | -5,354 | 1,211.2 | -17,467 |
| predicted ramp historical events | 10% | 30 | -5,354 | 1,211.2 | -41,692 |
| predicted ramp historical events | 20% | 0 | -8,411 | 1,848.4 | -8,411 |
| predicted ramp historical events | 20% | 10 | -8,411 | 1,848.4 | -26,894 |
| predicted ramp historical events | 20% | 30 | -8,411 | 1,848.4 | -63,862 |
| predicted ramp observed weather | 0% | 0 | 0 | 0.0 | 0 |
| predicted ramp observed weather | 0% | 10 | 0 | 0.0 | 0 |
| predicted ramp observed weather | 0% | 30 | 0 | 0.0 | 0 |
| predicted ramp observed weather | 5% | 0 | -3,068 | 745.7 | -3,068 |
| predicted ramp observed weather | 5% | 10 | -3,068 | 745.7 | -10,526 |
| predicted ramp observed weather | 5% | 30 | -3,068 | 745.7 | -25,440 |
| predicted ramp observed weather | 10% | 0 | -5,208 | 1,194.5 | -5,208 |
| predicted ramp observed weather | 10% | 10 | -5,208 | 1,194.5 | -17,153 |
| predicted ramp observed weather | 10% | 30 | -5,208 | 1,194.5 | -41,044 |
| predicted ramp observed weather | 20% | 0 | -7,679 | 1,831.7 | -7,679 |
| predicted ramp observed weather | 20% | 10 | -7,679 | 1,831.7 | -25,995 |
| predicted ramp observed weather | 20% | 30 | -7,679 | 1,831.7 | -62,629 |

### Table S53. Detector-perturbation axes


Every row crosses seven sites (Pizhou, Suining, Yandun, La Haute Borne, Hill of Towie, Greece and SDWPF) and lags of 60, 120 and 240 min. The seven perturbations therefore define 147 comparisons.


| Family | Reference | Perturbed values | Comparisons |
| --- | --- | --- | --- |
| Amplitude threshold | 0.20 | 0.10, 0.15, 0.25, 0.30 | 84 |
| Financial tail probability | 0.05 | 0.01, 0.025, 0.10 | 63 |

### Table S54. Independent human agreement before adjudication


320 paired windows, three actual observers. Nominal Krippendorff alpha and shared-calendar intervals preserve all ratings per window. The earlier 120-region reference is a separate cohort. One further review is ongoing; only received responses enter this table.


| Field | Block days | Agreement | Alpha | 95% interval |
| --- | --- | --- | --- | --- |
| event presence | 3 | 0.796 | 0.528 | 0.457–0.597 |
| event presence | 7 | 0.796 | 0.528 | 0.455–0.599 |
| event presence | 14 | 0.796 | 0.528 | 0.456–0.602 |
| morphology | 3 | 0.559 | 0.476 | 0.426–0.519 |
| morphology | 7 | 0.559 | 0.476 | 0.426–0.523 |
| morphology | 14 | 0.559 | 0.476 | 0.434–0.518 |

### Table S55. Jurisdiction-specific settlement requirements used to design transfer simulations


These are policy inputs and simulation requirements, not station invoices. Jiangsu specifies 15-min submitted curves, 96-point medium-short-term assessment, a monthly allowance for unqualified points and rated-capacity point charges. RTE specifies half-hourly imbalance settlement by balance-responsible-party imbalance sign, system trend, VWAP and coefficient k. S22 now evaluates the Chinese ultra-short-term accuracy component on native quarter-hour points. EMS/submission records are needed for actual invoices; aligned French historical prices remain a separate requirement.


| Jurisdiction | Policy quantity | Requirement used in simulation design | Current evidence |
| --- | --- | --- | --- |
| Jiangsu | Medium-short forecast | 15-min curve; 96-point assessment; next-day >=90%, day-10 >=70% | Official Su监能市场〔2022〕53号 |
| Jiangsu | Assessment allowance | Monthly unqualified-point allowance of 2%; point charge uses rated capacity | Official clause; station EMS missing |
| Jiangsu | Ultra-short accuracy | 97%/87% point accuracy at 15 min/4 h; CNY 4 per 10 MW per failed point | Native rule simulation in S22; no medium/short-term allowance |
| France | BRP imbalance | Positive/negative sign, trend, VWAP and k determine interval price | RTE official rule; historical price alignment pending |

### Table S56. Decision-aligned forecast extension at the two-hour horizon


The selected candidates use validation-only model/loss/blend selection. The test calendar is reused from v19 and is therefore exploratory. Gross-debit intervals compare selected event-aware training with the legacy ramp-mixture reference using shared 7-day farm blocks.


| Variant | nMAE | Gross debit (GBP) | Ramp nMAE |
| --- | --- | --- | --- |
| persistence | 13.66% | 206,169 | 34.69% |
| predicted ramp observed weather | 14.69% | 292,263 | 30.20% |
| predicted ramp historical events | 14.47% | 279,178 | 30.34% |
| selected weather | 13.61% | 225,532 | 32.45% |
| selected weather events | 13.69% | 233,084 | 32.33% |
| selected cost weather | 13.61% | 225,532 | 32.45% |
| selected cost weather events | 13.69% | 233,084 | 32.33% |


Selected event-aware versus legacy ramp-mixture: gross-debit reduction 16.51% (7-day interval 11.39–22.31%); nMAE reduction 0.79 percentage points (0.40–1.22).

### Table S57. Cluster-count sensitivity on frozen test populations

K-means, Pizhou training, three seeds. Each k uses the intersection of supported informative configuration pairs across the available representations and seeds. N denotes that intersection size. Six-representation and raw-only analyses are labelled separately; differing support sets across k must be retained when comparing medians.

| Population | k | Representations in support intersection | N | Raw25 ARI | Statistics9 ARI | GAF/PCA6 ARI |
|:--|--:|--:|--:|--:|--:|--:|
| greece | 2 | 6 | 24 | 0.961 | 0.456 | 0.135 |
| greece | 4 | 6 | 66 | 0.817 | 0.599 | 0.186 |
| greece | 6 | 6 | 66 | 0.735 | 0.835 | 0.294 |
| hill | 2 | 1 | 105 | 0.898 | — | — |
| hill | 4 | 6 | 104 | 0.717 | 0.488 | 0.209 |
| hill | 6 | 1 | 105 | 0.602 | — | — |
| hill_2021 | 2 | 6 | 91 | 0.904 | 0.233 | 0.144 |
| hill_2021 | 4 | 6 | 112 | 0.711 | 0.492 | 0.206 |
| hill_2021 | 6 | 6 | 112 | 0.587 | 0.651 | 0.252 |
| lahaute | 2 | 1 | 90 | 0.977 | — | — |
| lahaute | 4 | 6 | 89 | 0.785 | 0.579 | 0.195 |
| lahaute | 6 | 1 | 90 | 0.686 | — | — |
| pizhou | 2 | 6 | 63 | 0.930 | 0.324 | 0.147 |
| pizhou | 4 | 6 | 105 | 0.747 | 0.501 | 0.227 |
| pizhou | 6 | 6 | 105 | 0.653 | 0.643 | 0.284 |
| sdwpf | 2 | 1 | 119 | 0.940 | — | — |
| sdwpf | 4 | 6 | 119 | 0.745 | 0.501 | 0.220 |
| sdwpf | 6 | 1 | 119 | 0.605 | — | — |
| suining | 2 | 1 | 98 | 0.927 | — | — |
| suining | 4 | 6 | 98 | 0.724 | 0.515 | 0.223 |
| suining | 6 | 1 | 98 | 0.639 | — | — |
| yandun | 2 | 1 | 119 | 0.884 | — | — |
| yandun | 4 | 6 | 119 | 0.714 | 0.506 | 0.214 |
| yandun | 6 | 1 | 119 | 0.661 | — | — |

### Table S58. Many-to-many correspondence at IoU 0.5

The hierarchy-inclusive graph contains primitive and composite intervals. A split/merge component has more than one node on at least one side. Coverage pools unique connected nodes over eligible nodes across all configuration pairs. Component counts are summed over configuration pairs, not unique independent weather episodes. Full IoU 0.3/0.5/0.7 and containment configuration tables accompany this summary. The local component ledger retains individual interval clocks.

| Population | Components | Split/merge (%) | Both sides multiple (%) | Mixed hierarchy (%) | Left/right coverage (%) |
|:--|--:|--:|--:|--:|--:|
| greece | 18,327 | 19.8 | 8.2 | 16.4 | 32.8/32.4 |
| hill | 245,457 | 36.7 | 21.1 | 35.8 | 37.3/41.8 |
| hill_2021 | 370,583 | 33.4 | 17.8 | 31.9 | 36.2/40.8 |
| lahaute | 38,198 | 24.7 | 12.1 | 22.2 | 34.2/36.1 |
| pizhou | 276,979 | 29.9 | 15.8 | 26.8 | 35.3/37.5 |
| sdwpf | 1,113,510 | 29.1 | 15.7 | 27.1 | 34.8/37.3 |
| suining | 102,670 | 33.7 | 18.6 | 31.6 | 36.8/39.9 |
| yandun | 818,477 | 33.1 | 18.8 | 33.4 | 38.9/43.9 |

### Figure S1. Split and merge structure in the overlap graph

![Primitive and hierarchy-inclusive correspondence at IoU 0.5. Each segment gives the fraction of overlap components with one-to-one, one-to-many, many-to-one or many-to-many topology. All 136 configuration pairs are retained in each population.](figures_v23/supp_overlap_topology.pdf)

### Table S59. Primary policy-fee results and strong controls

| Lead | Validation-selected approach | nMAE (%) | Accuracy charge (CNY) | Saving (CNY) |
|:--|:--|--:|--:|--:|
| 15 min | Persistence | 3.039 | 112,705.56 | 0.00 |
| 15 min | Shape pipeline | 2.919 | 108,472.98 | 4,232.58 |
| 15 min | Scalar/weather control | 2.932 | 108,787.80 | 3,917.76 |
| 15 min | nMAE-selected reference | 2.910 | 106,654.02 | 6,051.54 |
| 4 h | Persistence | 17.557 | 148,804.92 | 0.00 |
| 4 h | Shape pipeline | 14.167 | 121,695.42 | 27,109.50 |
| 4 h | Scalar/weather control | 14.179 | 121,555.50 | 27,249.42 |
| 4 h | nMAE-selected reference | 13.589 | 121,100.76 | 27,704.16 |

CNY denotes Chinese yuan. The scalar/weather arm and nMAE reference are selected on validation under the same candidate budget; all methods share the test targets within a horizon. These are simulated accuracy charges, not complete operating costs.

### Table S60. Paired calendar-block uncertainty for policy-fee comparisons

Positive reductions favour the first named method. Low/high are 95% percentile limits for percentage reduction relative to the named comparator.

| comparison | block days | blocks | reduction pct | low | high |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 15 min: shape/persistence | 3 | 35 | 3.7554 | 2.2988 | 5.0394 |
| 15 min: shape/persistence | 7 | 16 | 3.7554 | 2.4109 | 4.9564 |
| 15 min: shape/persistence | 14 | 9 | 3.7554 | 2.7374 | 4.7095 |
| 15 min: shape/scalar | 3 | 35 | 0.2894 | -0.5303 | 1.0705 |
| 15 min: shape/scalar | 7 | 16 | 0.2894 | -0.5530 | 0.9175 |
| 15 min: shape/scalar | 14 | 9 | 0.2894 | -0.5396 | 1.0307 |
| 4h shape vs persistence | 3 | 35 | 18.2181 | 14.0247 | 22.3006 |
| 4h shape vs persistence | 7 | 16 | 18.2181 | 15.4317 | 21.3821 |
| 4h shape vs persistence | 14 | 9 | 18.2181 | 15.5854 | 21.5959 |
| 4h shape vs scalar | 3 | 35 | -0.1151 | -1.1399 | 0.9432 |
| 4h shape vs scalar | 7 | 16 | -0.1151 | -1.0524 | 0.7287 |
| 4h shape vs scalar | 14 | 9 | -0.1151 | -1.2945 | 0.8194 |
| 4h none band vs mean | 3 | 35 | 10.5435 | 5.5009 | 15.3175 |
| 4h none band vs mean | 7 | 16 | 10.5435 | 4.5487 | 16.0544 |
| 4h none band vs mean | 14 | 9 | 10.5435 | 5.7141 | 15.1012 |
| 4h jma band vs mean | 3 | 35 | 4.7007 | 0.1119 | 9.0097 |
| 4h jma band vs mean | 7 | 16 | 4.7007 | -0.3927 | 9.5338 |
| 4h jma band vs mean | 14 | 9 | 4.7007 | 2.0677 | 7.6969 |
| 4h jma gfs band vs mean | 3 | 35 | 4.5753 | 1.4295 | 7.4117 |
| 4h jma gfs band vs mean | 7 | 16 | 4.5753 | 1.1109 | 7.3343 |
| 4h jma gfs band vs mean | 14 | 9 | 4.5753 | 2.1051 | 7.1037 |

### Table S61. Classifier-seed robustness with fixed transformations and selected settings

| Lead (min) | seed | Charge (CNY) | Saving (%) | nmae |
| :-- | :-- | :-- | :-- | :-- |
| 15 | 41 | 108472.9800 | 3.7554 | 0.0292 |
| 15 | 42 | 108438.0000 | 3.7865 | 0.0292 |
| 15 | 43 | 108403.0200 | 3.8175 | 0.0292 |
| 240 | 41 | 121695.4200 | 18.2181 | 0.1417 |
| 240 | 42 | 122430.0000 | 17.7245 | 0.1423 |
| 240 | 43 | 122744.8200 | 17.5129 | 0.1421 |

### Table S62. Selection-objective comparison

Positive savings favour fee-selected over nMAE-selected predictions. Both selections use validation; testing does not alter either selection.

| Lead (min) | Block days | Blocks | Saved CNY | Reduction % | Low % | High % |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| 15 | 3 | 35 | -1818.960 | -1.705 | -2.722 | -0.629 |
| 15 | 7 | 16 | -1818.960 | -1.705 | -2.439 | -0.902 |
| 15 | 14 | 9 | -1818.960 | -1.705 | -2.443 | -0.991 |
| 240 | 3 | 35 | -594.660 | -0.491 | -3.064 | 1.952 |
| 240 | 7 | 16 | -594.660 | -0.491 | -3.364 | 1.671 |
| 240 | 14 | 9 | -594.660 | -0.491 | -2.954 | 1.910 |

### Table S63. Full-calendar attribution of rule-based charges

States use absolute actual-minus-persistence change. The first state lies within the horizon-specific tolerance, Moderate changes lie above tolerance and below 20% capacity, and high ramps reach at least 20%. Introduced charges and avoided charges both enter totals.

| Lead (min) | state | points | Persistence CNY | Pipeline CNY | Saved CNY |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 15 | Within tolerance | 6228 | 0.0000 | 7800.5400 | -7800.5400 |
| 15 | Moderate change | 3145 | 110012.1000 | 97978.9800 | 12033.1200 |
| 15 | High ramp | 77 | 2693.4600 | 2693.4600 | 0.0000 |
| 240 | Within tolerance | 5091 | 0.0000 | 14971.4400 | -14971.4400 |
| 240 | Moderate change | 1175 | 41101.5000 | 18154.6200 | 22946.8800 |
| 240 | High ramp | 3079 | 107703.4200 | 88569.3600 | 19134.0600 |

### Table S64. Complete-income British test outcomes

The July–December 2021 test uses frozen validation selections, observed MID execution-price references, imbalance settlement and a simulated trading fee. Negative differences indicate lower total income than passive persistence.

| Lead (h) | Arm | Intervals | Revenue GBP | Difference GBP |
| :-- | :-- | :-- | :-- | :-- |
| 1 | weather | 8430 | 6958536.4060 | -16311.5635 |
| 1 | weather events | 8430 | 6955018.3262 | -19829.6432 |
| 2 | weather | 8428 | 6905633.2851 | -22117.4134 |
| 2 | weather events | 8428 | 6906029.4332 | -21721.2653 |
| 4 | weather | 8424 | 6916025.2306 | -25991.0653 |
| 4 | weather events | 8424 | 6915705.8628 | -26310.4331 |

### Figure S2. Preserved British economic comparison

![Earlier British large-ramp exposure concentration. Grey bars show interval share and magenta bars the share of persistence gross debits.](figures_v22/fig12_ramp_exposure.pdf)

### Figure S3. Preserved British economic comparison

![Earlier British forecast-error and gross-debit comparison, on common targets within each horizon. This gross-exposure task is distinct from complete trading income in Table S64.](figures_v22/fig13_forecast_cost.pdf)

### Figure S4. Preserved British economic comparison

![Earlier ex-post metered-correction capability. The event-aware 20% battery reduces gross debits by 27.1% while signed settlement cost rises. Realized half-hour power, inventory restoration and model-specific schedules define this task; it is not an issue-time forecast or net-profit gain.](figures_v22/fig14_storage.pdf)
