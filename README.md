---
title: Meih Movies API
emoji: 🎬
colorFrom: red
colorTo: gray
sdk: docker
pinned: false
version: 1.1.0
---

# MEIH Movies API - Nitro Engine

A powerful, high-speed movie scraping API powered by FastAPI, FlareSolverr, and Hybrid Scrapers.

## Deploying on Hugging Face

This Space is configured to run as a Docker container. It automatically handles:

- Cloudflare bypass via FlareSolverr.
- Proxy rotation.
- High-speed content extraction.

## API Endpoints

- `/latest`: Get latest movies and series.
- `/search?q=query`: Search for content.
- `/details/{id}`: Get streaming and download links.
