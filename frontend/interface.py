import requests
import pandas as pd
import streamlit as st
import altair as alt
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
        .main {
            padding-top: 2rem;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1350px;
        }

        .title {
            font-size: 2.6rem;
            font-weight: 700;
            margin-bottom: 0.3rem;
        }

        .subtitle {
            font-size: 1rem;
            color: #9aa0a6;
            margin-bottom: 2rem;
        }

        .card {
            background: rgba(255,255,255,0.04);
            padding: 1.5rem;
            border-radius: 18px;
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: 0 8px 30px rgba(0,0,0,0.15);
            margin-bottom: 1rem;
        }

        .result-card {
            background: linear-gradient(135deg, rgba(0, 120, 255, 0.15), rgba(0, 200, 160, 0.12));
            padding: 1.5rem;
            border-radius: 18px;
            border: 1px solid rgba(255,255,255,0.08);
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
            font-size: 2rem;
            font-weight: 700;
            margin: 0;
        }

        .section-title {
            font-size: 1.35rem;
            font-weight: 700;
            margin-bottom: 1rem;
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


def calculate_ad_value(traffic_value):
    if traffic_value < 50:
        return 50
    elif 50 <= traffic_value < 100:
        return 100
    elif 100 <= traffic_value < 200:
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
def fetch_borough_dataset(borough):
    response = requests.get(
        f"{URL_API}/data/all",
        params={"borough": borough},
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

    return df


@st.cache_data(show_spinner=False)
def fetch_all_dataset():
    response = requests.get(f"{URL_API}/data/all", timeout=10)
    response.raise_for_status()
    data = response.json()
    df = pd.DataFrame(data)

    if not df.empty:
        df["hour"] = pd.to_numeric(df["hour"], errors="coerce")
        df["yhat"] = pd.to_numeric(df["yhat"], errors="coerce")
        df = df.dropna(subset=["hour", "yhat"])
        df["hour"] = df["hour"].astype(int)

    return df


st.markdown('<div class="title">🚕 NY Taxi Traffic Predictor</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Consultá la predicción de tráfico por barrio, día y horario y descubrí oportunidades de pauta.</div>',
    unsafe_allow_html=True
)

# st.markdown('<div class="card">', unsafe_allow_html=True)

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

st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.show_results:
    with st.spinner("Consultando predicción..."):
        try:
            prediction_data = fetch_prediction(selected_borough, selected_day, selected_hour)
            borough_df = fetch_borough_dataset(selected_borough)
            all_df = fetch_all_dataset()

            if prediction_data:
                item = prediction_data[0]

                traffic_value = float(item["yhat"])
                ad_value = calculate_ad_value(traffic_value)

                st.markdown('<div class="result-card">', unsafe_allow_html=True)

                metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

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
                    st.markdown('<div class="small-label">Valor de publicidad</div>', unsafe_allow_html=True)
                    st.markdown(f'<p class="big-number">{ad_value} USD/hora</p>', unsafe_allow_html=True)

                st.info(f"Ad tier: {get_tier_label(ad_value)}")

                st.success(
                    f"El nivel de tráfico para {item['borough']} el día "
                    f"{item['day_name']} a las {format_hour(item['hour'])} es de {int(traffic_value)}"
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

                map_df["borough_key"] = map_df["borough"].str.lower().str.strip()
                map_df["lat"] = map_df["borough_key"].map(lambda x: BOROUGH_COORDS.get(x, {}).get("lat"))
                map_df["lon"] = map_df["borough_key"].map(lambda x: BOROUGH_COORDS.get(x, {}).get("lon"))
                map_df = map_df.dropna(subset=["lat", "lon"])

                #Este es el mapa de New York
                GEOJSON_URL = "https://raw.githubusercontent.com/dwillis/nyc-maps/master/boroughs.geojson"
                geo_data = requests.get(GEOJSON_URL).json()

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

                m = folium.Map(location=[40.7128, -74.0060], zoom_start=11)

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
                    threshold_scale = [0, 1, 100, 500, 1000, 2000, 3000, 4000]
                ).add_to(m)

                # Para hacer interactivo el mapa
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
                    "state_island": {"lat": 40.5795, "lon": -74.1502, "label": "Staten Island"},
                    "manhattan": {"lat": 40.7580, "lon": -73.9855, "label": "Manhattan"},
                    "brooklyn": {"lat": 40.6502, "lon": -73.9442, "label": "Brooklyn"},
                }

                for key, info in BOROUGH_LABELS.items():
                    folium.Marker(
                        location=[info["lat"], info["lon"]],
                        icon=folium.DivIcon(
                            html=f'<div style="font-size:13px; font-weight:700; color:#333; text-shadow: 1px 1px 2px white;">{info["label"]}</div>',
                            icon_size=(120, 30),
                            icon_anchor=(60, 15)
                        )
                    ).add_to(m)

                st_folium(m, use_container_width=True, height=400, returned_objects=[])

                # st.markdown('</div>', unsafe_allow_html=True)

                # Recomendaciones
                # st.markdown('<div class="section-card">', unsafe_allow_html=True)
                # st.markdown('<div class="section-title">Otros horarios o zonas que pueden llegar a interesarte</div>', unsafe_allow_html=True)

                # rec_col1, rec_col2, rec_col3 = st.columns(3)

                # best_slot_same_borough = borough_df.sort_values("yhat", ascending=False).iloc[0]

                # with rec_col1:
                #     st.markdown('<div class="mini-card">', unsafe_allow_html=True)
                #     st.markdown("**Mejor horario en este distrito**")
                #     st.write(
                #         f"{best_slot_same_borough['day_name']} a las {format_hour(best_slot_same_borough['hour'])}"
                #     )
                #     st.write(f"Tráfico estimado: {int(best_slot_same_borough['yhat'])} autos")
                #     st.write(
                #         f"Valor estimado: {calculate_ad_value(best_slot_same_borough['yhat'])} USD/hora"
                #     )
                #     st.markdown('</div>', unsafe_allow_html=True)

                # same_moment_other_boroughs = all_df[
                #     (all_df["day_name"] == selected_day) &
                #     (all_df["hour"] == int(selected_hour)) &
                #     (all_df["borough"] != selected_borough)
                # ].sort_values("yhat", ascending=False)

                # with rec_col2:
                #     st.markdown('<div class="mini-card">', unsafe_allow_html=True)
                #     st.markdown("**Mejor zona alternativa**")
                #     if not same_moment_other_boroughs.empty:
                #         best_other_zone = same_moment_other_boroughs.iloc[0]
                #         st.write(f"{best_other_zone['borough']}")
                #         st.write(
                #             f"{best_other_zone['day_name']} a las {format_hour(best_other_zone['hour'])}"
                #         )
                #         st.write(f"Tráfico estimado: {int(best_other_zone['yhat'])} autos")
                #         st.write(
                #             f"Valor sugerido: {calculate_ad_value(best_other_zone['yhat'])} USD/hora"
                #         )
                #     else:
                #         st.write("No hay zonas alternativas disponibles para ese día y horario.")
                #     st.markdown('</div>', unsafe_allow_html=True)

                # alternative_slots = borough_df[
                #     ~(
                #         (borough_df["day_name"] == selected_day) &
                #         (borough_df["hour"] == int(selected_hour))
                #     )
                # ].sort_values("yhat", ascending=False).head(3)

                # with rec_col3:
                #     st.markdown('<div class="mini-card">', unsafe_allow_html=True)
                #     st.markdown("**Top 3 slots alternativos**")
                #     if not alternative_slots.empty:
                #         for _, row in alternative_slots.iterrows():
                #             st.write(
                #                 f"- {row['day_name']} {format_hour(row['hour'])} · {int(row['yhat'])} autos"
                #             )
                #     else:
                #         st.write("No hay otros slots disponibles.")
                #     st.markdown('</div>', unsafe_allow_html=True)

                # st.markdown('</div>', unsafe_allow_html=True)

                # Gráfico mejores horarios
                st.markdown('<div class="section-title">Mejor día y horario para anunciar en dicho distrito</div>', unsafe_allow_html=True)

                chart_df = borough_df.copy()
                chart_df["slot"] = (
                    chart_df["day_name"] + " " +
                    chart_df["hour"].astype(int).astype(str).str.zfill(2) + ":00"
                )
                chart_df = chart_df.sort_values("yhat", ascending=False).head(10)

                best_slot_chart = (
                    alt.Chart(chart_df)
                    .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
                    .encode(
                        x=alt.X("slot:N", sort="-y", title="Día / Hora"),
                        y=alt.Y("yhat:Q", title="Tráfico estimado"),
                        tooltip=[
                            alt.Tooltip("borough:N", title="Distrito"),
                            alt.Tooltip("day_name:N", title="Día"),
                            alt.Tooltip("hour:Q", title="Hora"),
                            alt.Tooltip("yhat:Q", title="Autos")
                        ]
                    )
                    .properties(height=380)
                )

                st.altair_chart(best_slot_chart, use_container_width=True)
                st.caption("Top 10 horarios con mayor tráfico estimado dentro del distrito seleccionado.")
                st.markdown('</div>', unsafe_allow_html=True)

                # Heatmap
                # st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">Heatmap día / hora del distrito seleccionado</div>', unsafe_allow_html=True)

                heatmap_df = borough_df.copy()

                heatmap = (
                    alt.Chart(heatmap_df)
                    .mark_rect()
                    .encode(
                        x=alt.X("hour:O", title="Hora"),
                        y=alt.Y("day_name:N", sort=day_options, title="Día"),
                        color=alt.Color("yhat:Q", title="Autos"),
                        tooltip=[
                            alt.Tooltip("borough:N", title="Distrito"),
                            alt.Tooltip("day_name:N", title="Día"),
                            alt.Tooltip("hour:Q", title="Hora"),
                            alt.Tooltip("yhat:Q", title="Autos")
                        ]
                    )
                    .properties(height=320)
                )

                st.altair_chart(heatmap, use_container_width=True)
                st.caption("Cuanto más intensa la celda, mayor es el tráfico estimado.")

                # Tabla mejores zonas
                st.markdown('<div class="section-title">Mejores zonas para el día y horario seleccionado</div>', unsafe_allow_html=True)

                best_zones_df = all_df[
                    (all_df["day_name"] == selected_day) &
                    (all_df["hour"] == int(selected_hour))
                ][["borough", "day_name", "hour", "yhat"]].sort_values("yhat", ascending=False)

                best_zones_df = best_zones_df.rename(columns={
                    "borough": "Distrito",
                    "day_name": "Día",
                    "hour": "Hora",
                    "yhat": "Predicción de autos",
                })

                best_zones_df["Hora"] = best_zones_df["Hora"].apply(format_hour)
                best_zones_df["Valor sugerido"] = best_zones_df["Predicción de autos"].apply(calculate_ad_value)

                st.dataframe(best_zones_df, use_container_width=True, hide_index=True)
                st.markdown('</div>', unsafe_allow_html=True)

            else:
                st.warning("No se encontraron datos para esa combinación de filtros.")

        except requests.exceptions.ConnectionError:
            st.error("No se pudo conectar con la API. Verificá que FastAPI esté corriendo en http://127.0.0.1:8000")
        except requests.exceptions.Timeout:
            st.error("La API tardó demasiado en responder.")
        except requests.exceptions.HTTPError as e:
            try:
                error_data = e.response.json()
                st.error(f"Error API: {error_data}")
            except Exception:
                st.error(f"Error API: {e}")
        except Exception as e:
            st.error(f"Error inesperado: {e}")
if not st.session_state.show_results:
    st.info("Seleccioná un distrito, día y hora para ver la predicción y recomendaciones.")
