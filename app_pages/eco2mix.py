import pandas as pd
import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.express as px
import requests
import dash_bootstrap_components as dbc



# Lecture du cache: données eco2mix annuel consolidé 2024 France
# Téléchargeable à : https://www.rte-france.com/eco2mix/telecharger-les-indicateurs
df = pd.read_csv('data/eCO2mix_RTE_En-cours-Consolide.xls', sep='\t', encoding='latin1',index_col=False)
df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Heures'])
df = df.dropna()
df.sort_values(by="Datetime", inplace=True)

min_date: pd.Timestamp = df["Datetime"].min()
max_date: pd.Timestamp = df["Datetime"].max()

energy_columns = [
    'Fioul', 
    'Charbon',
    'Gaz', 
    'Nucléaire',
    'Eolien', 
    'Solaire', 
    'Hydraulique', 
    'Pompage', 
    'Bioénergies',
    # 'Fioul - TAC', 
    # 'Fioul - Cogén.',
    # 'Fioul - Autres',
    # 'Gaz - TAC',
    # 'Gaz - Cogén.',
    # 'Gaz - CCG',
    # 'Gaz - Autres',
    # 'Hydraulique - Fil de l?eau + éclusée',
    # 'Hydraulique - Lacs', 
    # 'Hydraulique - STEP turbinage',
    # 'Bioénergies - Déchets', 
    # 'Bioénergies - Biomasse',
    # 'Bioénergies - Biogaz', 
    # ' Stockage batterie', 
    # 'Déstockage batterie',
    # 'Eolien terrestre', 
    # 'Eolien offshore'
    ]
  


eco2mix_layout = dbc.Container(
    fluid=True,
    className="p-4 bg-light rounded-3 shadow-sm",
    style={
        "backgroundColor": "#e8f4fa",  
        "borderRadius": "10px",
        "margin": "20px auto",
        "maxWidth": "1200px"
    },
    children=[
        # Titre aligné à gauche
        html.H2("Visualisation des données Eco2Mix 2024", className="mb-4 text-start"),

        # Ligne du sélecteur de dates
        dbc.Row([
            dbc.Col([
                html.Label("Plage de dates :", className="fw-bold mb-2 text-start"),
                dcc.DatePickerRange(
                    id="eco2mix-date-picker-range",
                    min_date_allowed=min_date,
                    max_date_allowed=max_date,
                    start_date=max_date - pd.DateOffset(weeks=1),
                    end_date=max_date,
                    display_format="YYYY-MM-DD",
                    clearable=False,
                    style={
                        "padding": "5px",
                        "backgroundColor": "white",
                        "borderRadius": "6px"
                    },
                ),
            ], width="auto"),
        ], className="mb-4", justify="start"),

        # Sélecteur des colonnes d'énergie
        dbc.Row([
            dbc.Col([
                html.Label("Sources d'énergie à visualiser :", className="fw-bold mb-2 text-start"),
                dcc.Dropdown(
                    id="eco2mix-dropdown",
                    options=[{"label": col, "value": col} for col in energy_columns],
                    value=energy_columns,
                    multi=True,
                    placeholder="Sélectionnez les sources à afficher",
                    className="mb-4"
                ),
            ], width=6)
        ], justify="start"),

        # Graphiques
        dbc.Row([
            dbc.Col(dcc.Graph(id="conso-time-series", style={"height": "450px"}), width=12, className="mb-4"),
            dbc.Col(dcc.Graph(id="conso-stacked-area", style={"height": "450px"}), width=12, className="mb-4"),
            dbc.Col(dcc.Graph(id="conso-comparative", style={"height": "450px"}), width=12)
        ]),
    ],
)


default_sources = energy_columns

@callback(
    Output("conso-time-series", "figure"),
    Output("conso-stacked-area", "figure"),
    Output("conso-comparative", "figure"),   
    Input("eco2mix-date-picker-range", "start_date"),
    Input("eco2mix-date-picker-range", "end_date"),
    Input("eco2mix-dropdown", "value"),
    Input("conso-time-series", "relayoutData")
)
def update_graphs(start_date, end_date, selected_sources, relayoutData):
    if not selected_sources:
        selected_sources = default_sources

    # Filtrage des données
    filtered_df = df[
        (df["Datetime"] >= start_date) & (df["Datetime"] <= end_date)
    ].copy()

    # Calcul de la somme pour le premier graphique
    filtered_df["Somme"] = filtered_df[selected_sources].sum(axis=1)

    # FIG1 : Courbes séparées
    fig1 = px.line(
        filtered_df,
        x="Datetime",
        y=[],
        title="Puissance par source d'énergie",
        labels={"Datetime": "Datetime", "value": "Puissance (MW)"},
    )
    fig1.add_scatter(
        x=filtered_df["Datetime"],
        y=filtered_df["Somme"],
        mode="lines",
        name="Somme",
        line=dict(width=3, dash="dot")
    )
    for source in selected_sources:
        fig1.add_scatter(
            x=filtered_df["Datetime"],
            y=filtered_df[source],
            mode="lines",
            name=source,
        )

    # FIG2 : Courbes empilées
    
    # Sources triées selon leur moyenne décroissante
    order = (
        filtered_df[selected_sources]
        .mean()
        .sort_values(ascending=False)
        .index
        .tolist()
    )
    melted_df = filtered_df.melt(
        id_vars="Datetime",
        value_vars=selected_sources,
        var_name="Source",
        value_name="Puissance"
    )
    melted_df["Source"] = pd.Categorical(
        melted_df["Source"],
        categories=order,
        ordered=True
    )

    fig2 = px.area(
        melted_df,
        x="Datetime",
        y="Puissance",
        color="Source",
        category_orders={"Source": order},
        title="Puissance sommée des sources d'énergie",
        labels={"Datetime": "Datetime", "Puissance": "Puissance (MW)"}
    )
    fig2.update_layout(legend_title_text="")
    
    # FIG3 : Consommation et prévisions     
    fig3 = px.line(
        filtered_df,
        x="Datetime",
        y=["Consommation", "Prévision J-1", "Prévision J"],
        title="Consommation et prévisions",
        labels={"value": "Puissance (MW)", "Datetime": "Datetime", "variable": ""}
    )
    
    # Synchronisation du zoom si relayoutData contient un zoom sur l'axe X
    if relayoutData and "xaxis.range[0]" in relayoutData:
        xmin = relayoutData["xaxis.range[0]"]
        xmax = relayoutData["xaxis.range[1]"]

        fig1.update_xaxes(range=[xmin, xmax])
        fig2.update_xaxes(range=[xmin, xmax])
        fig3.update_xaxes(range=[xmin, xmax])

    return fig1, fig2, fig3

