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
    "Queens": DATA_DIR / "borough-files" / "queens.csv",
    "State Island": DATA_DIR / "borough-files" / "staten_island.csv",
    "Bronx": DATA_DIR / "borough-files" / "bronx.csv",
    "Brooklyn": DATA_DIR / "borough-files" / "brooklyn.csv",
    "Manhattan": DATA_DIR / "borough-files" / "manhattan.csv",
}

VISUALIZATION_FILES = {
    "Queens": DATA_DIR / "visualizaciones" / "queens_visualizaciones.csv",
    "State Island": DATA_DIR / "visualizaciones" / "statenIsland_visualizaciones.csv",
    "Bronx": DATA_DIR / "visualizaciones" / "bronx_visualizaciones.csv",
    "Brooklyn": DATA_DIR / "visualizaciones" / "brooklyn_visualizaciones.csv",
    "Manhattan": DATA_DIR / "visualizaciones" / "manhattan_visualizaciones.csv",
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

    if ";" in first_line:
        return ";"
    return ","


def validate_inputs(borough: str, day_name: str, hour: str):
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


@lru_cache(maxsize=32)
def read_dataset_cached(dataset_type: str, borough: str) -> pd.DataFrame:
    file_map = BOROUGH_FILES if dataset_type == "traffic" else VISUALIZATION_FILES
    file_path = file_map.get(borough)

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
    df["dataset_type"] = dataset_type
    df["day_order"] = df["day_name"].map(DAY_ORDER)

    df = df.sort_values(["day_order", "hour"]).reset_index(drop=True)
    return df


def read_traffic_file(borough: str) -> pd.DataFrame:
    return read_dataset_cached("traffic", borough).copy()


def read_visualization_file(borough: str) -> pd.DataFrame:
    return read_dataset_cached("visualization", borough).copy()


def get_all_data(dataset_type: str) -> pd.DataFrame:
    frames = []
    for borough in BOROUGH_FILES.keys():
        if dataset_type == "traffic":
            frames.append(read_traffic_file(borough))
        elif dataset_type == "visualization":
            frames.append(read_visualization_file(borough))
        else:
            raise HTTPException(status_code=400, detail="dataset_type inválido")

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
    validate_inputs(borough, day_name, hour)

    traffic_df = read_traffic_file(borough)
    visualization_df = read_visualization_file(borough)

    traffic_row = traffic_df[
        (traffic_df["day_name"] == day_name) &
        (traffic_df["hour"] == int(hour))
    ].drop(columns=["day_order"], errors="ignore")

    visualization_row = visualization_df[
        (visualization_df["day_name"] == day_name) &
        (visualization_df["hour"] == int(hour))
    ].drop(columns=["day_order"], errors="ignore")

    if traffic_row.empty:
        raise HTTPException(
            status_code=404,
            detail="No se encontraron datos de tráfico para esa combinación"
        )

    if visualization_row.empty:
        raise HTTPException(
            status_code=404,
            detail="No se encontraron datos de visualizaciones para esa combinación"
        )

    traffic_item = traffic_row.iloc[0].to_dict()
    visualization_item = visualization_row.iloc[0].to_dict()

    traffic_value = float(traffic_item["yhat"])
    visualization_value = float(visualization_item["yhat"])

    calculated_value = traffic_value * visualization_value

    return {
        "borough": borough,
        "day_name": day_name,
        "hour": int(hour),
        "traffic": {
            "yhat": traffic_value
        },
        "visualizations": {
            "yhat": visualization_value
        },
        "calculated_value": calculated_value
    }


@app.get("/data/all")
def get_all_dataset(
    borough: str | None = Query(default=None, description="Optional borough filter"),
    dataset_type: str = Query(default="traffic", description="traffic o visualization")
):
    if dataset_type not in ["traffic", "visualization"]:
        raise HTTPException(
            status_code=400,
            detail="dataset_type inválido. Valores permitidos: traffic, visualization"
        )

    if borough:
        if borough not in BOROUGH_FILES:
            raise HTTPException(
                status_code=400,
                detail=f"borough inválido. Valores permitidos: {list(BOROUGH_FILES.keys())}"
            )

        df = read_traffic_file(borough) if dataset_type == "traffic" else read_visualization_file(borough)
    else:
        df = get_all_data(dataset_type)

    df = df.drop(columns=["day_order"], errors="ignore")
    return df.to_dict(orient="records")
