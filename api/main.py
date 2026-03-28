from pathlib import Path
from functools import lru_cache

import pandas as pd
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="NY Taxi Traffic API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

BOROUGH_FILES = {
    "Queens": DATA_DIR / "queens.csv",
    "State Island": DATA_DIR / "state_island.csv",
    "Bronx": DATA_DIR / "bronx.csv",
    "Brooklyn": DATA_DIR / "brooklyn.csv",
    "Manhattan": DATA_DIR / "manhattan.csv"
}

VALID_DAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
]

DAY_ORDER = {day: i for i, day in enumerate(VALID_DAYS)}
VALID_HOURS = [str(i) for i in range(24)]


def detect_separator(file_path: Path) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        first_line = f.readline().strip()

    if ";" in first_line and "," in first_line:
        return ";"
    if ";" in first_line:
        return ";"
    return ","


@lru_cache(maxsize=16)
def read_file_cached(borough: str) -> pd.DataFrame:
    file_path = BOROUGH_FILES.get(borough)

    if not file_path:
        raise HTTPException(status_code=400, detail="borough inválido")

    if not file_path.exists():
        raise HTTPException(
            status_code=500,
            detail=f"No se encontró el archivo para {borough}: {file_path.name}"
        )

    separator = detect_separator(file_path)
    df = pd.read_csv(file_path, sep=separator)
    df.columns = [col.strip() for col in df.columns]

    required_columns = {"day_name", "hour", "yhat"}
    if not required_columns.issubset(df.columns):
        raise HTTPException(
            status_code=500,
            detail=(
                f"El archivo {file_path.name} no tiene las columnas requeridas: "
                f"{required_columns}. Columnas detectadas: {list(df.columns)}"
            )
        )

    df["day_name"] = df["day_name"].astype(str).str.strip()
    df["hour"] = pd.to_numeric(df["hour"], errors="coerce")
    df["yhat"] = pd.to_numeric(df["yhat"], errors="coerce")

    df = df.dropna(subset=["day_name", "hour", "yhat"])
    df["hour"] = df["hour"].astype(int)
    df["yhat"] = df["yhat"].astype(float)
    df["borough"] = borough
    df["day_order"] = df["day_name"].map(DAY_ORDER)

    df = df.sort_values(["day_order", "hour"]).reset_index(drop=True)
    return df


def read_file(borough: str) -> pd.DataFrame:
    return read_file_cached(borough).copy()


def get_all_data() -> pd.DataFrame:
    frames = [read_file(borough) for borough in BOROUGH_FILES.keys()]
    return pd.concat(frames, ignore_index=True)


@app.get("/")
def index():
    return {
        "ok": True,
        "message": "NY Taxi Traffic API is running"
    }


@app.get("/boroughs")
def get_boroughs():
    return {
        "boroughs": list(BOROUGH_FILES.keys())
    }


@app.get("/data")
def get_data(
    borough: str = Query(..., description="Queens, State Island, Manhattan, Brooklyn o Bronx"),
    day_name: str = Query(..., description="Day of week"),
    hour: str = Query(..., description="Hour from 0 to 23")
):
    if borough not in BOROUGH_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"borough inválido. Valores permitidos: {list(BOROUGH_FILES.keys())}"
        )

    if day_name not in VALID_DAYS:
        raise HTTPException(
            status_code=400,
            detail=f"day_name inválido. Valores permitidos: {VALID_DAYS}"
        )

    if hour not in VALID_HOURS:
        raise HTTPException(
            status_code=400,
            detail=f"hour inválido. Valores permitidos: {VALID_HOURS}"
        )

    df = read_file(borough)

    filtered_df = df[
        (df["day_name"] == day_name) &
        (df["hour"] == int(hour))
    ].drop(columns=["day_order"], errors="ignore")

    return filtered_df.to_dict(orient="records")


@app.get("/data/all")
def get_all_dataset(
    borough: str | None = Query(default=None, description="Optional borough filter")
):
    if borough:
        if borough not in BOROUGH_FILES:
            raise HTTPException(
                status_code=400,
                detail=f"borough inválido. Valores permitidos: {list(BOROUGH_FILES.keys())}"
            )
        df = read_file(borough)
    else:
        df = get_all_data()

    df = df.drop(columns=["day_order"], errors="ignore")
    return df.to_dict(orient="records")
