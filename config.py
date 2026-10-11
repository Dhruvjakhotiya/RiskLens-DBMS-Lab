from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "instance" / "health_risk.db"
MODEL_DIR = BASE_DIR / "ml" / "saved_models"
DATA_DIR = BASE_DIR / "ml" / "data"
PLOTS_DIR = BASE_DIR / "static" / "plots"
