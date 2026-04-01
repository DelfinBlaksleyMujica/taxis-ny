import requests
import pandas as pd
import streamlit as st
import plotly.express as px
import folium

from streamlit_folium import st_folium

URL_API = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="NY Taxi Traffic Predictor",
    page_icon="🚕",
    layout="wide"
)

st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }

        .title {
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 0.2rem;
        }

        .subtitle {
            font-size: 1.05rem;
            color: #9aa0a6;
            margin-bottom: 1.5rem;
        }

        .card {
            background: rgba(255,255,255,0.03);
            padding: 1.5rem;
            border-radius: 20px;
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: 0 8px 30px rgba(0,0,0,0.10);
            margin-top: 1rem;
            margin-bottom: 1rem;
        }

        .result-card {
            background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.02));
            padding: 1.5rem;
            border-radius: 20px;
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: 0 8px 30px rgba(0,0,0,0.10);
            margin-top: 1rem;
            margin-bottom: 1rem;
        }

        .section-card {
            background: rgba(255,255,255,0.03);
            padding: 1.5rem;
            border-radius: 18px;
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: 0 8px 30px rgba(0,0,0,0.10);
            margin-top: 1rem;
            margin-bottom: 1rem;
        }

        .small-label {
            font-size: 0.9rem;
            color: #9aa0a6;
            margin-bottom: 0.25rem;
        }

        .big-number {
            font-size: 1.7rem;
            font-weight: 700;
            margin: 0;
        }

        .section-title {
            font-size: 1.35rem;
            font-weight: 700;
            margin-bottom: 1rem;
            margin-top: 1rem;
        }

        .mini-card {
            background: rgba(255,255,255,0.04);
            padding: 1rem;
            border-radius: 14px;
            border: 1px solid rgba(255,255,255,0.08);
            min-height: 140px;
        }
    </style>
""", unsafe_allow_html=True)

day_options = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
]

hour_options = [str(i) for i in range(24)]

borough_options = [
    "Queens",
    "Bronx",
    "State Island",
    "Manhattan",
    "Brooklyn"
]


def calculate_ad_value(traffic_value, visualization_value):
    if traffic_value < 50 and visualization_value < 100:
        return 50
    elif 50 <= traffic_value < 100 and  100 <= visualization_value < 500:
        return 100
    elif 100 <= traffic_value < 200 and 500 <= visualization_value < 1000:
        return 200
    else:
        return 300


def get_tier_label(ad_value):
    return {
        50: "Low traffic",
        100: "Medium traffic",
        200: "High traffic",
        300: "Premium traffic"
    }.get(ad_value, "")


def format_hour(hour_value):
    return f"{int(hour_value):02d}:00"


def normalize_borough_key(name: str) -> str:
    return name.lower().strip().replace(" ", "_")


@st.cache_data(show_spinner=False)
def fetch_prediction(borough, day_name, hour):
    response = requests.get(
        f"{URL_API}/data",
        params={
            "borough": borough,
            "day_name": day_name,
            "hour": hour
        },
        timeout=10
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(show_spinner=False)
def fetch_borough_dataset(borough, dataset_type="traffic"):
    response = requests.get(
        f"{URL_API}/data/all",
        params={
            "borough": borough,
            "dataset_type": dataset_type
        },
        timeout=10
    )
    response.raise_for_status()
    data = response.json()
    df = pd.DataFrame(data)

    if not df.empty:
        df["hour"] = pd.to_numeric(df["hour"], errors="coerce")
        df["yhat"] = pd.to_numeric(df["yhat"], errors="coerce")
        df = df.dropna(subset=["hour", "yhat"])
        df["hour"] = df["hour"].astype(int)
        df["yhat"] = df["yhat"].astype(float)

    return df


@st.cache_data(show_spinner=False)
def fetch_all_dataset(dataset_type="traffic"):
    response = requests.get(
        f"{URL_API}/data/all",
        params={"dataset_type": dataset_type},
        timeout=10
    )
    response.raise_for_status()
    data = response.json()
    df = pd.DataFrame(data)

    if not df.empty:
        df["hour"] = pd.to_numeric(df["hour"], errors="coerce")
        df["yhat"] = pd.to_numeric(df["yhat"], errors="coerce")
        df = df.dropna(subset=["hour", "yhat"])
        df["hour"] = df["hour"].astype(int)
        df["yhat"] = df["yhat"].astype(float)

    return df


st.markdown('<div class="title">🚕 NY Taxi Traffic Predictor</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Consultá tráfico estimado, visualizaciones y oportunidad de pauta por barrio, día y horario.</div>',
    unsafe_allow_html=True
)

col1, col2, col3 = st.columns(3)

with col1:
    selected_borough = st.selectbox("Seleccionar distrito", borough_options)

with col2:
    selected_day = st.selectbox("Seleccionar día", day_options)

with col3:
    selected_hour = st.selectbox("Seleccionar hora", hour_options, index=12)

if "show_results" not in st.session_state:
    st.session_state.show_results = False

search_clicked = st.button("Buscar predicción", use_container_width=True)

if search_clicked:
    st.session_state.show_results = True

if st.session_state.show_results:
    with st.spinner("Consultando predicción..."):
        try:
            prediction_data = fetch_prediction(selected_borough, selected_day, selected_hour)
            borough_df = fetch_borough_dataset(selected_borough, dataset_type="traffic")
            borough_visual_df = fetch_borough_dataset(selected_borough, dataset_type="visualization")
            all_df = fetch_all_dataset(dataset_type="traffic")
            all_visual_df = fetch_all_dataset(dataset_type="visualization")

            if prediction_data:
                item = prediction_data

                traffic_value = float(item["traffic"]["yhat"])
                visualization_value = float(item["visualizations"]["yhat"])
                ad_value = calculate_ad_value(traffic_value , visualization_value)

                metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)

                with metric_col1:
                    st.markdown('<div class="small-label">Distrito</div>', unsafe_allow_html=True)
                    st.markdown(f'<p class="big-number">{item["borough"]}</p>', unsafe_allow_html=True)

                with metric_col2:
                    st.markdown('<div class="small-label">Día / Hora</div>', unsafe_allow_html=True)
                    st.markdown(
                        f'<p class="big-number">{item["day_name"]} {format_hour(item["hour"])}</p>',
                        unsafe_allow_html=True
                    )

                with metric_col3:
                    st.markdown('<div class="small-label">Predicción de autos</div>', unsafe_allow_html=True)
                    st.markdown(f'<p class="big-number">{int(traffic_value)}</p>', unsafe_allow_html=True)

                with metric_col4:
                    st.markdown('<div class="small-label">Visualizaciones</div>', unsafe_allow_html=True)
                    st.markdown(f'<p class="big-number">{int(visualization_value)}</p>', unsafe_allow_html=True)


                with metric_col5:
                    st.markdown('<div class="small-label">Valor de publicidad</div>', unsafe_allow_html=True)
                    st.markdown(f'<p class="big-number">{ad_value} USD/hora</p>', unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)

                st.info(f"Ad tier: {get_tier_label(ad_value)}")

                st.success(
                    f"Para {item['borough']} el día {item['day_name']} a las {format_hour(item['hour'])}, "
                    f"la predicción es de {int(traffic_value)} autos y {int(visualization_value)} visualizaciones."
                )

                st.markdown('<div class="section-title">Mapa de Densidad de Tráfico por Distrito</div>', unsafe_allow_html=True)

                BOROUGH_COORDS = {
                    "queens": {"lat": 40.7282, "lon": -73.7949},
                    "bronx": {"lat": 40.8448, "lon": -73.8648},
                    "state_island": {"lat": 40.5795, "lon": -74.1502},
                    "manhattan": {"lat": 40.7831, "lon": -73.9712},
                    "brooklyn": {"lat": 40.6782, "lon": -73.9442},
                }

                map_df = all_df[
                    (all_df["day_name"] == selected_day) &
                    (all_df["hour"] == int(selected_hour))
                ].copy()

                map_df["borough_key"] = map_df["borough"].apply(normalize_borough_key)
                map_df["lat"] = map_df["borough_key"].map(lambda x: BOROUGH_COORDS.get(x, {}).get("lat"))
                map_df["lon"] = map_df["borough_key"].map(lambda x: BOROUGH_COORDS.get(x, {}).get("lon"))
                map_df = map_df.dropna(subset=["lat", "lon"])

                GEOJSON_URL = "https://raw.githubusercontent.com/dwillis/nyc-maps/master/boroughs.geojson"
                geo_data = requests.get(GEOJSON_URL, timeout=20).json()

                BOROUGH_NAME_MAP = {
                    "Staten Island": "state_island",
                    "Manhattan": "manhattan",
                    "Brooklyn": "brooklyn",
                    "Queens": "queens",
                    "The Bronx": "bronx"
                }

                yhat_dict = dict(zip(map_df["borough_key"], map_df["yhat"]))

                for feature in geo_data["features"]:
                    boro_name = feature["properties"]["BoroName"]
                    key = BOROUGH_NAME_MAP.get(boro_name, boro_name.lower())
                    feature["properties"]["borough_key"] = key
                    feature["properties"]["trafico"] = int(yhat_dict.get(key, 0))

                m = folium.Map(location=[40.7128, -74.0060], zoom_start=10, tiles="cartodbpositron")

                choropleth = folium.Choropleth(
                    geo_data=geo_data,
                    data=map_df,
                    columns=["borough_key", "yhat"],
                    key_on="feature.properties.borough_key",
                    fill_color="YlOrRd",
                    fill_opacity=0.7,
                    line_opacity=0.3,
                    legend_name="N° de autos estimados",
                    nan_fill_color="#ffffcc",
                    threshold_scale=[0, 1, 100, 500, 1000, 2000, 3000, 4000]
                ).add_to(m)

                choropleth.geojson.add_child(
                    folium.features.GeoJsonTooltip(
                        fields=["BoroName", "trafico"],
                        aliases=["Distrito:", "Autos estimados:"],
                        style="background-color: white; color: #333; font-size: 13px; padding: 8px;"
                    )
                )

                BOROUGH_LABELS = {
                    "queens": {"lat": 40.7282, "lon": -73.8449, "label": "Queens"},
                    "bronx": {"lat": 40.8448, "lon": -73.8648, "label": "Bronx"},
                    "state_island": {"lat": 40.5795, "lon": -74.1502, "label": "State Island"},
                    "manhattan": {"lat": 40.7831, "lon": -73.9712, "label": "Manhattan"},
                    "brooklyn": {"lat": 40.6782, "lon": -73.9442, "label": "Brooklyn"},
                }

                for key, data in BOROUGH_LABELS.items():
                    traffic_amount = int(yhat_dict.get(key, 0))
                    folium.Marker(
                        location=[data["lat"], data["lon"]],
                        icon=folium.DivIcon(
                            html=f"""
                                <div style="
                                    font-size: 11px;
                                    font-weight: 700;
                                    color: #111;
                                    text-align: center;
                                    white-space: nowrap;
                                    background: rgba(255,255,255,0.85);
                                    padding: 4px 6px;
                                    border-radius: 8px;
                                    border: 1px solid rgba(0,0,0,0.08);
                                ">
                                    {data["label"]}<br>{traffic_amount}
                                </div>
                            """
                        )
                    ).add_to(m)

                st_folium(m, width=None, height=520)

                st.markdown('<div class="section-title">Mejor día y horario para anunciar en dicho distrito</div>', unsafe_allow_html=True)

                chart_df = borough_df.copy()
                chart_df["slot"] = (
                    chart_df["day_name"] + " " +
                    chart_df["hour"].astype(int).astype(str).str.zfill(2) + ":00"
                )
                chart_df = chart_df.sort_values("yhat", ascending=False).head(15)

                fig_top_slots = px.bar(
                    chart_df,
                    x="slot",
                    y="yhat",
                    title=f"Top horarios por tráfico estimado en {selected_borough}",
                    labels={"slot": "Día y hora", "yhat": "Autos estimados"}
                )
                fig_top_slots.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_top_slots, use_container_width=True)

                st.markdown('<div class="section-title">Top horarios por visualizaciones en dicho distrito</div>', unsafe_allow_html=True)

                visual_chart_df = borough_visual_df.copy()
                visual_chart_df["slot"] = (
                    visual_chart_df["day_name"] + " " +
                    visual_chart_df["hour"].astype(int).astype(str).str.zfill(2) + ":00"
                )
                visual_chart_df = visual_chart_df.sort_values("yhat", ascending=False).head(15)

                fig_top_visual = px.bar(
                    visual_chart_df,
                    x="slot",
                    y="yhat",
                    title=f"Top horarios por visualizaciones en {selected_borough}",
                    labels={"slot": "Día y hora", "yhat": "Visualizaciones estimadas"}
                )
                fig_top_visual.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_top_visual, use_container_width=True)

                st.markdown('<div class="section-title">Comparación semanal del distrito</div>', unsafe_allow_html=True)

                selected_slot_visual = borough_visual_df[
                    borough_visual_df["hour"] == int(selected_hour)
                ].copy()

                selected_slot_traffic = borough_df[
                    borough_df["hour"] == int(selected_hour)
                ].copy()

                compare_df = selected_slot_traffic.merge(
                    selected_slot_visual[["day_name", "hour", "yhat"]],
                    on=["day_name", "hour"],
                    suffixes=("_traffic", "_visual")
                )

                # compare_df["combined"] = compare_df["yhat_traffic"] * compare_df["yhat_visual"]

                fig_compare = px.line(
                    compare_df,
                    x="day_name",
                    y=["yhat_traffic", "yhat_visual"],
                    markers=True,
                    title=f"Comparación semanal para las {format_hour(selected_hour)} en {selected_borough}",
                    labels={
                        "value": "Valor",
                        "day_name": "Día",
                        "variable": "Métrica"
                    }
                )
                st.plotly_chart(fig_compare, use_container_width=True)

                st.markdown('<div class="section-title">Ranking general por tráfico en el mismo día y horario</div>', unsafe_allow_html=True)

                ranking_df = all_df[
                    (all_df["day_name"] == selected_day) &
                    (all_df["hour"] == int(selected_hour))
                ].copy().sort_values("yhat", ascending=False)

                fig_ranking = px.bar(
                    ranking_df,
                    x="borough",
                    y="yhat",
                    title=f"Tráfico estimado por distrito · {selected_day} {format_hour(selected_hour)}",
                    labels={"borough": "Distrito", "yhat": "Autos estimados"}
                )
                st.plotly_chart(fig_ranking, use_container_width=True)

                st.markdown('<div class="section-title">Ranking general por visualizaciones en el mismo día y horario</div>', unsafe_allow_html=True)

                ranking_visual_df = all_visual_df[
                    (all_visual_df["day_name"] == selected_day) &
                    (all_visual_df["hour"] == int(selected_hour))
                ].copy().sort_values("yhat", ascending=False)

                fig_visual_ranking = px.bar(
                    ranking_visual_df,
                    x="borough",
                    y="yhat",
                    title=f"Visualizaciones estimadas por distrito · {selected_day} {format_hour(selected_hour)}",
                    labels={"borough": "Distrito", "yhat": "Visualizaciones"}
                )
                st.plotly_chart(fig_visual_ranking, use_container_width=True)

                st.markdown('<div class="section-title">Detalle tabular del distrito</div>', unsafe_allow_html=True)

                detail_df = borough_df.merge(
                    borough_visual_df[["day_name", "hour", "yhat"]],
                    on=["day_name", "hour"],
                    suffixes=("_traffic", "_visualizations")
                )
                detail_df["calculated_value"] = (
                    detail_df["yhat_traffic"] * detail_df["yhat_visualizations"]
                )
                detail_df = detail_df.rename(columns={
                    "yhat_traffic": "traffic_yhat",
                    "yhat_visualizations": "visualizations_yhat"
                })

                st.dataframe(
                    detail_df[[
                        "borough",
                        "day_name",
                        "hour",
                        "traffic_yhat",
                        "visualizations_yhat",
                        "calculated_value"
                    ]].sort_values(["day_name", "hour"]),
                    use_container_width=True
                )

        except requests.HTTPError as e:
            try:
                error_detail = e.response.json().get("detail", str(e))
            except Exception:
                error_detail = str(e)
            st.error(f"Error al consultar la API: {error_detail}")

        except Exception as e:
            st.error(f"Ocurrió un error inesperado: {e}")
