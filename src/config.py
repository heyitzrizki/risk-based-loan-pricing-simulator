from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SAMPLE_DATA_DIR = DATA_DIR / "sample"

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
ARTIFACT_DATA_DIR = ARTIFACTS_DIR / "data"
ARTIFACT_MODEL_DIR = ARTIFACTS_DIR / "model"
ARTIFACT_REPORT_DIR = ARTIFACTS_DIR / "reports"

RAW_DATA_PATH = RAW_DATA_DIR / "lending_club_loan_two.csv"

RANDOM_STATE = 42
