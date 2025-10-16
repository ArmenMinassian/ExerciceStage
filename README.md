Cette application Dash est composée de 3 onglets, et a été conçue comme exercice de recrutement pour un stage à EDF.

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

## Configuration
Télécharger les données "En-cours annuel consolidé" d'[éCO2mix](https://www.rte-france.com/eco2mix/la-production-delectricite-par-filiere) sur [ce lien](https://www.rte-france.com/eco2mix/telecharger-les-indicateurs). \
Attention, le format du fichier téléchargé est un .csv (séparé par des tabulations), et pas un .xls comme l'extension le laisse penser... :)

Les prix SPOT de l'électricité peuvent être téléchargés [ici](https://ember-energy.org/data/european-wholesale-electricity-price-data/).
Choisir "hourly", puis récupérer le fichier "France.csv"

## Ajout de modèle de prévision de prix SPOT
A votre charge de créer un ou plusieurs modèles (simples, l'objectif n'est pas la performance) de prévision de prix SPOT pour les intégrer dans le dossier "models". Chacun de ces modèles doivent être des .pkl (voir [pickle](https://docs.python.org/3/library/pickle.html)) implémentant une méthode `predict()` (comme la quasi-totalité des modèles de sklearn)
