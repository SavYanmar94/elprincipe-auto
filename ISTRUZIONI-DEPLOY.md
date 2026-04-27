# 🚗 El Principe Garage – Auto in Vendita
## Guida al Deploy su Netlify via GitHub

---

## Come funziona

```
Visitatore apre la pagina
    → Il browser chiama la Netlify Function
        → La Function fa scraping di Subito.it
            → Restituisce le auto come JSON
                → La pagina le mostra come card
```

- **Nessun database**, nessun costo
- Aggiornamento **automatico** ad ogni visita (cache 1 ora)
- Funziona su **piano gratuito** di Netlify

---

## Struttura dei file

```
elprincipe-auto/
├── index.html                    ← La pagina pubblica
├── netlify.toml                  ← Configurazione Netlify
├── package.json
└── netlify/
    └── functions/
        └── get-cars.js           ← Lo scraper (backend serverless)
```

---

## DEPLOY PASSO PER PASSO

### STEP 1 — Carica su GitHub

1. Vai su [github.com](https://github.com) → accedi (o crea account gratuito)
2. Clicca **"New repository"** (verde in alto a destra)
3. Nome: `elprincipe-auto` → **Create repository**
4. Carica i file: clicca **"uploading an existing file"**
5. Trascina TUTTA la cartella `elprincipe-auto` e aspetta il caricamento
6. Clicca **"Commit changes"**

> ⚠️ Assicurati che la struttura sia:
> `netlify/functions/get-cars.js` nella root del repo

---

### STEP 2 — Connetti a Netlify

1. Vai su [netlify.com](https://netlify.com) → **Sign up** (gratuito, anche con GitHub)
2. Dashboard → **"Add new site"** → **"Import an existing project"**
3. Seleziona **GitHub** → autorizza Netlify
4. Scegli il repository `elprincipe-auto`
5. Impostazioni build:
   - **Build command**: *(lascia vuoto)*
   - **Publish directory**: `.` (solo un punto)
6. Clicca **"Deploy site"**

Netlify detecta automaticamente `netlify.toml` e le Functions.

---

### STEP 3 — Personalizza il dominio (opzionale)

Nel pannello Netlify:
- **Domain settings** → puoi usare un sottodominio gratuito tipo:
  `elprincipe-auto.netlify.app`
- Oppure connetti un dominio personalizzato come:
  `auto.elprincipegarage.com` (aggiungendo un record CNAME dal pannello DNS)

---

### STEP 4 — Collega al sito Flazio

Nel sito Flazio, nella pagina Vendita Auto, aggiungi un **iframe**:

```html
<iframe
  src="https://TUO-SITO.netlify.app"
  style="width:100%; height:900px; border:none;"
  loading="lazy">
</iframe>
```

Oppure aggiungi semplicemente un link/bottone che porta alla nuova pagina Netlify.

---

## AGGIORNAMENTO AUTOMATICO GIORNALIERO (opzionale)

Se vuoi che Netlify rifaccia il deploy ogni giorno alle 8:00:

1. Netlify Dashboard → **Site settings** → **Build & deploy** → **Build hooks**
2. Crea un build hook → copia l'URL
3. Vai su [cron-job.org](https://cron-job.org) (gratuito)
4. Crea un nuovo cron job: URL = il tuo build hook, orario = 08:00 ogni giorno
5. Salva

> **Nota:** In realtà non serve perché la Function fa scraping in tempo reale
> ad ogni visita (con cache di 1 ora). Il rebuild giornaliero serve solo
> se vuoi che i cambiamenti si riflettano immediatamente nel CDN.

---

## MANUTENZIONE

- **Nuova auto su Subito** → appare automaticamente entro 1 ora
- **Auto venduta su Subito** → scompare automaticamente entro 1 ora
- **Aggiornamento manuale forzato** → clicca il bottone "Aggiorna" nella pagina

---

## PROBLEMA? Subito blocca le richieste?

Se in futuro Subito dovesse bloccare lo scraping, hai due opzioni:

**Opzione A – Apify (free tier):**
Usa l'API di Apify per Subito (hanno un actor già fatto).
Sostituisci la fetch in `get-cars.js` con la loro API.

**Opzione B – Aggiornamento manuale con JSON:**
Crea un file `cars.json` che aggiorni tu manualmente
e la pagina lo legge direttamente. Più robusto, meno automatico.

---

## Contatti tecnici

Per modifiche alla pagina, aggiornamento stili, o problemi tecnici,
contatta chi ti ha fornito questo progetto.
