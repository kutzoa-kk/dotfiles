# Data Dictionary — knee-oa-progression

## Data Sources

### Joint Angle Time-Series (`data/raw/joint_angles.h5`)

| Field | Type | Description | Unit |
|-------|------|-------------|------|
| patient_id | string | Unique patient identifier | - |
| side | string | Knee side: L (left) or R (right) | - |
| knee_flexion | float[] | Knee flexion angle time-series | degrees |
| knee_extension | float[] | Knee extension angle time-series | degrees |
| knee_varus_valgus | float[] | Varus/valgus angle time-series | degrees |
| knee_rotation | float[] | Internal/external rotation time-series | degrees |
| gait_cycle | float[] | Gait cycle phase indicators | - |

- **Sampling rate**: 100 Hz
- **Format**: HDF5, structured as `/patient_id/side/channel_name`
- **Zero semantics**: Zero values represent non-contact or valid zero angle, NOT missing data

### Clinical Metadata (`data/raw/clinical_metadata.csv`)

| Field | Type | Description | Range |
|-------|------|-------------|-------|
| patient_id | string | Unique patient identifier | - |
| side | string | Knee side (L/R) | L, R |
| kl_grade | int | Kellgren-Lawrence grade (TARGET) | 0-4 |
| radiograph_score | float | Raw radiograph severity score | continuous |
| age | int | Patient age at visit | 18-100 |
| sex | string | Patient sex | M, F |
| bmi | float | Body mass index | 15-50 |
| visit_date | date | Date of assessment | YYYY-MM-DD |

## Derived Features

Time-series data is aggregated to per-session summary statistics:

| Feature | Source | Description |
|---------|--------|-------------|
| knee_flexion_mean | joint_angles.h5 | Mean knee flexion during gait |
| knee_flexion_std | joint_angles.h5 | Variability of knee flexion |
| knee_flexion_range | joint_angles.h5 | Range of motion (max - min) |
| knee_flexion_max | joint_angles.h5 | Peak flexion angle |
| knee_flexion_min | joint_angles.h5 | Minimum flexion angle |
| stance_duration_mean | joint_angles.h5 | Mean stance phase duration |
| stride_length_mean | joint_angles.h5 | Mean stride length |
| cadence_mean | joint_angles.h5 | Mean stepping cadence |
| gait_speed_mean | joint_angles.h5 | Mean walking speed |

## Join Strategy

- **Primary key**: (`patient_id`, `side`)
- **Join type**: Inner join between joint_angles and clinical_metadata
- **Granularity**: One row per (patient, side, visit)
