# Form & Field: Complete Project Guide

**A file-by-file guide to the storefront, FastAPI backend, cart, and demo checkout**  
Prepared September 27, 2026

## 1. What This Project Is

Form & Field is a small, full-stack homewares storefront. It demonstrates a working product catalog, search and category filtering, a browser-side shopping bag, and a FastAPI JSON API. FastAPI serves both the website and the API, so the page and its API requests use the same origin.

The order button currently creates a **demo order only**. The app does not connect to Stripe, PayPal, or any other payment processor; it cannot charge a customer, store an order permanently, or collect customer or delivery details. A displayed order number is a sample receipt, not proof of payment or fulfillment.

## 2. At a Glance

| Area | Technology | Responsibility |
| --- | --- | --- |
| API and local web server | Python, FastAPI, Uvicorn | Serve the HTML, CSS, and JavaScript; expose product and checkout endpoints. |
| Request validation | Pydantic, through FastAPI | Parse JSON and reject invalid checkout shapes and quantities. |
| Browser interface | HTML5 | Define the page, product grid, shopping-bag drawer, and accessible labels. |
| Browser behavior | Plain JavaScript (ES6+) | Load products; filter and sort; maintain the cart; call checkout. |
| Styling and responsiveness | Plain CSS | Define visual styling, layout, motion, and desktop/tablet/mobile breakpoints. |
| PDF guide generation | Python-Markdown, ReportLab | Convert this guide and generated source listings into the downloadable PDF. These are documentation-only dependencies. |
| Product photos and display fonts | Unsplash and Google Fonts | Supply externally hosted images and the DM Sans / Playfair Display fonts. |
| Payment | None | Checkout is simulated; no payment request is made. |
| Persistent database | None | Products and stock are Python in-memory data; the cart is browser local storage. |

There is no React, Vue, npm package, JavaScript build step, database, ORM, login system, or payment SDK in this project.

## 3. Project Directory

```text
shop_demo/
├── main.py                    FastAPI application, catalog, stock, API routes
├── requirements.txt           Python runtime dependency ranges
├── README.md                  Short setup and API reference
├── .venv/                     Local Python environment; generated, not source
├── static/
│   ├── index.html             Storefront structure and text
│   ├── app.js                 Browser state, rendering, cart, API calls
│   └── styles.css             Design system, layout, responsive styles
└── docs/
    ├── COMPLETE_GUIDE.md      This guide (the maintainable source document)
    ├── build_guide.py         Build the PDF and add current source appendices
    └── COMPLETE_GUIDE.pdf     Generated PDF copy of this guide
```

The Python virtual environment `.venv/` isolates this app's installed packages from system Python and from the rest of the workspace. It is not source code and should not be committed.

## 4. Requirements and Packages

### 4.1 Python version

Use Python **3.10 or later**. The current development environment uses Python 3.11.13. The app uses the modern built-in typing forms `list[CartLine]` and `list[dict]`; Python 3.10 satisfies the project's documented minimum.

### 4.2 Direct runtime dependencies

`requirements.txt` declares two packages:

- **FastAPI** (`fastapi>=0.115,<1.0`) provides the application class, HTTP route decorators, JSON serialization, error responses, automatic OpenAPI schema, and the `/docs` API explorer. The installed development version is 0.141.1.
- **Uvicorn** (`uvicorn>=0.30,<1.0`) is the ASGI server that listens on the local port and runs the FastAPI application. The installed development version is 0.54.0.

FastAPI brings in and uses **Starlette** for ASGI/web behavior and **Pydantic** for validation. They are transitive dependencies; they do not need separate lines in `requirements.txt`. The installed Pydantic development version is 2.13.5. Exact versions can vary because `requirements.txt` specifies compatible version ranges, not a fully pinned lockfile.

### 4.3 Python standard library

`main.py` also uses standard-library modules:

- `pathlib.Path` finds `static/` relative to `main.py`, even if the process starts in a different directory.
- `collections.Counter` combines repeated product IDs in a checkout request before stock and total calculations.
- `threading.Lock` prevents two requests served by this one Python process from simultaneously passing the same stock check and decrement.
- `uuid.uuid4` makes a short, hard-to-predict-looking sample order reference. The reference is not recorded in a database.

### 4.4 Browser dependencies

The browser needs no package installation. The site is HTML, CSS, and plain JavaScript delivered directly by FastAPI. The `Intl.NumberFormat`, `fetch`, `localStorage`, DOM APIs, and JavaScript language features used by the app are supplied by the browser.

The DM Sans and Playfair Display fonts load from Google Fonts. Home and product photos load from Unsplash. Those assets need network access; if the font request fails, CSS falls back to Georgia/Trebuchet MS, and if an image request fails, the image area retains its background color.

## 5. Install and Run

Run these commands from the `shop_demo` directory. On Linux/macOS with Bash or Zsh:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

For the C shell terminal shown in this workspace, activate the same environment with:

```csh
source .venv/bin/activate.csh
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

The `main:app` argument means “import the Python module `main.py` and run the FastAPI object named `app`.” Uvicorn's working directory should be `shop_demo`, because `main` is imported as a module from that directory. `--reload` restarts the development server after Python changes; it is a development convenience, not a production setting.

By default the site is at <http://127.0.0.1:8000/>. The automatically generated, interactive API reference is at <http://127.0.0.1:8000/docs>; the raw OpenAPI schema is at <http://127.0.0.1:8000/openapi.json>. If port 8000 is occupied, choose another available port with `--port 8001`, then use that port in the browser.

To leave the environment, use `deactivate` in Bash/Zsh, or `deactivate` in a C shell terminal after activation.

## 6. How the Pieces Fit Together

```text
Browser: GET /
    -> Uvicorn runs FastAPI
    -> FastAPI returns static/index.html
Browser: GET /static/styles.css and /static/app.js
    -> FastAPI's StaticFiles serves the frontend assets
Browser: GET /api/products
    -> FastAPI returns the product list and current in-memory stock as JSON
User edits the bag
    -> JavaScript stores product IDs and quantities in localStorage
User presses "Place demo order"
    -> JavaScript POSTs item IDs and quantities to /api/checkout
    -> FastAPI validates, looks up current server prices, checks stock, totals,
       and decrements in-memory stock under a process-local lock
    -> FastAPI returns a sample JSON receipt
    -> JavaScript clears localStorage's cart and displays the receipt
```

The browser never sends an amount as an input to `/api/checkout`: it sends only product IDs and quantities. The browser calculates a convenient preview subtotal, but the server calculates the order total independently from its catalog. This is important because browser data can be edited by the shopper and must not set a chargeable price.

Because the browser and API are both served from `127.0.0.1:8000`, `fetch('/api/...')` is a **same-origin** request. The app does not need CORS configuration for its own page. If a separate frontend is later hosted on a different origin, the API's allowed origins must be configured deliberately.

## 7. Backend: `main.py`

### 7.1 App setup and paths

`BASE_DIR = Path(__file__).resolve().parent` identifies the folder containing `main.py`. `FastAPI(title=..., version=...)` constructs the ASGI application. `app.mount('/static', StaticFiles(...), name='static')` registers a static-file sub-application: the browser's `/static/...` URLs map to the project's `static/` folder.

The `GET /` route returns `FileResponse(BASE_DIR / 'static' / 'index.html')`. This makes the same FastAPI server responsible for the storefront HTML as well as its API.

### 7.2 Catalog and money representation

`PRODUCTS` is a Python list of eight dictionaries. Each product has an ID, name, category, integer price, color/variant text, optional badge, image URL, and image alternative text. Prices are **integer cents**: `12800` represents `$128.00`. Keeping money as integer minor units avoids floating-point rounding in price arithmetic.

`PRODUCT_BY_ID` is built once as a dictionary for efficient ID lookups. `STOCK` is a separate dictionary initialized to quantity 12 for each product. These are demonstration data; neither catalog edits nor stock changes survive a Python process restart. The same Unsplash photo URL is used by both lamp products.

### 7.3 Checkout request models

`CartLine` is a Pydantic model with `product_id: str` and `quantity: int`. `Field(gt=0, le=20)` requires a positive integer no greater than 20 on each input line. No price field exists in the model. Pydantic/FastAPI returns HTTP 422 when the JSON is malformed or fails these constraints.

`CheckoutRequest` wraps a required list named `items`. `Field(min_length=1, max_length=30)` requires at least one and at most 30 cart lines. Lines may repeat product IDs; the route merges these quantities before evaluating the final quantity. It separately rejects an aggregated quantity over 20 for one product.

An example request:

```http
POST /api/checkout
Content-Type: application/json
```

```json
{
  "items": [
    { "product_id": "arc-lamp", "quantity": 1 },
    { "product_id": "daily-cup", "quantity": 2 }
  ]
}
```

### 7.4 Product route

`GET /api/products` returns each product dictionary with a `stock` value added from `STOCK`. FastAPI converts this returned Python list/dictionary into JSON automatically. The frontend initially calls this endpoint to get product descriptions, cents-based prices, images, badges, and stock.

### 7.5 Demo checkout route, step by step

`@app.post('/api/checkout')` registers the function as an HTTP POST route. FastAPI parses the JSON request body into a `CheckoutRequest` instance before calling the function. A validation failure becomes a standard FastAPI 422 response without entering the function.

Within `checkout()`:

1. `Counter()` sums quantities by `product_id`, so duplicate lines cannot bypass the aggregate quantity check.
2. An unknown ID produces HTTP 404.
3. An aggregate quantity greater than 20 produces HTTP 422.
4. `CHECKOUT_LOCK` makes the stock-check-and-decrement block mutually exclusive between threads in this Python process. Insufficient stock produces HTTP 409.
5. The total is the sum of each server-owned catalog price (in cents) multiplied by quantity. Client-supplied prices are not part of the request model and cannot set this total.
6. The route subtracts the purchased quantities from the in-memory `STOCK` dictionary.
7. On success, it returns a generated `order_id`, `item_count`, integer-cent `total`, `currency`, and a demo confirmation `message`.

For the example above, using the current catalog, the server returns a total of 18,400 cents (`$184.00`) and an item count of 3. The exact generated order ID varies.

Example response:

```json
{
  "order_id": "FF-XXXXXXXX",
  "item_count": 3,
  "total": 18400,
  "currency": "USD",
  "message": "Your order is confirmed. Thanks for shopping small."
}
```

The placeholder ID above is illustrative. Actual IDs are eight uppercase hexadecimal characters after the `FF-` prefix. The endpoint does **not** save that response anywhere and does **not** call a payment service.

### 7.6 HTTP outcomes

| Situation | HTTP status | Where it comes from |
| --- | ---: | --- |
| Product list loaded | 200 | `GET /api/products` |
| Demo receipt created, stock decremented | 200 | Successful `POST /api/checkout` |
| Unknown product ID | 404 | Explicit `HTTPException` in checkout |
| Inventory less than requested | 409 | Explicit `HTTPException` inside locked checkout section |
| Invalid JSON/model; absent or empty `items`; quantities outside 1–20; over 30 input lines | 422 | FastAPI/Pydantic request validation |
| Repeated lines add up to more than 20 units for one product | 422 | Explicit aggregate check in checkout |

### 7.7 Concurrency boundary

The `threading.Lock` is useful only inside the **one Python process** holding that lock. It does not coordinate other worker processes, other servers, or a database. Running multiple Uvicorn workers with this in-memory stock can therefore result in inconsistent availability. A production inventory update belongs in a persistent database transaction with suitable concurrency control.

## 8. Frontend: `static/index.html`

The HTML is the document structure; it does not contain the product catalog itself. It links the stylesheet at `/static/styles.css` and loads `/static/app.js` with `defer`. `defer` lets the browser parse the page before executing the script, so JavaScript can safely find the existing controls.

The page contains:

- An announcement bar, brand/header, category navigation, search field, and bag button.
- A hero section with a remote living-room image and a link to the product section.
- A shop section containing empty elements (`#category-filters` and `#product-grid`) that JavaScript fills from `/api/products`; sort and empty-state controls are also declared here.
- A short story/brand section and footer.
- A bag overlay and side drawer. Its product rows, count, and subtotal are populated dynamically. The checkout button is labelled **Place demo order** to indicate it is not a card-payment flow.

Semantic landmarks (`header`, `nav`, `main`, `section`, `footer`), headings, image `alt` text, control labels, an `aria-live` product grid, status messages, and an accessible dialog label help assistive technologies. CSS focus-visible styles make keyboard focus visible. When the bag is opened, JavaScript toggles dialog visibility/state and puts focus on the close button; Escape and clicking the backdrop close it.

Google Fonts is requested in the HTML `<head>`. CSS has a matching font import; the fonts are external, not vendored into the project. The hero and product image URLs also reference Unsplash; those are not bundled project assets.

## 9. Frontend Behavior: `static/app.js`

### 9.1 State and initialization

At the top of the script, `document.querySelector()` captures references to the product grid, search, filter area, sort control, drawer, bag rows, and checkout controls. `products` holds the current server response. `selectedCategory` starts at `All pieces`; `cart` is loaded from browser `localStorage` key `form-field-cart`.

The `init()` function fetches `GET /api/products`, then renders filters, product cards, and the bag and clears the busy state. If the fetch fails, it displays an unavailable message. `loadCart()` handles absent, invalid JSON, or an unexpected array; it falls back to an empty object. `saveCart()` persists changes in that browser's local storage. Local storage is not shared across browsers or devices and can be edited by its owner.

### 9.2 Browse the products

`renderFilters()` creates category buttons using categories found in the API response. Clicking a filter changes the selected category and redraws filters and products. The header category links do the same and scroll to the shop section.

`visibleProducts()` narrows by selected category and by a case-insensitive search over product name, category, and color. Its sort options are featured/server order, ascending price, descending price, and alphabetical name. `renderProducts()` writes the resulting cards into the grid, formats cents as USD with `Intl.NumberFormat`, uses the server stock to disable sold-out products, and adds staggered appearance delays. Product images use lazy loading.

### 9.3 Add and edit bag items

The document-level click handler uses `event.target.closest()` to handle dynamically rendered Add-to-bag and quantity buttons. An add increments `cart[product.id]` if it is below the last loaded stock value, saves the cart, redraws the bag, and shows a short toast. The quantity minus button decrements; zero removes the item. The plus button is disabled at the known stock limit.

`cartEntries()` excludes IDs not present in the current product list and requires a positive integer quantity. `renderBag()` uses those entries to update the badge, drawer count, preview subtotal, product rows, and checkout-button enabled state. The browser subtotal is only a display estimate: the backend independently checks current stock and calculates its own total.

### 9.4 Place the demo order

When the checkout button is clicked, the handler disables the button, shows “Placing your order...”, and sends:

```javascript
fetch('/api/checkout', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    items: cartEntries().map(([product_id, quantity]) => ({ product_id, quantity }))
  })
});
```

The request contains only IDs and quantities. On a successful HTTP response, JavaScript clears local storage's cart, reloads products (so the bag sees the reduced stock), and displays the order ID and server-returned total. On a failed HTTP response, it displays FastAPI's `detail` message and leaves the cart in place. Network errors display the JavaScript error message. The code stops there: it does not redirect to a payment page, request card details, create a payment intent, or wait for a payment webhook.

## 10. Styling: `static/styles.css`

The stylesheet defines a small color-and-type system using CSS custom properties: warm paper/white backgrounds, dark ink, muted labels, lime-green accent, and red-orange accent. Display headings use Playfair Display; interface text uses DM Sans, with local generic fallbacks. Product cards use consistent image aspect ratios and keep badges positioned independently from product text.

The desktop product grid has four columns. At widths up to 940 pixels, the header and hero rearrange and the grid has three columns. Up to 620 pixels, the hero becomes a vertical stack and the grid has two columns; the product filters remain horizontally usable. At 1500 pixels and above, content receives a maximum-width style of centered padding. The bag drawer has a viewport-relative height and fixed position so its item list can scroll independently.

Subtle card/image hover and entrance transitions are included. A `prefers-reduced-motion: reduce` rule reduces animation and smooth scrolling for people who request less motion. CSS focus-visible outlines identify keyboard focus. Layout width was checked in a 390-pixel browser viewport; the document did not overflow horizontally.

## 11. API Examples for Manual Testing

With Uvicorn running from the project directory:

```sh
curl -i http://127.0.0.1:8000/
curl -s http://127.0.0.1:8000/api/products
curl -i -X POST http://127.0.0.1:8000/api/checkout \
  -H 'Content-Type: application/json' \
  -d '{"items":[{"product_id":"daily-cup","quantity":2}]}'
```

The final command creates a **demo order** and reduces `daily-cup` in-memory stock by two. Repeat it only if that demonstration side effect is acceptable. An unknown ID returns 404; quantity above stock returns 409; invalid model data returns 422. The OpenAPI `/docs` page can also send these requests interactively.

## 12. Verification Performed for This Project

The working implementation was checked with:

- Python compilation (`py_compile main.py`).
- Browser-script parsing (`node --check static/app.js`).
- HTTP checks for the home page, stylesheet, eight-product catalog, successful checkout, and reduced stock.
- A checkout request containing an extra, incorrect client `price` value; the server ignored it and used the catalog price.
- Error checks for unknown products (404) and orders above remaining stock (409).
- Browser interactions for category filtering, search, adding a product, bag subtotal, and demo checkout confirmation.
- A 390-pixel viewport horizontal-overflow check and a successful hero-image load.

These are development checks, not a comprehensive automated test suite. No dedicated pytest suite is currently included.

## 13. Important Limitations and Production Work

This is an educational/local demo, not a live commerce system:

1. **No payment provider:** there is no Stripe/PayPal SDK, payment session, card-entry UI, authorization, capture, refund, or payment event handler. No money is collected.
2. **No durable order record:** an order ID and response exist only for that request; there is no order table or purchase-history endpoint.
3. **No durable catalog or stock:** products and stock reset when the Python process restarts. A process-local lock cannot coordinate multiple application processes.
4. **Stock is reduced before any payment:** the demo treats its receipt as immediately successful and subtracts inventory at that point. A production payment flow must not tell the user it was paid before confirmed payment. It needs a defined reservation/expiry/release strategy and transactional stock updates.
5. **No customer/shipping/tax data:** there is no address, customer identity, shipping-rate calculation, tax calculation, order fulfillment, email, or return workflow.
6. **Cart is browser-local:** it does not synchronize between browsers/devices and is not a server-side, authenticated cart. The API must still validate every submitted ID, price, quantity, stock count, and order state.
7. **No payment secrets or HTTPS configuration:** those become essential when deploying or calling a real payment provider. Private keys must live in server-side environment/secret configuration, never in JavaScript or committed files.
8. **Externally hosted assets:** fonts and images depend on third-party availability and their terms. Store/optimize licensed production assets locally if reliability, privacy, or licensing requirements call for it.

### Recommended real-payment sequence

For a provider-hosted checkout such as Stripe Checkout, the safe high-level sequence is:

1. Browser posts the cart to this server, still sending only product IDs and quantities.
2. Server validates the cart, reads trusted current prices from the database, calculates delivery/tax where appropriate, and creates a **pending** order with a unique internal ID.
3. Server creates a provider Checkout Session for the pending order's calculated amount, using a secret API key held only by the server, and returns the provider's hosted checkout URL.
4. Browser redirects the shopper to that provider-hosted page. Raw card details go directly to the provider, not to this storefront server.
5. Provider redirects the shopper back to a result page. This redirect alone is not proof the customer paid.
6. Provider sends a server-to-server webhook. The app verifies the webhook signature and event and then updates the order to `paid` (or a failure/refund state) in a database. A verified webhook is the payment-state source of truth.
7. The app finalizes/reduces inventory transactionally and shows confirmation only when server-side payment status is verified. Retries use provider idempotency keys so they cannot accidentally create duplicate charges/orders.

The exact implementation depends on the chosen provider, test/live mode, shipping/tax rules, database, and deployment URL. The current app's order route would need to change rather than simply sending the existing demo response to a payment service.

## 14. Run and Update This Documentation

Edit `docs/COMPLETE_GUIDE.md` for the explanatory material. The PDF build script reads that document plus the current runtime source files and adds their full text as a source appendix; source listings therefore stay synchronized without copying code into this Markdown file manually.

Install the documentation-only dependencies once, then run the builder from `shop_demo`:

```sh
python -m pip install -r docs/requirements.txt
python docs/build_guide.py
```

The resulting PDF is `docs/COMPLETE_GUIDE.pdf`. `Markdown` converts the guide to an HTML structure, and `ReportLab` lays out the document and source code blocks. Neither documentation package is needed to run the storefront; they are not listed in the app's `requirements.txt`.