"""Download official M0 evidence; keep raw bytes and a SHA-256 manifest."""
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/raw/m0"
CATALOGUE = "https://www.epa.gov/vehicle-and-fuel-emissions-testing/combining-data-complete-emotor-alpha-maps"
SOURCES = {
    "epa_catalogue.html": CATALOGUE,
    "ornl_2010_prius_pub26762.pdf": "https://info.ornl.gov/sites/publications/files/Pub26762.pdf",
    "toyota_2009_launch.html": "https://global.toyota/en/detail/308252",
    "vw_id3_my23.pdf": "https://www.volkswagen.ie/idhub/content/dam/onehub_pkw/importers/ie/models/product-guides/my23/ID3_MY23.pdf",
    "vw_id3_2020_technical.html": "https://www.volkswagen-newsroom.com/en/the-new-id3-6240/technical-data-6249",
    "vw_id3_my21.pdf": "https://www.volkswagen.ie/idhub/content/dam/onehub_pkw/importers/ie/models/product-guides/2021/my21_master/ID3_MY21.pdf",
    "brembo_09_9908_21.html": "https://www.bremboparts.com/europe/en/view-document/catalogue/disc/09-9908-21",
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []
    for name, url in SOURCES.items():
        try:
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            (OUT / name).write_bytes(response.content)
            manifest.append(dict(file=name, requested_url=url, final_url=response.url,
                                 retrieved_utc=datetime.now(timezone.utc).isoformat(),
                                 bytes=len(response.content), sha256=hashlib.sha256(response.content).hexdigest(),
                                 content_type=response.headers.get("Content-Type"), status="downloaded"))
            print(name, len(response.content))
            if name == "epa_catalogue.html":
                links = re.findall(r'href=[\"\']([^\"\']+)[\"\']', response.text)
                matches = [urljoin(url, x) for x in links if ".zip" in x.lower() and "mg2" in x.lower()]
                if len(matches) != 1:
                    raise ValueError(f"Expected exactly one MG2 ZIP, got {matches}")
                SOURCES_ZIP = matches[0]
                z = requests.get(SOURCES_ZIP, timeout=120)
                z.raise_for_status()
                if not z.content.startswith(b"PK"):
                    raise ValueError("EPA response is not a ZIP")
                zipname = "epa_2010_prius_mg2_emot_2023-04-06.zip"
                (OUT / zipname).write_bytes(z.content)
                manifest.append(dict(file=zipname, requested_url=SOURCES_ZIP, final_url=z.url,
                                     retrieved_utc=datetime.now(timezone.utc).isoformat(), bytes=len(z.content),
                                     sha256=hashlib.sha256(z.content).hexdigest(), status="downloaded"))
                print(zipname, len(z.content), SOURCES_ZIP)
        except Exception as exc:
            manifest.append(dict(file=name, requested_url=url, status="FAILED", error=str(exc)))
            print("FAILED", name, str(exc))
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
