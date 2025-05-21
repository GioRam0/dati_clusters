import numpy as np
import scipy.stats as st

data = df['colonna'].dropna().values

# Esempio: normal, lognormal, exponential, prova amche con altre distribuzioni
dists = {
    'norm': st.norm,
    'lognorm': st.lognorm,
    'expon': st.expon
}

results = []
for name, dist in dists.items():
    #calcola i parametri di forma piu verosimili quali media deviazione ecc.
    params = dist.fit(data)
    # KS‐test contro la stessa distribuzione con quei parametri
    #prende in input i dati, il nome della distribuzione e i parametri e restituisce statistiche di somiglianza
    #D basso buona aderenza
    #p basso, fifiuti la distri
    D, p = st.kstest(data, name, args=params)
    # AIC approssimativo: 2*k - 2*logL, usando logpdf
    #calcola la logsomiglianza, vogliamo aic basso
    k = len(params)
    logL = np.sum(dist.logpdf(data, *params))
    AIC = 2*k - 2*logL
    #crea una tupla con i vari valori
    results.append((name, params, D, p, AIC))

# Ordina per AIC
results.sort(key=lambda x: x[4])
for r in results:
    print(f"{r[0]:8s}  KS‐D={r[2]:.3f}, p={r[3]:.3f}, AIC={r[4]:.1f}")


#distri con code lunghe
import powerlaw

fit = powerlaw.Fit(data)
print("alpha (esponente Pareto):", fit.alpha)
print("xmin (soglia code):", fit.xmin)
R, p = fit.distribution_compare('power_law', 'lognormal')
print("Confronto power_law vs lognormal:", R, p)

#per gli outliers fai valutazioni sulle singole distribuzioni