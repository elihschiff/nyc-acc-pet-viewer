#!/usr/bin/env python3
"""Fetch NYC ACC pet data and generate an interactive browser page."""

import json
import os
import subprocess
import webbrowser

API_BASE = "https://pets.mcgilldevtech.com"
API_KEY = "jKbOSNYtJn5qhYbsv9IKL6OEt7etN6jcALlerH82"

GRAPHQL_QUERY = """{
  feed {
    updated
    pets {
      id name age type species link gender
      summary summaryHtml weight size
      location locationInShelter
      spayedNeutered breeds colors
      photos youTubeIds intakeDate
    }
  }
}"""


def curl_post(url, headers, body):
    cmd = ["curl", "-s", "-X", "POST", url]
    for k, v in headers.items():
        cmd += ["-H", f"{k}: {v}"]
    cmd += ["-d", json.dumps(body)]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def fetch_pets():
    print("Fetching token...")
    token_resp = curl_post(f"{API_BASE}/token", {
        "Content-Type": "application/json; charset=UTF-8",
        "x-api-key": API_KEY,
    }, {
        "deviceId": "nycacc-browser-script",
        "organization": "accofnyc",
    })
    token = token_resp["access_token"]

    print("Fetching pets...")
    result = curl_post(f"{API_BASE}/graphql", {
        "Content-Type": "application/json; charset=UTF-8",
        "x-api-key": API_KEY,
        "authorization": f"bearer {token}",
        "apollographql-client-name": "ACC Web",
    }, {"query": GRAPHQL_QUERY})

    pets = result["data"]["feed"]["pets"]
    updated = result["data"]["feed"]["updated"]
    print(f"Got {len(pets)} pets (updated {updated})")
    return pets, updated


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NYC ACC — Find Your Companion</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Source+Sans+3:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

:root {
  --bg: #f6f1eb;
  --bg-card: #ffffff;
  --bg-filter: #ede7df;
  --text: #2c2420;
  --text-muted: #8a7e74;
  --text-light: #b5a99a;
  --accent: #c2703e;
  --accent-hover: #a85a2d;
  --accent-soft: #f0ddd0;
  --border: #e2dbd3;
  --shadow: 0 2px 12px rgba(44,36,32,0.06);
  --shadow-hover: 0 8px 30px rgba(44,36,32,0.12);
  --radius: 10px;
  --radius-sm: 6px;
  --font-display: 'DM Serif Display', Georgia, serif;
  --font-body: 'Source Sans 3', system-ui, sans-serif;
  --urgent-bg: #fef2f2;
  --urgent-border: #e8a0a0;
  --urgent-text: #9b3535;
  --new-bg: #f0f7ee;
  --new-border: #a8cda0;
  --new-text: #3d6b35;
  --foster-bg: #f5f0fa;
  --foster-border: #c4aed8;
  --foster-text: #6b4d8a;
}

html { font-size: 15px; }
body {
  font-family: var(--font-body);
  background: var(--bg);
  color: var(--text);
  line-height: 1.5;
  min-height: 100vh;
}

/* === HEADER === */
.header {
  background: var(--text);
  color: var(--bg);
  padding: 2rem 2rem 1.8rem;
  position: relative;
  overflow: hidden;
}
.header::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--accent), var(--accent-soft), var(--accent));
}
.header-inner {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 0.5rem;
}
.header h1 {
  font-family: var(--font-display);
  font-size: 2rem;
  font-weight: 400;
  letter-spacing: 0.01em;
}
.header h1 span { color: var(--accent); }
.header-meta {
  font-size: 0.85rem;
  opacity: 0.5;
  font-weight: 300;
}
.results-count {
  padding: 0.8rem 2rem;
  background: var(--bg-filter);
  border-bottom: 1px solid var(--border);
  font-size: 0.9rem;
  color: var(--text-muted);
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(10px);
}
.results-count strong {
  color: var(--text);
  font-weight: 600;
}

/* === LAYOUT === */
.layout {
  max-width: 1400px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 0;
  min-height: calc(100vh - 120px);
}

/* === SIDEBAR FILTERS === */
.sidebar {
  background: var(--bg-filter);
  border-right: 1px solid var(--border);
  padding: 1.5rem;
  position: sticky;
  top: 42px;
  height: calc(100vh - 42px);
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: var(--border) transparent;
}
.filter-section {
  margin-bottom: 1.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid var(--border);
}
.filter-section:last-child { border-bottom: none; }
.filter-section h3 {
  font-family: var(--font-display);
  font-size: 1rem;
  font-weight: 400;
  margin-bottom: 0.7rem;
  color: var(--text);
}

/* Species tabs */
.species-tabs {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}
.species-tab {
  padding: 0.4rem 0.9rem;
  border-radius: 99px;
  border: 1px solid var(--border);
  background: var(--bg-card);
  font-family: var(--font-body);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.15s;
  color: var(--text-muted);
  font-weight: 500;
}
.species-tab:hover { border-color: var(--accent); color: var(--accent); }
.species-tab.active {
  background: var(--accent);
  color: white;
  border-color: var(--accent);
}
.species-tab .count {
  font-size: 0.75rem;
  opacity: 0.7;
  margin-left: 0.2rem;
}

/* Range sliders */
.range-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.3rem;
}
.range-row label {
  font-size: 0.8rem;
  color: var(--text-muted);
  width: 32px;
  flex-shrink: 0;
}
.range-row input[type="range"] {
  flex: 1;
  accent-color: var(--accent);
  height: 4px;
}
.range-value {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text);
  width: 50px;
  text-align: right;
  flex-shrink: 0;
}

/* Checkboxes / pills for locations */
.location-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  max-height: 200px;
  overflow-y: auto;
  scrollbar-width: thin;
}
.location-pill {
  padding: 0.25rem 0.6rem;
  border-radius: 99px;
  border: 1px solid var(--border);
  background: var(--bg-card);
  font-size: 0.78rem;
  cursor: pointer;
  transition: all 0.15s;
  color: var(--text-muted);
  user-select: none;
}
.location-pill:hover { border-color: var(--accent); }
.location-pill.active {
  background: var(--accent-soft);
  border-color: var(--accent);
  color: var(--accent);
  font-weight: 500;
}

/* Text search inputs */
.text-filter {
  width: 100%;
  padding: 0.5rem 0.7rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: 0.85rem;
  background: var(--bg-card);
  color: var(--text);
  outline: none;
  transition: border-color 0.15s;
  margin-bottom: 0.4rem;
}
.text-filter:focus { border-color: var(--accent); }
.text-filter::placeholder { color: var(--text-light); }
.filter-hint {
  font-size: 0.72rem;
  color: var(--text-light);
  line-height: 1.4;
}

/* Gender / Fixed toggles */
.toggle-group {
  display: flex;
  gap: 0.3rem;
}
.toggle-btn {
  flex: 1;
  padding: 0.35rem 0.5rem;
  border: 1px solid var(--border);
  background: var(--bg-card);
  font-family: var(--font-body);
  font-size: 0.8rem;
  cursor: pointer;
  text-align: center;
  transition: all 0.15s;
  color: var(--text-muted);
}
.toggle-btn:first-child { border-radius: var(--radius-sm) 0 0 var(--radius-sm); }
.toggle-btn:last-child { border-radius: 0 var(--radius-sm) var(--radius-sm) 0; }
.toggle-btn:hover { border-color: var(--accent); }
.toggle-btn.active {
  background: var(--accent);
  color: white;
  border-color: var(--accent);
}

/* Sort */
.sort-select {
  width: 100%;
  padding: 0.5rem 0.7rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: 0.85rem;
  background: var(--bg-card);
  color: var(--text);
  outline: none;
  cursor: pointer;
}
.sort-select:focus { border-color: var(--accent); }

.reset-btn {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: transparent;
  font-family: var(--font-body);
  font-size: 0.82rem;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.15s;
  margin-top: 0.5rem;
}
.reset-btn:hover {
  background: var(--accent);
  color: white;
  border-color: var(--accent);
}

/* === PET GRID === */
.pet-grid {
  padding: 1.5rem;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.2rem;
  align-content: start;
}

.pet-card {
  background: var(--bg-card);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  overflow: hidden;
  transition: all 0.2s ease;
  cursor: pointer;
  position: relative;
}
.pet-card:hover {
  box-shadow: var(--shadow-hover);
  transform: translateY(-2px);
}

/* Carousel */
.carousel-wrap { position: relative; }
.carousel {
  position: relative;
  width: 100%;
  aspect-ratio: 4/3;
  background: var(--bg-filter);
  overflow: hidden;
  cursor: zoom-in;
}
.carousel-main {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.yt-play-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 56px;
  height: 56px;
  background: rgba(255,0,0,0.85);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.5rem;
  pointer-events: none;
  z-index: 2;
}
.carousel-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(0,0,0,0.45);
  color: white;
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  font-size: 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.15s;
  z-index: 3;
}
.carousel:hover .carousel-btn { opacity: 1; }
.carousel-btn:hover { background: rgba(0,0,0,0.7); }
.carousel-btn.prev { left: 8px; }
.carousel-btn.next { right: 8px; }
.carousel-count {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(0,0,0,0.5);
  color: white;
  font-size: 0.7rem;
  padding: 2px 7px;
  border-radius: 99px;
  z-index: 2;
}
/* Thumbnail strip */
.thumb-strip {
  display: flex;
  gap: 3px;
  padding: 3px;
  overflow-x: auto;
  scrollbar-width: thin;
  scrollbar-color: var(--border) transparent;
  background: var(--bg-filter);
}
.thumb {
  flex-shrink: 0;
  width: 48px;
  height: 36px;
  border-radius: 4px;
  overflow: hidden;
  cursor: pointer;
  opacity: 0.5;
  transition: opacity 0.15s;
  border: 2px solid transparent;
  position: relative;
}
.thumb.active { opacity: 1; border-color: var(--accent); }
.thumb:hover { opacity: 0.9; }
.thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
.thumb-yt-icon {
  display: none;
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%,-50%);
  color: white;
  font-size: 0.7rem;
  text-shadow: 0 0 4px rgba(0,0,0,0.7);
}
.thumb-yt .thumb-yt-icon { display: block; }
.pet-card-no-photo {
  width: 100%;
  aspect-ratio: 4/3;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-filter);
  color: var(--text-light);
  font-size: 2.5rem;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.85);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s;
}
.modal-overlay.open {
  opacity: 1;
  pointer-events: auto;
}
.modal-content {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal-content img {
  max-width: 90vw;
  max-height: 85vh;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}
.modal-video {
  width: 80vw;
  height: 45vw;
  max-height: 80vh;
  border-radius: 8px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}
.modal-yt-link {
  position: relative;
  display: block;
  text-decoration: none;
}
.modal-yt-play {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -60%);
  width: 80px;
  height: 80px;
  background: rgba(255,0,0,0.9);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 2.2rem;
}
.modal-yt-label {
  position: absolute;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%);
  color: white;
  background: rgba(0,0,0,0.6);
  padding: 0.4rem 1rem;
  border-radius: 99px;
  font-family: var(--font-body);
  font-size: 0.9rem;
  white-space: nowrap;
}
.modal-close {
  position: fixed;
  top: 20px;
  right: 24px;
  background: rgba(255,255,255,0.15);
  color: white;
  border: none;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  font-size: 1.3rem;
  cursor: pointer;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
}
.modal-close:hover { background: rgba(255,255,255,0.3); }
.modal-nav {
  position: fixed;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(255,255,255,0.15);
  color: white;
  border: none;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  font-size: 1.4rem;
  cursor: pointer;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
}
.modal-nav:hover { background: rgba(255,255,255,0.3); }
.modal-nav.prev { left: 20px; }
.modal-nav.next { right: 20px; }
.modal-counter {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  color: rgba(255,255,255,0.7);
  font-family: var(--font-body);
  font-size: 0.85rem;
  z-index: 10000;
}

.pet-card-body {
  padding: 1rem 1.1rem;
}
.pet-card-name {
  font-family: var(--font-display);
  font-size: 1.2rem;
  font-weight: 400;
  margin-bottom: 0.15rem;
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
}
.pet-card-id {
  font-family: var(--font-body);
  font-size: 0.72rem;
  color: var(--text-light);
  font-weight: 400;
}
.pet-card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem 0.8rem;
  font-size: 0.82rem;
  color: var(--text-muted);
  margin: 0.4rem 0;
}
.pet-card-meta span { white-space: nowrap; }

.pet-card-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  margin-top: 0.5rem;
}
.badge {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border-radius: 99px;
  font-size: 0.7rem;
  font-weight: 500;
  letter-spacing: 0.02em;
}
.badge-breed {
  background: var(--bg-filter);
  color: var(--text-muted);
}
.badge-color {
  background: var(--bg-filter);
  color: var(--text-muted);
}
.badge-days {
  background: var(--accent-soft);
  color: var(--accent);
  font-weight: 600;
}
.badge-urgent {
  background: var(--urgent-bg);
  color: var(--urgent-text);
  border: 1px solid var(--urgent-border);
}
.badge-new {
  background: var(--new-bg);
  color: var(--new-text);
  border: 1px solid var(--new-border);
}
.badge-foster {
  background: var(--foster-bg);
  color: var(--foster-text);
  border: 1px solid var(--foster-border);
}
.badge-not-fixed {
  background: #fef2f2;
  color: #c33;
  border: 1px solid #e8a0a0;
  font-weight: 600;
}
.badge-gone {
  background: #f0f0f0;
  color: #666;
  border: 1px solid #ccc;
  font-weight: 600;
}
.pet-card.gone {
  opacity: 0.6;
}
.pet-card.gone .carousel-main {
  filter: grayscale(40%);
}

.pet-card-desc {
  margin-top: 0.6rem;
  font-size: 0.82rem;
  line-height: 1.55;
  color: var(--text-muted);
}

.pet-card-link {
  display: block;
  margin-top: 0.6rem;
  padding-top: 0.6rem;
  border-top: 1px solid var(--border);
  font-size: 0.8rem;
  color: var(--accent);
  text-decoration: none;
  font-weight: 500;
  transition: color 0.15s;
}
.pet-card-link:hover { color: var(--accent-hover); }

.no-results {
  grid-column: 1 / -1;
  text-align: center;
  padding: 4rem 2rem;
  color: var(--text-muted);
}
.no-results h2 {
  font-family: var(--font-display);
  font-weight: 400;
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
  color: var(--text);
}

/* View tabs */
.view-tabs {
  display: flex;
  gap: 0;
  max-width: 1400px;
  margin: 0 auto;
  padding: 0.8rem 2rem 0;
}
.view-tab {
  padding: 0.5rem 1.5rem;
  border: 1px solid var(--border);
  background: var(--bg-card);
  font-family: var(--font-body);
  font-size: 0.9rem;
  cursor: pointer;
  color: var(--text-muted);
  font-weight: 500;
  transition: all 0.15s;
}
.view-tab:first-child { border-radius: var(--radius-sm) 0 0 var(--radius-sm); }
.view-tab:last-child { border-radius: 0 var(--radius-sm) var(--radius-sm) 0; }
.view-tab.active {
  background: var(--accent);
  color: white;
  border-color: var(--accent);
}
.view-tab:hover:not(.active) { border-color: var(--accent); color: var(--accent); }

/* Charts */
.charts-view {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1.5rem 2rem;
}
.charts-species-tabs {
  display: flex;
  gap: 0.4rem;
  margin-bottom: 1.2rem;
}
.charts-species-tab {
  padding: 0.4rem 0.9rem;
  border-radius: 99px;
  border: 1px solid var(--border);
  background: var(--bg-card);
  font-family: var(--font-body);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.15s;
  color: var(--text-muted);
  font-weight: 500;
}
.charts-species-tab:hover { border-color: var(--accent); color: var(--accent); }
.charts-species-tab.active {
  background: var(--accent);
  color: white;
  border-color: var(--accent);
}
.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
  gap: 1.2rem;
}
.chart-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.2rem;
}
.chart-card h3 {
  font-family: var(--font-display);
  font-weight: 400;
  font-size: 1rem;
  margin-bottom: 0.8rem;
  color: var(--text);
}

/* Responsive */
@media (max-width: 900px) {
  .layout {
    grid-template-columns: 1fr;
  }
  .sidebar {
    position: relative;
    top: 0;
    height: auto;
    border-right: none;
    border-bottom: 1px solid var(--border);
  }
  .pet-grid {
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  }
}
</style>
<script>
  (function(h,o,u,n,d) {
    h=h[d]=h[d]||{q:[],onReady:function(c){h.q.push(c)}}
    d=o.createElement(u);d.async=1;d.src=n;d.crossOrigin=''
    n=o.getElementsByTagName(u)[0];n.parentNode.insertBefore(d,n)
  })(window,document,'script','https://www.datadoghq-browser-agent.com/us1/v6/datadog-rum.js','DD_RUM')
  window.DD_RUM.onReady(function() {
    window.DD_RUM.init({
      clientToken: 'pub78a116d712b53b48b04b0d4673daffce',
      applicationId: 'c22bcaa5-1c66-409e-9797-388b586e6b7b',
      site: 'datadoghq.com',
      service: 'nyc-acc-pet-viewer',
      env: 'prod',
      sessionSampleRate: 100,
      sessionReplaySampleRate: 20,
      trackBfcacheViews: true,
      defaultPrivacyLevel: 'mask-user-input',
    });
  })
</script>
</head>
<body>

<div class="header">
  <div class="header-inner">
    <h1>NYC <span>ACC</span> — Find Your Companion</h1>
    <div class="header-meta">Updated __UPDATED__</div>
  </div>
</div>
<div class="view-tabs">
  <button class="view-tab active" data-view="browse" onclick="switchView('browse')">Browse</button>
  <button class="view-tab" data-view="charts" onclick="switchView('charts')">Charts</button>
</div>
<div class="results-count" id="resultsCount"></div>

<div class="layout" id="browseView">
  <aside class="sidebar">

    <div class="filter-section">
      <h3>Species</h3>
      <div class="species-tabs" id="speciesTabs"></div>
    </div>

    <div class="filter-section">
      <h3>Show Removed Pets</h3>
      <div class="toggle-group" id="goneToggle">
        <button class="toggle-btn active" data-val="hide">Hide</button>
        <button class="toggle-btn" data-val="show">Show</button>
        <button class="toggle-btn" data-val="only">Only</button>
      </div>
      <div class="filter-hint" style="margin-top:0.4rem">Pets no longer listed on NYC ACC.</div>
    </div>

    <div class="filter-section">
      <h3>Sort By</h3>
      <select class="sort-select" id="sortSelect">
        <option value="days-asc">Newest arrivals</option>
        <option value="days-desc">Longest in system</option>
        <option value="name-asc">Name A–Z</option>
        <option value="name-desc">Name Z–A</option>
        <option value="age-asc">Youngest first</option>
        <option value="age-desc">Oldest first</option>
        <option value="weight-asc">Lightest first</option>
        <option value="weight-desc">Heaviest first</option>
      </select>
    </div>

    <div class="filter-section">
      <h3>Age</h3>
      <div class="range-row">
        <label>Min</label>
        <input type="range" id="ageMin" min="0" max="240" value="0" step="1">
        <span class="range-value" id="ageMinVal">0 mo</span>
      </div>
      <div class="range-row">
        <label>Max</label>
        <input type="range" id="ageMax" min="0" max="240" value="240" step="1">
        <span class="range-value" id="ageMaxVal">20 yr</span>
      </div>
    </div>

    <div class="filter-section">
      <h3>Weight (lbs)</h3>
      <div class="range-row">
        <label>Min</label>
        <input type="range" id="weightMin" min="0" max="150" value="0" step="1">
        <span class="range-value" id="weightMinVal">0</span>
      </div>
      <div class="range-row">
        <label>Max</label>
        <input type="range" id="weightMax" min="0" max="150" value="150" step="1">
        <span class="range-value" id="weightMaxVal">150</span>
      </div>
    </div>

    <div class="filter-section">
      <h3>Gender</h3>
      <div class="toggle-group" id="genderToggle">
        <button class="toggle-btn active" data-val="all">All</button>
        <button class="toggle-btn" data-val="Female">Female</button>
        <button class="toggle-btn" data-val="Male">Male</button>
      </div>
    </div>

    <div class="filter-section">
      <h3>Spayed / Neutered</h3>
      <div class="toggle-group" id="fixedToggle">
        <button class="toggle-btn active" data-val="all">All</button>
        <button class="toggle-btn" data-val="Yes">Yes</button>
        <button class="toggle-btn" data-val="No">No</button>
      </div>
    </div>

    <div class="filter-section">
      <h3>Location</h3>
      <div class="location-pills" id="locationPills"></div>
    </div>

    <div class="filter-section">
      <h3>Breed</h3>
      <div class="location-pills" id="breedPills"></div>
    </div>

    <div class="filter-section">
      <h3>Color</h3>
      <div class="location-pills" id="colorPills"></div>
    </div>

    <div class="filter-section">
      <h3>Experienced Owner</h3>
      <div class="toggle-group" id="experiencedToggle">
        <button class="toggle-btn active" data-val="all">All</button>
        <button class="toggle-btn" data-val="no">Not required</button>
        <button class="toggle-btn" data-val="yes">Required</button>
      </div>
      <div class="filter-hint" style="margin-top:0.4rem">Filters based on "experienced" in description.</div>
    </div>

    <div class="filter-section">
      <h3>Staff Will Address</h3>
      <div class="toggle-group" id="staffAddressToggle">
        <button class="toggle-btn active" data-val="all">All</button>
        <button class="toggle-btn" data-val="hide">Hide these</button>
        <button class="toggle-btn" data-val="only">Only these</button>
      </div>
      <div class="filter-hint" style="margin-top:0.4rem">Filters based on "staff will address" in description.</div>
    </div>

    <div class="filter-section">
      <h3>Description Contains</h3>
      <input type="text" class="text-filter" id="descInclude" placeholder='e.g. friendly, playful'>
      <div class="filter-hint">Comma-separated. Pet must match ALL terms.</div>
    </div>

    <div class="filter-section">
      <h3>Description Excludes</h3>
      <input type="text" class="text-filter" id="descExclude" placeholder='e.g. bite, aggressive'>
      <div class="filter-hint">Comma-separated. Hide pets matching ANY term.</div>
    </div>

    <div class="filter-section">
      <h3>Name Search</h3>
      <input type="text" class="text-filter" id="nameSearch" placeholder='Search by name...'>
    </div>

    <button class="reset-btn" id="resetBtn">Reset All Filters</button>
  </aside>

  <main class="pet-grid" id="petGrid"></main>
</div>

<div class="charts-view" id="chartsView" style="display:none">
  <div class="charts-species-tabs" id="chartSpeciesTabs"></div>
  <div class="charts-grid">
    <div class="chart-card"><h3>Time in Shelter</h3><canvas id="chartDays"></canvas></div>
    <div class="chart-card"><h3>Average Weight by Age</h3><canvas id="chartWeightAge"></canvas></div>
    <div class="chart-card"><h3>Weight Distribution</h3><canvas id="chartWeight"></canvas></div>
    <div class="chart-card"><h3>Age Distribution</h3><canvas id="chartAge"></canvas></div>
    <div class="chart-card"><h3>Gender Breakdown</h3><canvas id="chartGender"></canvas></div>
    <div class="chart-card"><h3>By Location</h3><canvas id="chartLocation"></canvas></div>
    <div class="chart-card"><h3>Intake Over Time (Last 12 Months)</h3><canvas id="chartIntake"></canvas></div>
    <div class="chart-card"><h3>Spayed/Neutered</h3><canvas id="chartFixed"></canvas></div>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<script>
const PETS = __PET_DATA__;
const NOW = Date.now();

// Parse age string to months
function parseAgeMonths(age) {
  if (!age) return 0;
  let months = 0;
  const yMatch = age.match(/(\d+)\s*Year/i);
  const mMatch = age.match(/(\d+)\s*Month/i);
  const wMatch = age.match(/(\d+)\s*Week/i);
  const dMatch = age.match(/(\d+)\s*Day/i);
  if (yMatch) months += parseInt(yMatch[1]) * 12;
  if (mMatch) months += parseInt(mMatch[1]);
  if (wMatch) months += parseInt(wMatch[1]) / 4.33;
  if (dMatch) months += parseInt(dMatch[1]) / 30;
  return months;
}

// Parse weight string to number
function parseWeight(w) {
  if (!w) return 0;
  const m = w.match(/([\d.]+)/);
  return m ? parseFloat(m[1]) : 0;
}

// Days since intake
function daysSince(dateStr) {
  if (!dateStr) return 0;
  return Math.floor((NOW - new Date(dateStr).getTime()) / 86400000);
}

// Format months for display
function fmtAge(months) {
  if (months >= 12) return Math.round(months / 12) + ' yr';
  return Math.round(months) + ' mo';
}

// Precompute fields
PETS.forEach(p => {
  p._ageMonths = parseAgeMonths(p.age);
  p._weight = parseWeight(p.weight);
  p._days = daysSince(p.intakeDate);
  p._searchText = ((p.summary || '') + ' ' + (p.name || '')).toLowerCase();
  p._experienced = p._searchText.includes('experienced');
  p._staffAddress = p._searchText.includes('staff will address');
});

// Get unique values
const allSpecies = [...new Set(PETS.map(p => p.species).filter(Boolean))].sort();
const allLocations = [...new Set(PETS.map(p => p.location).filter(Boolean))].sort();

// State persistence
const STORAGE_KEY = 'nycacc_filters';
const DEFAULTS = {
  species: 'Cat', ageMin: 0, ageMax: 240,
  weightMin: 0, weightMax: 150,
  gender: 'all', fixed: 'all', experienced: 'all', staffAddress: 'all', showGone: 'hide',
  locations: [], breeds: [], colors: [],
  descInclude: '', descExclude: '',
  nameSearch: '', sort: 'days-asc',
};
const SET_KEYS = ['locations', 'breeds', 'colors'];

function stateToParams() {
  const p = new URLSearchParams();
  for (const [k, def] of Object.entries(DEFAULTS)) {
    const val = SET_KEYS.includes(k) ? [...state[k]] : state[k];
    const defVal = SET_KEYS.includes(k) ? [] : def;
    if (SET_KEYS.includes(k)) {
      if (val.length > 0) p.set(k, val.join('|'));
    } else if (val !== defVal) {
      p.set(k, val);
    }
  }
  return p;
}

function paramsToState(params) {
  const s = {};
  for (const [k, def] of Object.entries(DEFAULTS)) {
    if (SET_KEYS.includes(k)) {
      const raw = params.get(k);
      s[k] = new Set(raw ? raw.split('|').filter(Boolean) : []);
    } else if (typeof def === 'number') {
      s[k] = params.has(k) ? parseInt(params.get(k)) : def;
    } else {
      s[k] = params.has(k) ? params.get(k) : def;
    }
  }
  return s;
}

function saveState() {
  const s = {...state, locations: [...state.locations], breeds: [...state.breeds], colors: [...state.colors]};
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(s)); } catch(e) {}
  const params = stateToParams();
  const qs = params.toString();
  const newUrl = qs ? location.pathname + '?' + qs : location.pathname;
  history.replaceState(null, '', newUrl);
}

function loadState() {
  // URL params take priority (for shared links)
  const urlParams = new URLSearchParams(location.search);
  if (urlParams.toString()) return paramsToState(urlParams);
  // Fall back to localStorage
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const s = JSON.parse(raw);
    s.locations = new Set(s.locations || []);
    s.breeds = new Set(s.breeds || []);
    s.colors = new Set(s.colors || []);
    if (!s.experienced) s.experienced = 'all';
    if (!s.staffAddress) s.staffAddress = 'all';
    if (!s.showGone) s.showGone = 'hide';
    return s;
  } catch(e) { return null; }
}

let state = loadState() || (function() {
  const s = {...DEFAULTS};
  SET_KEYS.forEach(k => s[k] = new Set());
  return s;
})();

// Build species tabs
const speciesTabs = document.getElementById('speciesTabs');
allSpecies.forEach(sp => {
  const count = PETS.filter(p => p.species === sp).length;
  const btn = document.createElement('button');
  btn.className = 'species-tab' + (sp === state.species ? ' active' : '');
  btn.innerHTML = `${sp} <span class="count">${count}</span>`;
  btn.dataset.species = sp;
  btn.onclick = () => {
    state.species = sp;
    document.querySelectorAll('.species-tab').forEach(b => b.classList.toggle('active', b.dataset.species === sp));
    buildLocations(true);
    buildBreeds(true);
    buildColors(true);
    render();
  };
  speciesTabs.appendChild(btn);
});

// Build location pills
function buildLocations(reset) {
  const pills = document.getElementById('locationPills');
  pills.innerHTML = '';
  const locs = [...new Set(PETS.filter(p => p.species === state.species).map(p => p.location).filter(Boolean))].sort();
  if (reset) state.locations = new Set();
  else state.locations = new Set([...state.locations].filter(l => locs.includes(l)));
  locs.forEach(loc => {
    const pill = document.createElement('button');
    pill.className = 'location-pill' + (state.locations.has(loc) ? ' active' : '');
    pill.textContent = loc;
    pill.onclick = () => {
      if (state.locations.has(loc)) state.locations.delete(loc);
      else state.locations.add(loc);
      pill.classList.toggle('active');
      render();
    };
    pills.appendChild(pill);
  });
}
buildLocations(false);

// Build breed pills
function buildBreeds(reset) {
  const pills = document.getElementById('breedPills');
  pills.innerHTML = '';
  const breeds = [...new Set(PETS.filter(p => p.species === state.species).flatMap(p => p.breeds || []).filter(Boolean))].sort();
  if (reset) state.breeds = new Set();
  else state.breeds = new Set([...state.breeds].filter(b => breeds.includes(b)));
  breeds.forEach(breed => {
    const pill = document.createElement('button');
    pill.className = 'location-pill' + (state.breeds.has(breed) ? ' active' : '');
    pill.textContent = breed;
    pill.onclick = () => {
      if (state.breeds.has(breed)) state.breeds.delete(breed);
      else state.breeds.add(breed);
      pill.classList.toggle('active');
      render();
    };
    pills.appendChild(pill);
  });
}
buildBreeds(false);

// Build color pills
function buildColors(reset) {
  const pills = document.getElementById('colorPills');
  pills.innerHTML = '';
  const clrs = [...new Set(PETS.filter(p => p.species === state.species).flatMap(p => p.colors || []).filter(Boolean))].sort();
  if (reset) state.colors = new Set();
  else state.colors = new Set([...state.colors].filter(c => clrs.includes(c)));
  clrs.forEach(color => {
    const pill = document.createElement('button');
    pill.className = 'location-pill' + (state.colors.has(color) ? ' active' : '');
    pill.textContent = color;
    pill.onclick = () => {
      if (state.colors.has(color)) state.colors.delete(color);
      else state.colors.add(color);
      pill.classList.toggle('active');
      render();
    };
    pills.appendChild(pill);
  });
}
buildColors(false);

// Toggle groups
function setupToggle(id, stateKey) {
  const el = document.getElementById(id);
  el.querySelectorAll('.toggle-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.val === state[stateKey]);
    btn.onclick = () => {
      state[stateKey] = btn.dataset.val;
      el.querySelectorAll('.toggle-btn').forEach(b => b.classList.toggle('active', b.dataset.val === state[stateKey]));
      render();
    };
  });
}
setupToggle('genderToggle', 'gender');
setupToggle('fixedToggle', 'fixed');
setupToggle('experiencedToggle', 'experienced');
setupToggle('staffAddressToggle', 'staffAddress');
setupToggle('goneToggle', 'showGone');

// Sliders
function setupRange(sliderId, valId, stateKey, fmt) {
  const slider = document.getElementById(sliderId);
  const valEl = document.getElementById(valId);
  slider.value = state[stateKey];
  valEl.textContent = fmt(state[stateKey]);
  slider.oninput = () => {
    state[stateKey] = parseInt(slider.value);
    valEl.textContent = fmt(state[stateKey]);
    render();
  };
}
setupRange('ageMin', 'ageMinVal', 'ageMin', fmtAge);
setupRange('ageMax', 'ageMaxVal', 'ageMax', fmtAge);
setupRange('weightMin', 'weightMinVal', 'weightMin', v => v);
setupRange('weightMax', 'weightMaxVal', 'weightMax', v => v);

// Text inputs
['descInclude', 'descExclude', 'nameSearch'].forEach(id => {
  const el = document.getElementById(id);
  el.value = state[id] || '';
  el.oninput = (e) => {
    state[id] = e.target.value;
    render();
  };
});

// Sort
document.getElementById('sortSelect').value = state.sort;
document.getElementById('sortSelect').onchange = (e) => {
  state.sort = e.target.value;
  render();
};

// Reset
document.getElementById('resetBtn').onclick = () => {
  try { localStorage.removeItem(STORAGE_KEY); } catch(e) {}
  state.ageMin = 0; state.ageMax = 240;
  state.weightMin = 0; state.weightMax = 150;
  state.gender = 'all'; state.fixed = 'all'; state.experienced = 'all'; state.staffAddress = 'all'; state.showGone = 'hide';
  state.locations = new Set();
  state.breeds = new Set();
  state.colors = new Set();
  state.descInclude = ''; state.descExclude = '';
  state.nameSearch = '';
  state.sort = 'days-asc';
  document.getElementById('ageMin').value = 0;
  document.getElementById('ageMax').value = 240;
  document.getElementById('weightMin').value = 0;
  document.getElementById('weightMax').value = 150;
  document.getElementById('ageMinVal').textContent = fmtAge(0);
  document.getElementById('ageMaxVal').textContent = fmtAge(240);
  document.getElementById('weightMinVal').textContent = '0';
  document.getElementById('weightMaxVal').textContent = '150';
  document.getElementById('descInclude').value = '';
  document.getElementById('descExclude').value = '';
  document.getElementById('nameSearch').value = '';
  document.getElementById('sortSelect').value = 'days-asc';
  document.querySelectorAll('.toggle-btn').forEach(b => b.classList.toggle('active', b.dataset.val === 'all'));
  document.querySelectorAll('.location-pill').forEach(p => p.classList.remove('active'));
  render();
};

// Filter + Sort + Render
function getFiltered() {
  let pets = PETS.filter(p => p.species === state.species);

  // Gone filter
  if (state.showGone === 'hide') pets = pets.filter(p => !p._gone);
  else if (state.showGone === 'only') pets = pets.filter(p => p._gone);

  pets = pets.filter(p => p._ageMonths >= state.ageMin && p._ageMonths <= state.ageMax);
  pets = pets.filter(p => p._weight >= state.weightMin && p._weight <= state.weightMax);

  if (state.gender !== 'all') pets = pets.filter(p => p.gender === state.gender);
  if (state.fixed !== 'all') pets = pets.filter(p => p.spayedNeutered === state.fixed);

  if (state.locations.size > 0) pets = pets.filter(p => state.locations.has(p.location));
  if (state.breeds.size > 0) pets = pets.filter(p => (p.breeds || []).some(b => state.breeds.has(b)));
  if (state.colors.size > 0) pets = pets.filter(p => (p.colors || []).some(c => state.colors.has(c)));
  if (state.experienced === 'yes') pets = pets.filter(p => p._experienced);
  if (state.experienced === 'no') pets = pets.filter(p => !p._experienced);
  if (state.staffAddress === 'hide') pets = pets.filter(p => !p._staffAddress);
  if (state.staffAddress === 'only') pets = pets.filter(p => p._staffAddress);

  if (state.descInclude.trim()) {
    const terms = state.descInclude.split(',').map(t => t.trim().toLowerCase()).filter(Boolean);
    pets = pets.filter(p => terms.every(t => p._searchText.includes(t)));
  }
  if (state.descExclude.trim()) {
    const terms = state.descExclude.split(',').map(t => t.trim().toLowerCase()).filter(Boolean);
    pets = pets.filter(p => !terms.some(t => p._searchText.includes(t)));
  }
  if (state.nameSearch.trim()) {
    const q = state.nameSearch.trim().toLowerCase();
    pets = pets.filter(p => (p.name || '').toLowerCase().includes(q));
  }

  // Sort
  const [key, dir] = state.sort.split('-');
  const mul = dir === 'asc' ? 1 : -1;
  pets.sort((a, b) => {
    let va, vb;
    switch(key) {
      case 'days': va = a._days; vb = b._days; break;
      case 'name': va = (a.name||'').toLowerCase(); vb = (b.name||'').toLowerCase(); return mul * va.localeCompare(vb);
      case 'age': va = a._ageMonths; vb = b._ageMonths; break;
      case 'weight': va = a._weight; vb = b._weight; break;
      default: va = a._days; vb = b._days;
    }
    return mul * (va - vb);
  });

  return pets;
}

function escapeHtml(s) {
  if (!s) return '';
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function buildSlides(p) {
  const slides = [];
  (p.photos || []).forEach(url => slides.push({type:'img', src: url}));
  (p.youTubeIds || []).forEach(id => slides.push({type:'yt', id: id, thumb: `https://img.youtube.com/vi/${id}/hqdefault.jpg`}));
  return slides;
}

function slideThumb(slide) {
  return slide.type === 'yt' ? slide.thumb : slide.src;
}

function renderCarousel(p) {
  const slides = buildSlides(p);
  if (slides.length === 0) return `<div class="pet-card-no-photo">\u{1F43E}</div>`;
  const slidesJson = escapeHtml(JSON.stringify(slides));
  const count = slides.length > 1 ? `<span class="carousel-count">1 / ${slides.length}</span>` : '';
  const nav = slides.length > 1
    ? `<button class="carousel-btn prev" onclick="event.stopPropagation();carouselNav(this.closest('.carousel-wrap'),-1)">\u2039</button>
       <button class="carousel-btn next" onclick="event.stopPropagation();carouselNav(this.closest('.carousel-wrap'),1)">\u203A</button>`
    : '';
  const ytOverlay = slides[0].type === 'yt' ? '<div class="yt-play-overlay">\u25B6</div>' : '';
  const thumbStrip = slides.length > 1
    ? `<div class="thumb-strip">${slides.map((s, i) =>
        `<div class="thumb${i===0?' active':''}${s.type==='yt'?' thumb-yt':''}" data-i="${i}"
          onclick="event.stopPropagation();carouselGoTo(this.closest('.carousel-wrap'),${i})">
          <img src="${slideThumb(s)}" loading="lazy"><span class="thumb-yt-icon">\u25B6</span></div>`
      ).join('')}</div>`
    : '';
  return `<div class="carousel-wrap" data-idx="0" data-slides="${slidesJson}">
    <div class="carousel"
      onclick="event.stopPropagation();openModal(JSON.parse(this.closest('.carousel-wrap').dataset.slides), parseInt(this.closest('.carousel-wrap').dataset.idx))">
      <img class="carousel-main" src="${slideThumb(slides[0])}" alt="${escapeHtml(p.name)}" loading="lazy">
      ${ytOverlay}
      ${nav}${count}
    </div>
    ${thumbStrip}
  </div>`;
}

function renderCard(p) {
  const days = p._days;
  const daysLabel = days < 1 ? Math.max(1, Math.floor((NOW - new Date(p.intakeDate).getTime()) / 3600000)) + 'h' : days + 'd';
  let daysBadge = `<span class="badge badge-days">${daysLabel} in system</span>`;

  let extraBadges = '';
  if (days <= 3) extraBadges += '<span class="badge badge-new">New arrival</span>';
  if (p.summaryHtml && p.summaryHtml.includes('emergency') || p.summaryHtml && p.summaryHtml.includes('urgent'))
    extraBadges += '<span class="badge badge-urgent">Needs rescue</span>';
  if (p.location === 'In Foster') extraBadges += '<span class="badge badge-foster">In foster</span>';
  if (p.spayedNeutered && p.spayedNeutered !== 'Yes') extraBadges += '<span class="badge badge-not-fixed">Not spayed/neutered</span>';
  if (p._gone) extraBadges += `<span class="badge badge-gone">No longer listed${p._goneDate ? ' \u2014 ' + p._goneDate.substring(0,10) : ''}</span>`;

  const breeds = (p.breeds || []).map(b => `<span class="badge badge-breed">${escapeHtml(b)}</span>`).join('');
  const colors = (p.colors || []).map(c => `<span class="badge badge-color">${escapeHtml(c)}</span>`).join('');

  const desc = p.summary ? escapeHtml(p.summary) : '';
  const descBlock = desc ? `<div class="pet-card-desc">${desc}</div>` : '';

  const goneClass = p._gone ? ' gone' : '';
  return `<div class="pet-card${goneClass}" onclick="if(!event.target.closest('.carousel-wrap'))window.open('${p.link || '#'}','_blank')">
    ${renderCarousel(p)}
    <div class="pet-card-body">
      <div class="pet-card-name">${escapeHtml(p.name)} <span class="pet-card-id">#${p.id}</span></div>
      <div class="pet-card-meta">
        <span>${escapeHtml(p.age) || 'Unknown age'}</span>
        <span>${escapeHtml(p.gender) || ''}</span>
        <span>${escapeHtml(p.weight) || ''}</span>
        <span>${escapeHtml(p.location) || ''}</span>
      </div>
      <div class="pet-card-badges">
        ${daysBadge}${extraBadges}${breeds}${colors}
      </div>
      ${descBlock}
    </div>
  </div>`;
}

function render() {
  const pets = getFiltered();
  const grid = document.getElementById('petGrid');
  const countEl = document.getElementById('resultsCount');

  const goneCount = pets.filter(p => p._gone).length;
  const goneLabel = goneCount > 0 ? ` <span style="color:var(--text-light)">(${goneCount} no longer listed)</span>` : '';
  countEl.innerHTML = `Showing <strong>${pets.length}</strong> ${state.species.toLowerCase()}${pets.length !== 1 ? 's' : ''}${goneLabel}`;

  if (pets.length === 0) {
    grid.innerHTML = `<div class="no-results"><h2>No matches</h2><p>Try adjusting your filters.</p></div>`;
    return;
  }

  grid.innerHTML = pets.map(renderCard).join('');
  saveState();
}

render();

// Carousel navigation
function carouselGoTo(wrap, idx) {
  const slides = JSON.parse(wrap.dataset.slides);
  if (idx < 0) idx = slides.length - 1;
  if (idx >= slides.length) idx = 0;
  wrap.dataset.idx = idx;
  const slide = slides[idx];
  const img = wrap.querySelector('.carousel-main');
  img.src = slide.type === 'yt' ? slide.thumb : slide.src;
  const ytOverlay = wrap.querySelector('.yt-play-overlay');
  if (ytOverlay) ytOverlay.style.display = slide.type === 'yt' ? '' : 'none';
  else if (slide.type === 'yt') {
    const ov = document.createElement('div');
    ov.className = 'yt-play-overlay';
    ov.textContent = '\u25B6';
    wrap.querySelector('.carousel').appendChild(ov);
  }
  wrap.querySelectorAll('.thumb').forEach((t, i) => t.classList.toggle('active', i === idx));
  const counter = wrap.querySelector('.carousel-count');
  if (counter) counter.textContent = `${idx + 1} / ${slides.length}`;
}
function carouselNav(wrap, dir) {
  carouselGoTo(wrap, parseInt(wrap.dataset.idx) + dir);
}

// Modal
let modalSlides = [];
let modalIdx = 0;

function renderModalSlide(slide) {
  const content = document.querySelector('.modal-content');
  if (slide.type === 'yt') {
    const isLocal = location.protocol === 'file:';
    if (isLocal) {
      content.innerHTML = `<a href="https://www.youtube.com/watch?v=${slide.id}" target="_blank" rel="noopener" class="modal-yt-link"
        onclick="event.stopPropagation()">
        <img class="modal-img" src="${slide.thumb}" alt="YouTube video">
        <div class="modal-yt-play">\u25B6</div>
        <div class="modal-yt-label">Click to watch on YouTube</div>
      </a>`;
    } else {
      content.innerHTML = `<iframe class="modal-video" src="https://www.youtube-nocookie.com/embed/${slide.id}?rel=0&autoplay=1" frameborder="0" allowfullscreen allow="autoplay"></iframe>`;
    }
  } else {
    content.innerHTML = `<img class="modal-img" src="${slide.src}" alt="Pet photo">`;
  }
}

function openModal(slides, idx) {
  modalSlides = slides;
  modalIdx = idx || 0;
  const overlay = document.getElementById('modalOverlay');
  renderModalSlide(slides[modalIdx]);
  overlay.querySelector('.modal-counter').textContent = `${modalIdx + 1} / ${slides.length}`;
  overlay.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  const overlay = document.getElementById('modalOverlay');
  overlay.classList.remove('open');
  overlay.querySelector('.modal-content').innerHTML = '';
  document.body.style.overflow = '';
}

function modalNav(dir) {
  modalIdx += dir;
  if (modalIdx < 0) modalIdx = modalSlides.length - 1;
  if (modalIdx >= modalSlides.length) modalIdx = 0;
  const overlay = document.getElementById('modalOverlay');
  renderModalSlide(modalSlides[modalIdx]);
  overlay.querySelector('.modal-counter').textContent = `${modalIdx + 1} / ${modalSlides.length}`;
}

document.addEventListener('keydown', (e) => {
  const overlay = document.getElementById('modalOverlay');
  if (!overlay.classList.contains('open')) return;
  if (e.key === 'Escape') closeModal();
  if (e.key === 'ArrowLeft') modalNav(-1);
  if (e.key === 'ArrowRight') modalNav(1);
});

// View switching
let chartInstances = {};
let chartSpecies = 'Cat';

function buildChartSpeciesTabs() {
  const container = document.getElementById('chartSpeciesTabs');
  container.innerHTML = '';
  allSpecies.forEach(sp => {
    const count = PETS.filter(p => p.species === sp).length;
    const btn = document.createElement('button');
    btn.className = 'charts-species-tab' + (sp === chartSpecies ? ' active' : '');
    btn.innerHTML = `${sp} <span style="font-size:0.75rem;opacity:0.7;margin-left:0.2rem">${count}</span>`;
    btn.onclick = () => {
      chartSpecies = sp;
      container.querySelectorAll('.charts-species-tab').forEach(b => b.classList.toggle('active', b === btn));
      renderCharts();
    };
    container.appendChild(btn);
  });
}

function switchView(view) {
  document.querySelectorAll('.view-tab').forEach(t => t.classList.toggle('active', t.dataset.view === view));
  document.getElementById('browseView').style.display = view === 'browse' ? '' : 'none';
  document.getElementById('chartsView').style.display = view === 'charts' ? '' : 'none';
  document.querySelector('.results-count').style.display = view === 'browse' ? '' : 'none';
  if (view === 'charts') {
    buildChartSpeciesTabs();
    renderCharts();
  }
}

function renderCharts() {
  const pets = PETS.filter(p => p.species === chartSpecies);
  const accent = '#c2703e';
  const accentSoft = '#f0ddd0';
  const colors6 = ['#c2703e','#8a7e74','#3d6b35','#6b4d8a','#9b3535','#2c6e8a'];

  Object.values(chartInstances).forEach(c => c.destroy());
  chartInstances = {};

  function makeChart(id, config) {
    chartInstances[id] = new Chart(document.getElementById(id), config);
  }

  // Days in shelter histogram
  const dayBuckets = [0,7,14,30,60,90,180,365,Infinity];
  const dayLabels = ['0-7d','8-14d','15-30d','31-60d','61-90d','91-180d','181-365d','365d+'];
  const dayCounts = dayLabels.map(() => 0);
  pets.forEach(p => {
    for (let i = 0; i < dayBuckets.length - 1; i++) {
      if (p._days >= dayBuckets[i] && p._days < dayBuckets[i+1]) { dayCounts[i]++; break; }
    }
  });
  makeChart('chartDays', {
    type: 'bar',
    data: { labels: dayLabels, datasets: [{ label: 'Count', data: dayCounts, backgroundColor: accent }] },
    options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
  });

  // Average weight by age
  const ageGroups = {};
  pets.forEach(p => {
    if (!p._weight) return;
    const ageYr = Math.floor(p._ageMonths / 12);
    const label = ageYr + 'yr';
    if (!ageGroups[label]) ageGroups[label] = { sum: 0, count: 0, weights: [] };
    ageGroups[label].sum += p._weight;
    ageGroups[label].count++;
    ageGroups[label].weights.push(p._weight);
  });
  const ageSorted = Object.keys(ageGroups).sort((a, b) => parseInt(a) - parseInt(b));
  const avgWeights = ageSorted.map(k => (ageGroups[k].sum / ageGroups[k].count).toFixed(1));
  const minWeights = ageSorted.map(k => Math.min(...ageGroups[k].weights));
  const maxWeights = ageSorted.map(k => Math.max(...ageGroups[k].weights));
  makeChart('chartWeightAge', {
    type: 'bar',
    data: {
      labels: ageSorted,
      datasets: [
        { label: 'Avg Weight (lbs)', data: avgWeights, backgroundColor: accent },
        { label: 'Min', data: minWeights, backgroundColor: accentSoft },
        { label: 'Max', data: maxWeights, backgroundColor: '#8a7e74' },
      ]
    },
    options: { plugins: { legend: { display: true } }, scales: { y: { beginAtZero: true } } }
  });

  // Weight distribution histogram
  const wBuckets = [0,5,10,15,20,30,50,75,100,Infinity];
  const wLabels = ['0-5','5-10','10-15','15-20','20-30','30-50','50-75','75-100','100+'];
  const wCounts = wLabels.map(() => 0);
  pets.forEach(p => {
    if (!p._weight) return;
    for (let i = 0; i < wBuckets.length - 1; i++) {
      if (p._weight >= wBuckets[i] && p._weight < wBuckets[i+1]) { wCounts[i]++; break; }
    }
  });
  makeChart('chartWeight', {
    type: 'bar',
    data: { labels: wLabels.map(l => l + ' lbs'), datasets: [{ label: 'Count', data: wCounts, backgroundColor: accent }] },
    options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
  });

  // Age distribution
  const aBuckets = [0,3,6,12,24,60,120,Infinity];
  const aLabels = ['0-3mo','3-6mo','6mo-1yr','1-2yr','2-5yr','5-10yr','10yr+'];
  const aCounts = aLabels.map(() => 0);
  pets.forEach(p => {
    for (let i = 0; i < aBuckets.length - 1; i++) {
      if (p._ageMonths >= aBuckets[i] && p._ageMonths < aBuckets[i+1]) { aCounts[i]++; break; }
    }
  });
  makeChart('chartAge', {
    type: 'bar',
    data: { labels: aLabels, datasets: [{ label: 'Count', data: aCounts, backgroundColor: '#3d6b35' }] },
    options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
  });

  // Gender pie
  const genderCounts = {};
  pets.forEach(p => { const g = p.gender || 'Unknown'; genderCounts[g] = (genderCounts[g] || 0) + 1; });
  makeChart('chartGender', {
    type: 'doughnut',
    data: { labels: Object.keys(genderCounts), datasets: [{ data: Object.values(genderCounts), backgroundColor: colors6 }] },
    options: { plugins: { legend: { position: 'bottom' } } }
  });

  // Location bar
  const locCounts = {};
  pets.forEach(p => { const l = p.location || 'Unknown'; locCounts[l] = (locCounts[l] || 0) + 1; });
  const locSorted = Object.entries(locCounts).sort((a, b) => b[1] - a[1]);
  makeChart('chartLocation', {
    type: 'bar',
    data: { labels: locSorted.map(l => l[0]), datasets: [{ label: 'Count', data: locSorted.map(l => l[1]), backgroundColor: '#6b4d8a' }] },
    options: { indexAxis: 'y', plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true } } }
  });

  // Intake over time (last 12 months)
  const now = new Date();
  const monthLabels = [];
  const monthCounts = [];
  for (let i = 11; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const key = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0');
    monthLabels.push(key);
    monthCounts.push(0);
  }
  pets.forEach(p => {
    if (!p.intakeDate) return;
    const d = new Date(p.intakeDate);
    const key = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0');
    const idx = monthLabels.indexOf(key);
    if (idx >= 0) monthCounts[idx]++;
  });
  makeChart('chartIntake', {
    type: 'line',
    data: { labels: monthLabels, datasets: [{ label: 'Intakes', data: monthCounts, borderColor: accent, backgroundColor: accentSoft, fill: true, tension: 0.3 }] },
    options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
  });

  // Spayed/Neutered pie
  const fixedCounts = {};
  pets.forEach(p => { const f = p.spayedNeutered || 'Unknown'; fixedCounts[f] = (fixedCounts[f] || 0) + 1; });
  makeChart('chartFixed', {
    type: 'doughnut',
    data: { labels: Object.keys(fixedCounts), datasets: [{ data: Object.values(fixedCounts), backgroundColor: colors6 }] },
    options: { plugins: { legend: { position: 'bottom' } } }
  });
}
</script>

<div class="modal-overlay" id="modalOverlay" onclick="if(event.target===this)closeModal()">
  <button class="modal-close" onclick="closeModal()">&times;</button>
  <button class="modal-nav prev" onclick="modalNav(-1)">&lsaquo;</button>
  <div class="modal-content"></div>
  <button class="modal-nav next" onclick="modalNav(1)">&rsaquo;</button>
  <div class="modal-counter"></div>
</div>
</body>
</html>"""


HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nycacc_history.json")


def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_history(history):
    sorted_history = dict(sorted(history.items(), key=lambda x: int(x[0])))
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted_history, f, ensure_ascii=False, indent=1, sort_keys=True)


def merge_pets(live_pets, updated):
    """Merge live API data with historical data.

    - Live pets get updated with fresh data and marked active.
    - Pets in history but not in live data get marked as gone.
    - New pets get added.
    """
    history = load_history()
    live_ids = set()

    for pet in live_pets:
        pid = str(pet["id"])
        live_ids.add(pid)
        pet["_gone"] = False
        pet["_lastSeen"] = updated
        if pid in history:
            pet["_firstSeen"] = history[pid].get("_firstSeen", updated)
        else:
            pet["_firstSeen"] = updated
        history[pid] = pet

    for pid, pet in history.items():
        if pid not in live_ids:
            if not pet.get("_gone"):
                pet["_gone"] = True
                pet["_goneDate"] = updated

    save_history(history)

    all_pets = list(history.values())
    active = sum(1 for p in all_pets if not p.get("_gone"))
    gone = sum(1 for p in all_pets if p.get("_gone"))
    print(f"History: {active} active, {gone} no longer listed, {len(all_pets)} total")
    return all_pets


def generate_html(pets, updated):
    pets_json = json.dumps(pets, ensure_ascii=False)
    html = HTML_TEMPLATE.replace("__PET_DATA__", pets_json)
    html = html.replace("__UPDATED__", updated[:16].replace("T", " "))
    return html


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=os.path.dirname(os.path.abspath(__file__)),
                        help="Directory to write output files")
    parser.add_argument("--no-open", action="store_true",
                        help="Don't open browser after generating")
    args = parser.parse_args()

    global HISTORY_FILE
    HISTORY_FILE = os.path.join(args.output_dir, "nycacc_history.json")

    live_pets, updated = fetch_pets()
    all_pets = merge_pets(live_pets, updated)
    html = generate_html(all_pets, updated)

    os.makedirs(args.output_dir, exist_ok=True)

    html_path = os.path.join(args.output_dir, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Generated {html_path}")

    if not args.no_open:
        webbrowser.open(f"file://{html_path}")


if __name__ == "__main__":
    main()
