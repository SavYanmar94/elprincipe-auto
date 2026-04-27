# 🚗 El Principe Garage – Guida Deploy

## Come funziona (architettura semplice)

```
GitHub Actions (ogni notte alle 7:00)
    → Python + Playwright (browser vero, come Octoparse)
        → Legge la pagina Subito.it
            → Salva cars.json nel repository
                → Netlify pubblica il sito aggiornato automaticamente
```

**Nessun server**, nessun costo, tutto gratuito.

---

## STEP 1 – Carica il progetto su GitHub

1. Vai su **github.com** → Login (o crea account)
2. Click **"+"** in alto a destra → **"New repository"**
3. Nome: `elprincipe-auto` → **"Create repository"**
4. Nella pagina del repo: click **"uploading an existing file"**
5. **Trascina l'intera cartella `elprincipe-auto`**
   (deve contenere: `index.html`, `cars.json`, `netlify.toml`, la cartella `.github/`, la cartella `scraper/`)
6. Click **"Commit changes"**

> ⚠️ IMPORTANTE: la cartella `.github` è nascosta su Mac/Linux.
> Per vederla: premi `Cmd+Shift+.` su Mac, oppure su Windows attiva "Mostra file nascosti".
> Puoi anche trascinarla direttamente nel browser GitHub, la vede.

---

## STEP 2 – Deploy su Netlify

1. Vai su **netlify.com** → Sign up (usa GitHub, più veloce)
2. Dashboard → **"Add new site"** → **"Import an existing project"**
3. Seleziona **GitHub** → autorizza Netlify → scegli `elprincipe-auto`
4. Impostazioni:
   - **Build command**: *(lascia VUOTO)*
   - **Publish directory**: `.`  ← solo un punto
5. Click **"Deploy site"**

Il sito è online in 30 secondi. Già funziona con le 7 auto pre-caricate in `cars.json`.

---

## STEP 3 – Verifica che GitHub Actions funzioni

1. Nel tuo repository GitHub → click su **"Actions"** (tab in alto)
2. Dovresti vedere il workflow **"Aggiorna annunci auto da Subito.it"**
3. Per testarlo subito: click sul workflow → **"Run workflow"** → **"Run workflow"** (verde)
4. Aspetta 2-3 minuti → se vedi la spunta verde ✅ tutto funziona
5. Il `cars.json` si aggiorna automaticamente e Netlify pubblica il nuovo sito

> Se vedi una X rossa, aprila e leggi il log — di solito è un problema di permessi.
> Soluzione: vai in **Settings** del repo → **Actions** → **General** →
> "Workflow permissions" → seleziona **"Read and write permissions"** → Save.

---

## STEP 4 – Collega al sito Flazio

**Opzione A – Link diretto** (più semplice):
Aggiungi un bottone nel sito Flazio che porta a:
`https://tuo-nome.netlify.app`

**Opzione B – Iframe** (la pagina appare dentro il sito):
Aggiungi un elemento HTML in Flazio con questo codice:
```html
<iframe
  src="https://tuo-nome.netlify.app"
  style="width:100%; min-height:1000px; border:none; display:block;"
  loading="lazy">
</iframe>
```

**Opzione C – Dominio personalizzato** (più professionale):
In Netlify → Domain settings → aggiungi `auto.elprincipegarage.com`
Poi nel pannello DNS del dominio aggiungi un record CNAME:
`auto → tuo-nome.netlify.app`

---

## Aggiornamento automatico

- Ogni notte alle **07:00** GitHub Actions esegue lo scraper
- Playwright apre un browser vero (non semplice HTTP) e legge Subito.it
- Le auto vengono salvate in `cars.json`
- Netlify rideploya automaticamente (si configura in Netlify → Build hooks)

Per attivare il rideploy automatico:
1. Netlify → Site settings → **Build & deploy** → **Build hooks**
2. Click **"Add build hook"** → nome: "GitHub Actions" → Save
3. Copia l'URL del hook
4. Nel file `.github/workflows/update-cars.yml` sostituisci
   `git push` con anche una chiamata al hook:
   ```
   curl -X POST "https://api.netlify.com/build_hooks/IL_TUO_HOOK"
   ```

---

## Domande frequenti

**Il sito mostra auto vecchie?**
→ Vai su GitHub → Actions → lancia manualmente il workflow.

**Lo scraper smette di funzionare?**
→ Subito.it ha cambiato il layout. Contatta uno sviluppatore per aggiornare `scraper.py`.

**Voglio aggiungere più informazioni alle card?**
→ Modifica `index.html` – la funzione `buildCard()` gestisce ogni card.
