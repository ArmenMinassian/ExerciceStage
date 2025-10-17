from dash import dcc, html, Input, Output, callback, State
import os
import pandas as pd
import pickle
import base64
import io

model_files = [f for f in os.listdir("models") if f.endswith(".pkl")]
prev_spot_layout = html.Div(
    style={
        "backgroundColor": "lightblue",
        "borderRadius": "10px",
        "padding": "20px",
        "margin": "20px",
    },
    children=[
        html.H2("Prévisions de prix SPOT"),
        dcc.Upload(
            id="upload-data",
            children=html.Div(
                ["Glisser-déposer ou sélectionner un fichier CSV à importer"]
            ),
            style={
                "width": "100%",
                "height": "60px",
                "lineHeight": "60px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
                "margin": "10px",
            },
            multiple=False,
        ),
        html.Div(id="output-data-upload"),
        html.P(
            [
                "Veuillez importer un fichier CSV contenant les données historiques (téléchargé depuis ",
                html.A(
                    "eco2mix",
                    href="https://www.rte-france.com/eco2mix/telecharger-les-indicateurs",
                    target="_blank",
                    rel="noopener noreferrer",
                ),
                ").",
            ]
        ),
        html.H3("Sélectionner un modèle:"),
        dcc.Dropdown(
            id="model-dropdown",
            options=[{"label": f, "value": f} for f in model_files],
            placeholder="Sélectionner un modèle",
        ),
        html.Button("Lancer les prévisions", id="run-forecasts-button", n_clicks=0),
        html.Div(id="forecast-output"),
    ],
)


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

        # Si l'import a réussi, affiche le nom du fichier et ses premières lignes
        return html.Div([html.H5(filename), html.Hr(), html.Div(df.head().to_string())])
    except Exception as e:
        print(e)
        return html.Div(["There was an error processing this file."])


@callback(
    Output("forecast-output", "children"),
    Input("run-forecasts-button", "n_clicks"),
    State("model-dropdown", "value"),
    State("upload-data", "contents"),
)
def run_forecasts(n_clicks, model_filename, contents):
    if not (n_clicks > 0 and model_filename and contents):
        return html.Div()

    try:
        _, content_string = contents.split("base64,")
        decoded = base64.b64decode(content_string)
        df = pd.read_csv(
            io.StringIO(decoded.decode("latin1")), sep="\t", index_col=False
        ).iloc[:-1]

        with open(f"models/{model_filename}", "rb") as file:
            model = pickle.load(file)
        try:
            # TODO: exploiter `previsions_prix_spot`
            previsions_prix_spot = model.predict(
                df[model.feature_names_in_].replace("ND", float("nan")).dropna()
            )
        except Exception as e:
            return html.Div([f"Erreur lors de l'exécution du modèle: {e}"])

        return html.Div(
            ["Prévisions lancées avec succès! (Affichage des résultats à implémenter)"]
        )
    except Exception as e:
        return html.Div([f"Erreur lors du chargement ou de l'exécution du modèle: {e}"])
