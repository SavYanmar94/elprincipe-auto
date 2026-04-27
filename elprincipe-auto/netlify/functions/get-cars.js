// Netlify Serverless Function - get-cars.js
// Fa scraping della pagina Subito di El Principe e restituisce le auto in JSON

const SHOP_URL = "https://impresapiu.subito.it/shops/54233-el-principe-di-bavaro-biagio";

exports.handler = async function (event, context) {
  const headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type": "application/json",
  };

  try {
    const response = await fetch(SHOP_URL, {
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        Accept:
          "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "it-IT,it;q=0.9",
        "Cache-Control": "no-cache",
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const html = await response.text();
    const cars = parseCarListings(html);

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        success: true,
        updated: new Date().toISOString(),
        count: cars.length,
        cars,
      }),
    };
  } catch (error) {
    console.error("Scraping error:", error);
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({
        success: false,
        error: error.message,
        cars: [],
      }),
    };
  }
};

function parseCarListings(html) {
  const cars = [];

  // Estrae tutti i blocchi annuncio dalla pagina Subito
  // Pattern: cerca i link agli annunci auto
  const adBlockRegex =
    /<li[^>]*>[\s\S]*?<a[^>]+href="(https:\/\/www\.subito\.it\/auto\/[^"]+)"[^>]*>([\s\S]*?)<\/a>[\s\S]*?<\/li>/gi;

  // Approccio più robusto: parse manuale dei dati strutturati
  // Subito inserisce i dati nelle card in modo prevedibile

  // Estrae URL e titolo degli annunci
  const linkRegex =
    /href="(https:\/\/www\.subito\.it\/auto\/[^"]+)"[^>]*title="([^"]+)"/gi;
  const links = [];
  let linkMatch;
  while ((linkMatch = linkRegex.exec(html)) !== null) {
    const url = linkMatch[1];
    const title = linkMatch[2];
    // Evita duplicati
    if (!links.find((l) => l.url === url)) {
      links.push({ url, title });
    }
  }

  // Per ogni link trovato, estrae i dettagli dal contesto HTML circostante
  links.forEach((link) => {
    const urlSlug = link.url.match(/\/([^\/]+)-bari-(\d+)\.htm$/);
    if (!urlSlug) return;

    const adId = urlSlug[2];

    // Cerca il blocco HTML relativo a questo annuncio
    const escapedUrl = link.url.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const blockRegex = new RegExp(
      `href="${escapedUrl}"[\\s\\S]{0,2000}?(?=href="https://www\\.subito\\.it/auto/|$)`,
      "i"
    );
    const blockMatch = html.match(blockRegex);
    const block = blockMatch ? blockMatch[0] : "";

    // Immagine
    const imgRegex = new RegExp(
      `href="${escapedUrl}"[\\s\\S]{0,100}?<img[^>]+src="([^"]+)"`,
      "i"
    );
    // Cerca immagine prima del link nella card
    const imgBeforeRegex = new RegExp(
      `<img[^>]+src="(https://images\\.sbito\\.it[^"]+)"[\\s\\S]{0,500}?${adId}`,
      "i"
    );
    const imgAfterMatch = html.match(imgBeforeRegex);

    let imageUrl = "";
    if (imgAfterMatch) {
      imageUrl = imgAfterMatch[1];
    } else {
      // Fallback: cerca immagine dopo il link
      const imgAfter = block.match(
        /<img[^>]+src="(https:\/\/images\.sbito\.it[^"]+)"/i
      );
      if (imgAfter) imageUrl = imgAfter[1];
    }

    // Prezzo
    const priceMatch = block.match(
      /(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*€|€\s*(\d{1,3}(?:\.\d{3})*)/
    );
    const price = priceMatch ? (priceMatch[1] || priceMatch[2]) + " €" : "";

    // Data pubblicazione
    const dateMatch = block.match(/(Oggi|Ieri|\d{1,2}\s+[A-Za-z]+),?\s+\d{2}:\d{2}/i);
    const publishDate = dateMatch ? dateMatch[0] : "";

    // Dettagli tecnici (km, anno, carburante, cambio)
    // Subito li mette in <li> dentro la card
    const detailsMatch = block.match(
      /<li[^>]*>([\s\S]*?)<\/li>/gi
    );
    const details = [];
    if (detailsMatch) {
      detailsMatch.forEach((li) => {
        const text = li.replace(/<[^>]+>/g, "").trim();
        if (text && text.length > 0 && text.length < 50) details.push(text);
      });
    }

    // Parsing specifico dei dettagli
    let km = "",
      year = "",
      fuel = "",
      transmission = "";

    details.forEach((d) => {
      if (d.match(/\d{2,3}\.\d{3}\s*km/i) || d.match(/km$/i)) km = d;
      else if (d.match(/^20\d{2}$/)) year = d;
      else if (
        d.match(
          /diesel|benzina|gpl|ibrido|elettric|hybrid/i
        )
      )
        fuel = d;
      else if (d.match(/manuale|automatico|semi/i)) transmission = d;
    });

    // Numero foto
    const photoCountMatch = block.match(/>(\d+)<\/span>/);
    const photoCount = photoCountMatch ? photoCountMatch[1] : "0";

    if (link.title && price) {
      cars.push({
        id: adId,
        title: link.title,
        price,
        url: link.url,
        imageUrl: imageUrl.replace("bigthumbs-auto", "large-auto"), // versione più grande
        publishDate,
        km,
        year,
        fuel,
        transmission,
        photoCount,
      });
    }
  });

  return cars;
}
