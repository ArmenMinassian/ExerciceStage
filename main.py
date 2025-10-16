from dash import Dash, dcc, html, Input, Output, callback
from app_pages.eco2mix import eco2mix_layout
from app_pages.spot import spot_layout
from app_pages.prev_spot import prev_spot_layout
import dash_bootstrap_components as dbc

"""
 Cette application Dash est composée de 3 onglets, et a été conçue comme exercice de recrutement
 pour un stage à EDF.

 ## Lien vers la documentation officielle de plotly:
 https://dash.plotly.com/

 ## Comment lancer cette application ?
 1. Assurez-vous d'avoir les dépendances (cf requirements.txt) dans votre environnement python
 2. Depuis un terminal, exécutez la commande suivante pour lancer l'application :
    ```
    python main.py
    ```
 4. Le message ci-dessous doit s'afficher dans la console.
 Faites un Ctrl+Click sur (ou copiez-collez) le lien `http://127.[...]` pour ouvrir l'application dans votre navigateur par défaut:
 ```
 Dash is running on http://127.0.0.1:8050/

 * Serving Flask app 'main'
 * Debug mode: on
 ```

"""


app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
)

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Accueil", href="/")),
        dbc.NavItem(dbc.NavLink("Données éco2mix 2024", href="/eco2mix")),
        dbc.NavItem(dbc.NavLink("Données SPOT", href="/spot")),
        dbc.NavItem(dbc.NavLink("Prévision de prix SPOT", href="/prev_spot")),
    ],
    id="my_nvb",
    color="dark",
    dark=True,
    className="mb-2",
)

app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        navbar,
        dbc.Container(id="page-content", className="mb-4", fluid=True),
    ]
)

home_layout = html.Div(
    children=[
        html.H1(children="Exercice de stage"),
        html.P("Cette application est composée de trois sous-pages:"),
        html.Ul(
            children=[
                html.Li("Une page pour visualiser les données d'éco2mix de 2024"),
                html.Li("Une page pour visualiser les prix SPOT historiques"),
                html.Li(
                    "Une page pour réaliser (et visualiser !) les prévisions de prix SPOT"
                ),
            ]
        ),
    ]
)


@callback(Output("page-content", "children"), Input("url", "pathname"))
def display_page(pathname):
    if pathname == "/":
        return home_layout
    elif pathname == "/eco2mix":
        return eco2mix_layout
    elif pathname == "/spot":
        return spot_layout
    elif pathname == "/prev_spot":
        return prev_spot_layout
    else:
        return html.Div(
            [
                html.H1("404: Not found", className="text-danger"),
                html.Hr(),
                html.P(f"L'url {pathname} n'est pas reconnue..."),
            ]
        )


app.run(debug=True)
