import pandas as pd
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State, callback
import plotly.express as px

# Lecture du cache: données de prix SPOT réalisé France
# Téléchargeable à: https://ember-energy.org/data/european-wholesale-electricity-price-data/
df = pd.read_csv("data/France.csv")
df["Datetime (UTC)"] = pd.to_datetime(df["Datetime (UTC)"])
df.sort_values(by="Datetime (UTC)", inplace=True)
min_date: pd.Timestamp = df["Datetime (UTC)"].min()
max_date: pd.Timestamp = df["Datetime (UTC)"].max()



spot_layout = dbc.Container(
    fluid=True,
    className="p-4 bg-light rounded-3 shadow-sm",
    style={
        "backgroundColor": "#e8f4fa",
        "borderRadius": "10px",
        "margin": "20px auto",
        "maxWidth": "1100px"
    },
    children=[
        html.H2("Prix SPOT (France)", className="mb-4 text-start"),

        dbc.Row([
            dbc.Col(
                dbc.ButtonGroup([
                    dbc.Button("Dernière semaine", id="derniere-semaine-button",
                               color="primary", className="me-2", n_clicks=0),
                    dbc.Button("Dernier mois", id="dernier-mois-button",
                               color="secondary", n_clicks=0),
                ]),
                width="auto"
            ),
        ], className="mb-3", justify="start"),

        dbc.Row([
            dbc.Col([
                html.Label("Plage de dates : ", className="fw-bold mb-2 text-start"),
                dcc.DatePickerRange(
                    id="date-picker-range",
                    min_date_allowed=min_date,
                    max_date_allowed=max_date,
                    start_date=max_date - pd.DateOffset(weeks=1),
                    end_date=max_date,
                    display_format="YYYY-MM-DD",
                    clearable=False,
                    style={"padding": "2px", "backgroundColor": "white", "borderRadius": "6px"}
                ),
            ], width="auto"),
        ], className="mb-4", justify="start"),

        # Graphique
        dcc.Graph(id="price-time-series", style={"height": "600px"}),
    ],
)





@callback(
    Output("price-time-series", "figure"),
    Input("date-picker-range", "start_date"),
    Input("date-picker-range", "end_date"),
)
def update_graph(start_date, end_date):
    filtered_df = df[
        (df["Datetime (UTC)"] >= start_date) & (df["Datetime (UTC)"] <= end_date)
    ]

    # La figure principale
    fig = px.line(
        filtered_df,
        x="Datetime (UTC)",
        y="Price (EUR/MWhe)",
        title="Prix SPOT",
    )

    # Ajoute un background rouge quand prix négatif
    negative_prices = filtered_df[filtered_df["Price (EUR/MWhe)"] < 0]
    for i in range(len(negative_prices)):
        start_time = negative_prices["Datetime (UTC)"].iloc[i]
        fig.add_shape(
            type="rect",
            x0=start_time,
            x1=start_time + pd.Timedelta(hours=1),
            y0=filtered_df["Price (EUR/MWhe)"].min(),
            y1=filtered_df["Price (EUR/MWhe)"].max(),
            fillcolor="red",
            opacity=0.2,
            line=dict(width=0),
            layer="below",
        )

    return fig


@callback(
    Output("date-picker-range", "start_date"),
    Output("date-picker-range", "end_date"),
    Input("derniere-semaine-button", "n_clicks"),
    Input("dernier-mois-button", "n_clicks"),
    State("date-picker-range", "start_date"),
    State("date-picker-range", "end_date"),
)
def update_date_range(n_clicks_dernier_mois, n_clicks_six_mois, start_date, end_date):
    ctx = dash.callback_context
    changed_id = ctx.triggered[0]["prop_id"]
    if "derniere-semaine-button" in changed_id:
        return max_date - pd.DateOffset(weeks=1), max_date
    elif "dernier-mois-button" in changed_id:
        return max_date - pd.DateOffset(months=1), max_date
    else:
        return start_date, end_date
