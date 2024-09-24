from flask import Flask, render_template, request, redirect, url_for
import yfinance as yf
import plotly.graph_objects as go
import plotly.io as pio
import numpy as np
import matplotlib.pyplot as plt
import os

app = Flask(__name__)

# Liste des 15 plus grandes capitalisations boursières (exemples de tickers)
top_15_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'BRK-B', 'NVDA', 'META', 'V', 'JPM', 'JNJ', 'WMT', 'PG', 'UNH', 'HD']

# Fonction pour récupérer les données financières
def get_financial_data(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    financials = stock.financials
    cashflow = stock.cashflow
    return info, financials, cashflow

# Fonction pour calculer la note
def calculate_score(info, financials, cashflow):
    score = {
        "Rentabilité": 0, 
        "Analyse des Marges": 0, 
        "Liquidité à court terme": 0, 
        "Solvabilité": 0, 
        "Croissance": 0, 
        "Valorisation": 0
    }

    # 1. Rentabilité (2 points)
    score_rentabilite = 0
    if 'returnOnAssets' in info:
        score_rentabilite += 1 if info['returnOnAssets'] > 0.05 else 0
    if 'returnOnEquity' in info:
        score_rentabilite += 1 if info['returnOnEquity'] > 0.1 else 0
    score["Rentabilité"] = score_rentabilite

    # 2. Analyse des Marges (4 points)
    score_marges = 0
    if 'grossMargins' in info:
        score_marges += 1 if info['grossMargins'] > 0.6 else 0
    if 'ebitdaMargins' in info:
        score_marges += 1 if 0.4 <= info['ebitdaMargins'] <= 0.6 else 0
    if 'operatingMargins' in info:
        score_marges += 1 if 0.3 <= info['operatingMargins'] <= 0.4 else 0
    if 'profitMargins' in info:
        score_marges += 1 if info['profitMargins'] > 0.2 else 0
    score["Analyse des Marges"] = score_marges

    # 3. Liquidité à court terme (2 points)
    score_liquidite = 0
    if 'currentRatio' in info:
        score_liquidite += 1 if info['currentRatio'] > 1 else 0
    if 'quickRatio' in info:
        score_liquidite += 1 if info['quickRatio'] > 1 else 0
    score["Liquidité à court terme"] = score_liquidite

    # 4. Solvabilité (4 points)
    score_solvabilite = 0
    if 'debtToEquity' in info:
        score_solvabilite += 1 if info['debtToEquity'] < 1 else 0
    if 'totalDebt' in info and 'totalAssets' in info:
        score_solvabilite += 1 if info['totalDebt'] / info['totalAssets'] < 0.5 else 0
    if 'longTermDebt' in info and 'equity' in info:
        score_solvabilite += 1 if info['longTermDebt'] / info['equity'] < 1 else 0
    if 'longTermDebt' in info and 'totalAssets' in info:
        score_solvabilite += 1 if info['longTermDebt'] / info['totalAssets'] < 0.5 else 0
    score["Solvabilité"] = score_solvabilite

    # 5. Croissance (3 points)
    score_croissance = 0
    if 'revenueGrowth' in info:
        score_croissance += 1 if info['revenueGrowth'] > 0.1 else 0
    # Croissance sur 3 et 5 ans non disponible directement dans l'API YFinance
    score["Croissance"] = score_croissance

    # 6. Valorisation (5 points)
    score_valorisation = 0
    if 'trailingPE' in info:
        score_valorisation += 1 if info['trailingPE'] < 25 else 0
    if 'priceToBook' in info:
        score_valorisation += 1 if 1 <= info['priceToBook'] <= 2 else 0
    if 'pegRatio' in info:
        score_valorisation += 1 if 1 <= info['pegRatio'] <= 2 else 0
    if 'freeCashFlowYield' in cashflow:
        score_valorisation += 1 if cashflow['Operating Cash Flow'][0] / info['marketCap'] > 0.05 else 0
    if 'bookValue' in info:
        score_valorisation += 1 if info['bookValue'] < 1 else 0
    score["Valorisation"] = score_valorisation

    return score


# Fonction pour afficher un diagramme en constellation
def plot_score(score, ticker):
    labels = list(score.keys())
    values = list(score.values())

    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    values += values[:1]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    
    ax.fill(angles, values, color='skyblue', alpha=0.4)
    ax.plot(angles, values, color='blue', linewidth=2)

    ax.set_yticklabels([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)

    plt.title(f"Score de l'entreprise : {ticker}")

    # Enregistrer l'image temporairement dans le dossier static
    image_path = f"static/{ticker}_score.png"
    plt.savefig(image_path)
    plt.close()
    
    return image_path

# Route pour la page principale
@app.route("/", methods=['GET', 'POST'])
def index():
    top_15_stocks = []

    # Récupérer les données pour chaque entreprise de la liste
    for ticker in top_15_tickers:
        stock = yf.Ticker(ticker)
        info = stock.info
        top_15_stocks.append({
            'name': info.get('longName', ticker),  # Nom de l'entreprise ou ticker si indisponible
            'ticker': ticker,
            'price': info.get('currentPrice', 'N/A'),  # Prix actuel
            'country': info.get('country', 'N/A'),  # Pays
            'market_cap': info.get('marketCap', 'N/A')  # Market Cap
        })

    if request.method == 'POST':
        ticker = request.form.get('ticker')
        if ticker:
            return redirect(url_for('ticker_page', ticker=ticker.upper()))

    return render_template('index.html', top_15_stocks=top_15_stocks)

# Route pour la page d'un ticker spécifique
@app.route("/ticker/<ticker>")
def ticker_page(ticker):
    info, financials, cashflow = get_financial_data(ticker)
    if not info:
        return redirect(url_for('index'))

    # Générer le graphique de type bougie
    history = yf.Ticker(ticker).history(period="1y")
    fig = go.Figure(data=[go.Candlestick(x=history.index,
                                         open=history['Open'],
                                         high=history['High'],
                                         low=history['Low'],
                                         close=history['Close'])])

    fig.update_layout(
        title=f"Cours de l'action {ticker}",
        xaxis_title="Date",
        yaxis_title="Prix",
        xaxis_rangeslider_visible=False,
        xaxis=dict(rangeselector=dict(buttons=list([
            dict(count=1, label="1m", step="month", stepmode="backward"),
            dict(count=6, label="6m", step="month", stepmode="backward"),
            dict(step="all")
        ])))
    )

    graph_html = pio.to_html(fig, full_html=False)

    # Calculer le score des critères
    score = calculate_score(info, financials, cashflow)

    return render_template('ticker.html', ticker=ticker, score=score, graph_html=graph_html)

if __name__ == "__main__":
    app.run(debug=True)