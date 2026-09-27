# Form & Field

A small full-stack homewares storefront. FastAPI serves the product catalog and demo checkout API, and the frontend is plain HTML, CSS, and JavaScript with no build step.

## Run locally

Requires Python 3.10 or later.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Open <http://127.0.0.1:8000>. Interactive API documentation is at <http://127.0.0.1:8000/docs>.

## API

- `GET /api/products` returns the catalog and current in-memory stock.
- `POST /api/checkout` accepts `{"items":[{"product_id":"arc-lamp","quantity":1}]}` and returns a demo order receipt.

Checkout recalculates prices on the server and decrements in-memory stock. This is a demo, not a production store: stock and orders reset on restart, and checkout does not collect payment or customer information.

## Detailed guide

See [docs/COMPLETE_GUIDE.md](docs/COMPLETE_GUIDE.md) for a file-by-file explanation of the app, API flow, package roles, examples, limitations, and the complete current source appendix in [docs/COMPLETE_GUIDE.pdf](docs/COMPLETE_GUIDE.pdf). Rebuild the PDF after installing the documentation-only dependencies with `python -m pip install -r docs/requirements.txt`, then run `python docs/build_guide.py`.
