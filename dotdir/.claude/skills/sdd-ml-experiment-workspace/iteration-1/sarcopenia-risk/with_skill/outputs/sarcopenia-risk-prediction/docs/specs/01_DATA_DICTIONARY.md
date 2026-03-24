# Data Dictionary — sarcopenia-risk-prediction

## Data Sources

### InBody Data (CSV)
- **Location**: `data/raw/` (CSV format)
- **Description**: Body composition measurements from InBody device
- **Key columns**:
  | Column | Type | Description |
  |--------|------|-------------|
  | username | string | Subject identifier (join key) |
  | smi | float | Skeletal Muscle Index (kg/m^2) |
  | height | float | Height in cm |
  | weight | float | Weight in kg |
  | age | int/float | Age in years |
  | bmi | float | Body Mass Index |
  | vfl | float | Visceral Fat Level |
  | gender | categorical | Male/Female |

### Gait Features (Parquet)
- **Location**: `data/raw/` (Parquet format)
- **Description**: Gait biomechanics features extracted from insole sensor data
- **Key columns**:
  | Column Group | Count | Description |
  |-------------|-------|-------------|
  | username | 1 | Subject identifier (join key) |
  | walk_features | 830 | Walk-level gait characteristics |
  | step_features | 259 | Step-level biomechanical measurements |

## Join Strategy

- **Join key**: `username`
- **Join type**: INNER (only subjects with both InBody and gait data)
- **Deduplication**: If multiple records per subject, handle at data loading time

## Target Variable

- **Name**: `sarcopenia_risk_score`
- **Type**: Continuous (regression)
- **Construction**: Derived from InBody clinical measurements (details in Phase A)

## Split Unit

- **Field**: `username`
- **Constraint**: All data from the same subject must reside in the same fold/split
