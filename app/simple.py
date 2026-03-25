from fastapi import FastAPI

app = FastAPI()

# Define a root `/` endpoint
@app.get('/')
def index():
    return {'ok': True}

def load_model():
    with open("prophet_model.pkl", "rb") as f:
        model = pickle.load(f)
    return model


@app.get("/predict")
def predict(hours):
    hours = int(hours)
    model = load_model()
    future = model.make_future_dataframe(periods=744, freq="h")
    forecast = model.predict(future)

    print(forecast.shape)
    forecast = forecast["yhat"].tail(744)  # len(train_p) + len(periods)
    print(forecast.shape)

    prediction = forecast.iloc[hours]

    return {"traffic": int(prediction)}