# Data Dictionary -- afib-classification

## Data Sources

### ECG Features (`data/raw/ecg_features.parquet`)

| Column | Type | Description | Unit | Availability |
|--------|------|-------------|------|--------------|
| record_id | string | Unique ECG recording identifier | - | unavailable (ID) |
| rr_mean | float | Mean RR interval | ms | available |
| rr_std | float | Standard deviation of RR intervals | ms | available |
| rr_median | float | Median RR interval | ms | available |
| rr_iqr | float | Interquartile range of RR intervals | ms | available |
| rr_rmssd | float | Root mean square of successive RR differences | ms | available |
| rr_pnn50 | float | Percentage of successive RR intervals differing by >50ms | % | available |
| p_wave_duration | float | Mean P-wave duration | ms | available |
| p_wave_amplitude | float | Mean P-wave amplitude | mV | available |
| p_wave_area | float | Mean P-wave area | mV*ms | available |
| p_wave_morphology_score | float | P-wave morphology consistency score | 0-1 | available |
| qrs_duration | float | Mean QRS complex duration | ms | available |
| qrs_amplitude | float | Mean QRS amplitude | mV | available |
| qrs_area | float | Mean QRS area | mV*ms | available |
| hrv_sdnn | float | Standard deviation of NN intervals | ms | available |
| hrv_sdsd | float | Standard deviation of successive differences | ms | available |
| hrv_lf_power | float | Low-frequency HRV power (0.04-0.15 Hz) | ms^2 | available |
| hrv_hf_power | float | High-frequency HRV power (0.15-0.4 Hz) | ms^2 | available |
| hrv_lf_hf_ratio | float | LF/HF ratio | ratio | available |
| hrv_sample_entropy | float | Sample entropy of RR intervals | - | available |
| hrv_approximate_entropy | float | Approximate entropy of RR intervals | - | available |
| heart_rate_mean | float | Mean heart rate | bpm | available |
| heart_rate_std | float | Heart rate standard deviation | bpm | available |
| heart_rate_min | float | Minimum heart rate | bpm | available |
| heart_rate_max | float | Maximum heart rate | bpm | available |

### Clinical Labels (`data/raw/clinical_labels.csv`)

| Column | Type | Description | Unit | Availability |
|--------|------|-------------|------|--------------|
| record_id | string | Unique ECG recording identifier | - | unavailable (ID) |
| af_label | int | Atrial fibrillation label (0=no AF, 1=AF) | binary | unavailable (target) |
| diagnosis_date | date | Date of clinical diagnosis | date | unavailable (metadata) |
| cardiologist_notes | string | Clinical notes from cardiologist review | text | unavailable (metadata) |

## Join Strategy

- **Join key**: `record_id`
- **Join type**: inner join
- **Expected**: 1:1 relationship between ECG features and clinical labels
