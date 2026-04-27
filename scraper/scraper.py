"""
scraper.py - El Principe Garage
Usa Playwright (browser headless) per leggere la pagina Subito
esattamente come fa Octoparse: esegue il JavaScript, aspetta il caricamento,
poi estrae i dati. Salva tutto in cars.json.
"""

import asyncio
import json
import re
import os
from datetime import datetime, timezone
from playwright.async_api import async_playwright

SHOP_URL = "https://impresapiu.subito.it/shops/54233-el-principe-di-bavaro-biagio"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "cars.json")


async def scrape():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Avvio scraping: {SHOP_URL}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="it-IT",
            viewport={"width": 1280, "height": 900},
        )

        page = await context.new_page()

        # Blocca risorse inutili per velocità
        await page.route(
            "**/*.{woff,woff2,ttf,otf}",
            lambda r: r.abort()
        )

        print("  → Caricamento pagina...")
        await page.goto(SHOP_URL, wait_until="domcontentloaded", timeout=30000)

        # Aspetta che le card degli annunci siano visibili
        print("  → Attesa caricamento annunci...")
        try:
            await page.wait_for_selector(
                "li.item-card, article[class*='item'], .items-list li, [class*='AdCard'], [class*='card-body']",
                timeout=15000,
            )
        except Exception:
            # Prova un selettore più generico
            await page.wait_for_selector("a[href*='/auto/']", timeout=10000)

        # Scroll per triggerare lazy loading
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)
        await page.evaluate("window.scrollTo(0, 0)")
        await asyncio.sleep(1)

        # Estrai tutti gli annunci
        cars = await page.evaluate("""
            () => {
                const results = [];
                const seen = new Set();

                // Cerca tutti i link ad annunci auto
                const links = document.querySelectorAll('a[href*="subito.it/auto/"]');

                links.forEach(link => {
                    const url = link.href;
                    if (!url || seen.has(url)) return;

                    // Filtra solo URL annunci (contengono ID numerico finale)
                    if (!/bari-\\d+\\.htm$/.test(url)) return;
                    seen.add(url);

                    // Risali al contenitore della card
                    let card = link;
                    for (let i = 0; i < 6; i++) {
                        if (!card.parentElement) break;
                        card = card.parentElement;
                    }

                    // Titolo
                    let title = link.title || link.getAttribute('title') || '';
                    if (!title) {
                        const h2 = link.querySelector('h2') || card.querySelector('h2, h3, [class*="title"]');
                        title = h2 ? h2.innerText.trim() : '';
                    }
                    if (!title) title = link.innerText.trim().split('\\n')[0];

                    // Prezzo
                    let price = '';
                    const priceEl = card.querySelector('[class*="price"], [class*="Price"], .price');
                    if (priceEl) {
                        price = priceEl.innerText.trim().replace(/\\s+/g, ' ');
                    }
                    if (!price) {
                        const allText = card.innerText;
                        const m = allText.match(/(\\d{1,3}(?:\\.\\d{3})*)\\s*€/);
                        if (m) price = m[1] + ' €';
                    }

                    // Immagine
                    let imageUrl = '';
                    const img = link.querySelector('img') || card.querySelector('img[src*="sbito.it"], img[src*="subito"]');
                    if (img) {
                        imageUrl = img.src || img.dataset.src || img.getAttribute('data-original') || '';
                        // Upgrade qualità immagine
                        imageUrl = imageUrl.replace('bigthumbs-auto', 'large-auto');
                    }

                    // Data
                    let publishDate = '';
                    const dateEl = card.querySelector('[class*="date"], [class*="Date"], time');
                    if (dateEl) publishDate = dateEl.innerText.trim();
                    if (!publishDate) {
                        const m = card.innerText.match(/(Oggi|Ieri|\\d{1,2}\\s+[A-Za-z]+),?\\s+\\d{2}:\\d{2}/i);
                        if (m) publishDate = m[0];
                    }

                    // Specifiche tecniche (chip/tag sotto la card)
                    const specs = [];
                    const specEls = card.querySelectorAll('li, [class*="feature"], [class*="spec"], [class*="tag"], [class*="chip"]');
                    specEls.forEach(el => {
                        const t = el.innerText.trim();
                        if (t && t.length < 40 && t.length > 1) specs.push(t);
                    });

                    // Parse specs
                    let km = '', year = '', fuel = '', transmission = '';
                    specs.forEach(s => {
                        if (/\\d{2,3}\\.\\d{3}\\s*km|^\\d+\\s*km$/i.test(s)) km = s;
                        else if (/^20\\d{2}$/.test(s)) year = s;
                        else if (/diesel|benzina|gpl|hybrid|elettr/i.test(s)) fuel = s;
                        else if (/manuale|automatico|semi/i.test(s)) transmission = s;
                    });

                    // Numero foto
                    let photoCount = '';
                    const photoEl = card.querySelector('[class*="photo"], [class*="count"], span[class*="number"]');
                    if (photoEl) {
                        const m = photoEl.innerText.match(/\\d+/);
                        if (m) photoCount = m[0];
                    }

                    if (title && price) {
                        results.push({ url, title, price, imageUrl, publishDate, km, year, fuel, transmission, photoCount });
                    }
                });

                return results;
            }
        """)

        await browser.close()

        if not cars:
            # Fallback: dump HTML per debug
            print("  ⚠️  Nessuna auto trovata con il selettore principale, provo fallback...")
            async with async_playwright() as p2:
                b2 = await p2.chromium.launch(headless=True, args=["--no-sandbox"])
                pg2 = await b2.new_context().new_page()
                await pg2.goto(SHOP_URL, wait_until="networkidle", timeout=40000)
                await asyncio.sleep(3)
                cars = await pg2.evaluate("""
                    () => {
                        const results = [];
                        const seen = new Set();
                        document.querySelectorAll('a[href]').forEach(a => {
                            const url = a.href;
                            if (!/subito\\.it\\/auto\\/.+-\\d+\\.htm/.test(url) || seen.has(url)) return;
                            seen.add(url);
                            const title = a.title || a.innerText.trim().split('\\n')[0] || '';
                            if (title.length > 5) {
                                results.push({ url, title, price: '', imageUrl: '', publishDate: '', km: '', year: '', fuel: '', transmission: '', photoCount: '' });
                            }
                        });
                        return results;
                    }
                """)
                await b2.close()

    output = {
        "success": True,
        "updated": datetime.now(timezone.utc).isoformat(),
        "count": len(cars),
        "cars": cars,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"  ✅ Trovate {len(cars)} auto → salvate in cars.json")
    return len(cars)


if __name__ == "__main__":
    asyncio.run(scrape())
