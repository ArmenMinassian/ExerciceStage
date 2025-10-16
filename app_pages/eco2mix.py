from dash import html

eco2mix_layout = html.Div(
    style={
        "backgroundColor": "lightblue",
        "borderRadius": "10px",
        "padding": "20px",
        "margin": "20px",
    },
    children=[
        html.P("TODO :)"),
        html.P("Quelques idées :"),
        html.Ul(
            [
                html.Li("Un sélecteur de date de début/fin"),
                html.Li(
                    "Un dropdown à sélection multiple pour créer une courbe 'somme'"
                ),
                html.Li(
                    [
                        "Une mise à jour du cache, soit par ",
                        html.A(
                            "API",
                            href="https://data.rte-france.com/catalog/-/api/generation/Actual-Generation/v1.1#",
                            target="_blank",
                            rel="noopener noreferrer",
                        ),
                        ", soit en glissant-déposant un fichier",
                    ]
                ),
            ]
        ),
    ],
)
