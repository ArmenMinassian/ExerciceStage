from dash import dcc, html, Input, Output, callback, State, dash_table
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_squared_error
import dash_bootstrap_components as dbc
import sklearn
import os
import pandas as pd
import pickle
import base64
import io
import numpy as np
import requests
import plotly.express as px
from dash.exceptions import PreventUpdate
import joblib

# Chargement des modèles et du scaler
model_files = [f for f in os.listdir("models") if f.endswith(".pkl")]
scaler_file = [f for f in os.listdir("models") if f.endswith(".joblib")]


# Données Spot
df_spot = pd.read_csv("data/France.csv")
df_spot["Datetime (UTC)"] = pd.to_datetime(df_spot["Datetime (UTC)"])
df_spot.sort_values(by="Datetime (UTC)", inplace=True)

prev_spot_layout = dbc.Container(
    style={"backgroundColor": "lightblue", "borderRadius": "10px", "padding": "20px", "margin": "20px"},
    children=[
        html.H2("Prévisions de prix SPOT"),
        dcc.Tabs([
            dcc.Tab(label="Importer un fichier", children=[
                dbc.Card([
                    dbc.CardBody([
                        dcc.Upload(
                            id="upload-data",
                            children=html.Div(["Glisser-déposer ou sélectionner un fichier CSV"]),
                            style={
                                "width": "100%", "height": "60px", "lineHeight": "60px",
                                "borderWidth": "1px", "borderStyle": "dashed", "borderRadius": "5px",
                                "textAlign": "center", "margin": "10px"
                            },
                            multiple=False,
                        ),
                        html.Div(id="output-data-upload"),
                        html.P([
                            "Veuillez importer un fichier CSV contenant les données historiques (ex: ",
                            html.A("eCO2mix_RTE_YYYY-MM-DD.xls",
                                   href="https://www.rte-france.com/eco2mix/telecharger-les-indicateurs",
                                   target="_blank"),
                            ")."
                        ], className="mt-2 text-muted"),
                    ])
                ], className="mb-4 shadow-sm"),
            ]),
            dcc.Tab(label="Appeler l'API", children=[
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            dcc.DatePickerRange(
                                id="api-date-range",
                                display_format="YYYY-MM-DD",
                                start_date_placeholder_text="Début",
                                end_date_placeholder_text="Fin",
                                min_date_allowed=None,
                                max_date_allowed=None,
                                style={"width": "300px", "marginRight": "10px"},
                            ),
                            dbc.Button("Récupérer les données depuis l'API",
                                       id="call-api-button",
                                       n_clicks=0,
                                       color="primary"),
                        ], className="d-flex align-items-center mb-3"),
                        html.Div(id="api-data-output"),
                        dcc.Store(id="api-data-store"),
                    ])
                ], className="mb-4 shadow-sm"),
            ]),
        ]),
        html.H3("Sélectionner un modèle :", className="mt-4"),
        dcc.Dropdown(
            id="model-dropdown",
            options=[{"label": f, "value": f} for f in model_files],
            placeholder="Sélectionner un modèle",
            className="mb-3",
        ),
        dbc.Button("Lancer les prévisions",
                   id="run-forecasts-button",
                   n_clicks=0,
                   color="success"),
        html.Div(id="forecast-output", className="mt-4"),
    ],
    fluid=True,
    className="p-4 bg-light rounded-3 shadow-sm"
)


### Chargement des données depuis un csv

@callback(
    Output("output-data-upload", "children"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
)
def upload_input_file(contents, filename):
    if contents is None:
        return html.Div()
    try:
        # Les fichiers eCO2mix_RTE_*.xls sont en réalité des .csv séparés par des \t
        # Ils sont encodés en latin1 (présence d'accents),
        # et la dernière ligne est un message d'avertissement, à supprimer
        _, content_string = contents.split("base64,")
        decoded = base64.b64decode(content_string)
        df = pd.read_csv(
            io.StringIO(decoded.decode("latin1")), sep="\t", index_col=False
        ).iloc[:-1]
        
        # Affichage du nom de fichier + DataFrame avec dash_table
        return html.Div([
            html.H5(filename),
            html.Hr(),
            dash_table.DataTable(
                columns=[{"name": i, "id": i} for i in df.columns],
                data=df.head(10).to_dict("records"),  # afficher les 10 premières lignes
                page_size=10,                          
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '5px',
                    'whiteSpace': 'normal',
                    'height': 'auto'
                },
            )
        ])
    except Exception as e:
        print(e)
        return html.Div(["Erreur lors du chargement du fichier."])
    
    
    
### Limiter les dates appelées avec l'API
@callback(
    Output("api-date-range", "min_date_allowed"),
    Output("api-date-range", "max_date_allowed"),
    Input("api-date-range", "id")  
)
def set_date_range(_):
    try:
        url = "https://odre.opendatasoft.com/api/records/1.0/search/"
        params = {
            "dataset": "eco2mix-national-tr",
            "rows": 10000,
            "sort": "-date"
        }
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise Exception("Erreur API")

        data_json = response.json()
        records = data_json.get("records", [])
        if not records:
            raise Exception("Aucune donnée récupérée")

        df_tmp = pd.json_normalize(records)
        df_tmp["fields.date"] = pd.to_datetime(df_tmp["fields.date"])
        
        min_date = df_tmp["fields.date"].min().date()
        max_date = df_tmp["fields.date"].max().date()

        return min_date, max_date

    except Exception as e:
        print(f"Erreur lors de la récupération des dates : {e}")
        return None, None


### Chargement des données depuis l'API

@callback(
    Output("api-data-output", "children"),
    Output("api-data-store", "data"),
    Input("call-api-button", "n_clicks"),
    State("api-date-range", "start_date"),
    State("api-date-range", "end_date"),
)
def call_api_multiple_days(n_clicks, start_date, end_date):
    if n_clicks == 0:
        return html.Div(), None
    
    if not start_date or not end_date:
        return html.Div(["Veuillez sélectionner une plage de dates."]), None

    try:
        url = "https://odre.opendatasoft.com/api/records/1.0/search/"
        params = {
            "dataset": "eco2mix-national-tr",
            "rows": 10000,             
            "sort": "-date"
        }

        response = requests.get(url, params=params)
        if response.status_code != 200:
            return html.Div([f"Erreur API: {response.status_code}"]), None

        data_json = response.json()
        records = data_json.get("records", [])

        if not records:
            return html.Div(["Aucune donnée trouvée."]), None

        df = pd.json_normalize(records)
        
        # Conversion et filtrage des dates
        df["fields.date"] = pd.to_datetime(df["fields.date"])
        mask = (df["fields.date"] >= pd.to_datetime(start_date)) & \
               (df["fields.date"] <= pd.to_datetime(end_date))
        df = df.loc[mask].dropna()

        if df.empty:
            return html.Div([f"Aucune donnée trouvée entre {start_date} et {end_date}."]), None

        df_store = df.to_json(date_format="iso", orient="split")

        return html.Div([
            html.H5(f"{len(df)} lignes récupérées du {start_date} au {end_date}"),
            html.Hr(),
            dash_table.DataTable(
                columns=[{"name": i, "id": i} for i in df.columns],
                data=df.head(20).to_dict("records"),
                page_size=10,
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '5px',
                    'whiteSpace': 'normal',
                    'height': 'auto'
                },
            )
        ]), df_store

    except Exception as e:
        return html.Div([f"Erreur lors de l'appel API: {e}"]), None

### Prédiction et visualisation

@callback(
    Output("forecast-output", "children"),
    Input("run-forecasts-button", "n_clicks"),
    State("model-dropdown", "value"),
    State("upload-data", "contents"),
    State("api-data-store", "data"),
)
def run_forecasts(n_clicks, model_filename, contents, api_data):
    if n_clicks == 0 or not model_filename:
        return html.Div()

    try:
        # Chargement des données
        if contents:  # cas 1 : fichier local
            _, content_string = contents.split("base64,")
            decoded = base64.b64decode(content_string)
            df = pd.read_csv(io.StringIO(decoded.decode("latin1")), sep="\t", index_col=False).iloc[:-1]
            source = "fichier importé"

        elif api_data:  # cas 2 : données API eCO2mix
            df = pd.read_json(io.StringIO(api_data), orient="split")

            # Transformation des noms de colonnes
            df = df.rename(columns={
                'fields.heure': 'Heures',
                'fields.date': 'Date',
                'fields.prevision_j1': 'Prévision J-1',
                'fields.prevision_j': 'Prévision J',
                'fields.fioul_tac': 'Fioul - TAC',
                'fields.nucleaire': 'Nucléaire',
                'fields.ech_comm_angleterre': 'Ech. comm. Angleterre',
                'fields.gaz_tac': 'Gaz - TAC',
                'fields.bioenergies_biogaz': 'Bioénergies - Biogaz',
                'fields.bioenergies_biomasse': 'Bioénergies - Biomasse',
                'fields.destockage_batterie': 'Déstockage batterie',
                'fields.charbon': 'Charbon',
                'fields.hydraulique_step_turbinage': 'Hydraulique - STEP turbinage',
                'fields.stockage_batterie': ' Stockage batterie',
                'fields.pompage': 'Pompage',
                'fields.gaz_ccg': 'Gaz - CCG',
                'fields.hydraulique_lacs': 'Hydraulique - Lacs',
                'fields.eolien_terrestre': 'Eolien terrestre',
                'fields.ech_comm_allemagne_belgique': 'Ech. comm. Allemagne-Belgique',
                'fields.fioul': 'Fioul',
                'fields.solaire': 'Solaire',
                'fields.ech_comm_italie': 'Ech. comm. Italie',
                'fields.bioenergies': 'Bioénergies',
                'fields.gaz_autres': 'Gaz - Autres',
                'fields.fioul_cogen': 'Fioul - Cogén.',
                'fields.gaz_cogen': 'Gaz - Cogén.',
                'fields.hydraulique_fil_eau_eclusee': 'Hydraulique - Fil de l?eau + éclusée',
                'fields.hydraulique': 'Hydraulique',
                'fields.ech_comm_suisse': 'Ech. comm. Suisse',
                'fields.eolien_offshore': 'Eolien offshore',
                'fields.ech_comm_espagne': 'Ech. comm. Espagne',
                'fields.taux_co2': 'Taux de Co2',
                'fields.eolien': 'Eolien',
                'fields.ech_physiques': 'Ech. physiques',
                'fields.bioenergies_dechets': 'Bioénergies - Déchets',
                'fields.consommation': 'Consommation',
                'fields.gaz': 'Gaz',
                'fields.fioul_autres': 'Fioul - Autres'
            })
            source = "API eCO2mix"

        else:
            return html.Div(["Aucune donnée disponible (ni fichier ni API)."])
        
        if not hasattr(DecisionTreeRegressor, "monotonic_cst"):
             print("cc")
             DecisionTreeRegressor.monotonic_cst = None
        
        # Chargement du modèle
        with open(f"models/{model_filename}", "rb") as file:
            # model = pickle.load(file)
            model = joblib.load(f"models/{model_filename}")
        # Chargement du scaler
        if scaler_file:
            scaler_path = os.path.join("models", scaler_file[0])
            scaler = joblib.load(scaler_path)
        else:
            print("Aucun scaler .joblib trouvé dans /models")

        # Vérification que les features du modèle sont présentes dans le dataframe
        missing_cols = [c for c in model.feature_names_in_ if c not in df.columns]
        if missing_cols:
            return html.Div([
                f"Les colonnes suivantes sont absentes des données ({source}) : {missing_cols}"
            ])

        # Prédiction
        X = df[model.feature_names_in_].replace("ND", float("nan")).dropna()
        X_scaled = scaler.transform(X)
        y_pred = model.predict(X_scaled)

        if "Date" in df.columns and "Heures" in df.columns:
            df["Datetime"] = pd.to_datetime(df["Date"] + " " + df["Heures"])
        elif "date" in df.columns:
            df["Datetime"] = pd.to_datetime(df["date"])
        else:
            df["Datetime"] = pd.date_range(start="2024-01-01", periods=len(y_pred), freq="H")

        df_pred = df.loc[X.index].copy()
        df_pred["Prix Spot Prédit"] = y_pred

        # Jointure avec prix réels
        df_pred["Datetime"] = pd.to_datetime(df_pred["Datetime"])
        df_spot["Datetime (Local)"] = pd.to_datetime(df_spot["Datetime (Local)"])
        df_eval = pd.merge(df_pred, df_spot, left_on="Datetime", right_on="Datetime (Local)", how="inner")
        df_eval = df_eval.rename(columns={"Price (EUR/MWhe)": "Prix Spot Réel"})
        df_eval = df_eval.sort_values(by="Datetime").reset_index(drop=True)
        
        # Calcul erreur de prédiction
        rmse = np.sqrt(mean_squared_error(df_eval["Prix Spot Réel"], df_eval["Prix Spot Prédit"]))


        # Visualisation
        fig = px.line(
            df_eval,
            x="Datetime",
            y=["Prix Spot Prédit", "Prix Spot Réel"],
            title=f"Comparaison des prix prédits et réels ({source})",
            labels={"value": "Prix (EUR/MWhe)", "variable": "Type"},
        )
        fig.update_layout(xaxis_title="Date", yaxis_title="Prix")

        return html.Div([
            html.H4(f"Prévisions réalisées avec succès à partir du {source}"),
            dcc.Graph(figure=fig),
            html.P(f"RMSE du modèle : {rmse:.2f}", style={"fontWeight": "bold", "marginTop": "10px"})
        ])

    except Exception as e:
        return html.Div([f"Erreur lors du chargement ou de l'exécution du modèle: {e}"])


