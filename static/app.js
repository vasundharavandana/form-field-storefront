const productGrid = document.querySelector('#product-grid');
const categoryFilters = document.querySelector('#category-filters');
const searchInput = document.querySelector('#search-input');
const sortSelect = document.querySelector('#sort-select');
const emptyState = document.querySelector('#empty-state');
const bagDrawer = document.querySelector('#bag-drawer');
const bagOverlay = document.querySelector('#bag-overlay');
const bagItems = document.querySelector('#bag-items');
const checkoutButton = document.querySelector('#checkout-button');
const checkoutMessage = document.querySelector('#checkout-message');

const currency = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' });
let products = [];
let selectedCategory = 'All pieces';
let toastTimer;
let cart = loadCart();

function loadCart() {
  try {
    const saved = JSON.parse(localStorage.getItem('form-field-cart') || '{}');
    return saved && typeof saved === 'object' && !Array.isArray(saved) ? saved : {};
  } catch {
    return {};
  }
}

function saveCart() {
  localStorage.setItem('form-field-cart', JSON.stringify(cart));
}

function getProduct(id) {
  return products.find((product) => product.id === id);
}

function renderFilters() {
  const categories = ['All pieces', ...new Set(products.map((product) => product.category))];
  categoryFilters.innerHTML = '';
  categories.forEach((category) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = `filter-button${selectedCategory === category ? ' is-active' : ''}`;
    button.textContent = category;
    button.setAttribute('aria-pressed', String(selectedCategory === category));
    button.addEventListener('click', () => {
      selectedCategory = category;
      document.querySelectorAll('[data-nav-category]').forEach((link) => link.classList.remove('is-active'));
      renderFilters();
      renderProducts();
    });
    categoryFilters.append(button);
  });
}

function visibleProducts() {
  const query = searchInput.value.trim().toLowerCase();
  const filtered = products.filter((product) => {
    const matchesCategory = selectedCategory === 'All pieces' || product.category === selectedCategory;
    const matchesSearch = `${product.name} ${product.category} ${product.color}`.toLowerCase().includes(query);
    return matchesCategory && matchesSearch;
  });

  switch (sortSelect.value) {
    case 'price-asc': return filtered.sort((a, b) => a.price - b.price);
    case 'price-desc': return filtered.sort((a, b) => b.price - a.price);
    case 'name': return filtered.sort((a, b) => a.name.localeCompare(b.name));
    default: return filtered;
  }
}

function renderProducts() {
  const shown = visibleProducts();
  emptyState.hidden = shown.length > 0;
  productGrid.innerHTML = shown.map((product, index) => `
    <article class="product-card" style="animation-delay:${Math.min(index * 35, 245)}ms">
      <div class="product-image-wrap">
        <img class="product-image" src="${product.image}" alt="${product.alt}" loading="lazy">
        ${product.badge ? `<span class="product-badge">${product.badge}</span>` : ''}
      </div>
      <div class="product-info">
        <div class="product-title-row"><h3 class="product-name">${product.name}</h3><p class="product-price">${currency.format(product.price / 100)}</p></div>
        <p class="product-color">${product.color}</p>
        <button class="add-button" type="button" data-add="${product.id}" ${product.stock < 1 ? 'disabled' : ''}>${product.stock < 1 ? 'Sold out' : 'Add to bag'}</button>
      </div>
    </article>`).join('');
}

function cartEntries() {
  return Object.entries(cart).filter(([id, quantity]) => getProduct(id) && Number.isInteger(quantity) && quantity > 0);
}

function renderBag() {
  const items = cartEntries();
  const count = items.reduce((total, [, quantity]) => total + quantity, 0);
  const subtotal = items.reduce((total, [id, quantity]) => total + getProduct(id).price * quantity, 0);
  document.querySelector('#bag-count').textContent = count;
  document.querySelector('#drawer-count').textContent = `(${count})`;
  document.querySelector('#bag-subtotal').textContent = currency.format(subtotal / 100);
  bagItems.innerHTML = items.length ? items.map(([id, quantity]) => {
    const product = getProduct(id);
    return `<article class="bag-line">
      <img src="${product.image}" alt="" loading="lazy">
      <div class="bag-line-info"><h3>${product.name}</h3><p>${product.color}</p><div class="quantity-control" aria-label="Quantity for ${product.name}">
        <button type="button" data-quantity="-1" data-id="${id}" aria-label="Remove one ${product.name}">−</button>
        <span>${quantity}</span>
        <button type="button" data-quantity="1" data-id="${id}" aria-label="Add one ${product.name}" ${quantity >= product.stock ? 'disabled' : ''}>+</button>
      </div></div><p class="bag-line-price">${currency.format(product.price * quantity / 100)}</p>
    </article>`;
  }).join('') : '<p class="empty-bag">Nothing in here just yet. Your next favorite is out there.</p>';
  checkoutButton.disabled = items.length === 0;
}

function openBag() {
  bagOverlay.hidden = false;
  bagDrawer.inert = false;
  bagDrawer.setAttribute('aria-hidden', 'false');
  requestAnimationFrame(() => bagDrawer.classList.add('is-open'));
  document.querySelector('#bag-close').focus();
}

function closeBag() {
  bagDrawer.classList.remove('is-open');
  bagDrawer.inert = true;
  bagDrawer.setAttribute('aria-hidden', 'true');
  window.setTimeout(() => { bagOverlay.hidden = true; }, 260);
  document.querySelector('#bag-open').focus();
}

function showToast(message) {
  const toast = document.querySelector('#toast');
  toast.textContent = message;
  toast.classList.add('is-visible');
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => toast.classList.remove('is-visible'), 2100);
}

document.addEventListener('click', (event) => {
  const addButton = event.target.closest('[data-add]');
  if (addButton) {
    const product = getProduct(addButton.dataset.add);
    if (product && (cart[product.id] || 0) < product.stock) {
      cart[product.id] = (cart[product.id] || 0) + 1;
      saveCart();
      renderBag();
      showToast(`${product.name} added to your bag`);
    }
  }

  const quantityButton = event.target.closest('[data-quantity]');
  if (quantityButton) {
    const id = quantityButton.dataset.id;
    cart[id] = Math.max(0, (cart[id] || 0) + Number(quantityButton.dataset.quantity));
    if (!cart[id]) delete cart[id];
    saveCart();
    renderBag();
  }

  const categoryLink = event.target.closest('[data-nav-category]');
  if (categoryLink) {
    event.preventDefault();
    selectedCategory = categoryLink.dataset.navCategory;
    document.querySelectorAll('[data-nav-category]').forEach((link) => link.classList.toggle('is-active', link === categoryLink));
    renderFilters();
    renderProducts();
    document.querySelector('#shop').scrollIntoView({ behavior: 'smooth' });
  }
});

searchInput.addEventListener('input', renderProducts);
sortSelect.addEventListener('change', renderProducts);
document.querySelector('#bag-open').addEventListener('click', openBag);
document.querySelector('#bag-close').addEventListener('click', closeBag);
bagOverlay.addEventListener('click', closeBag);
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && !bagOverlay.hidden) closeBag();
});

checkoutButton.addEventListener('click', async () => {
  checkoutButton.disabled = true;
  checkoutMessage.classList.remove('is-error');
  checkoutMessage.textContent = 'Placing your order...';
  try {
    const response = await fetch('/api/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ items: cartEntries().map(([product_id, quantity]) => ({ product_id, quantity })) }),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || 'Checkout could not be completed.');
    cart = {};
    saveCart();
    renderBag();
    products = await fetchProducts();
    renderProducts();
    checkoutMessage.textContent = `Order ${result.order_id} confirmed. Total ${currency.format(result.total / 100)}.`;
  } catch (error) {
    checkoutMessage.textContent = error.message;
    checkoutMessage.classList.add('is-error');
    renderBag();
  }
});

async function fetchProducts() {
  const response = await fetch('/api/products');
  if (!response.ok) throw new Error('The product collection is unavailable.');
  return response.json();
}

async function init() {
  try {
    products = await fetchProducts();
    renderFilters();
    renderProducts();
    renderBag();
    productGrid.setAttribute('aria-busy', 'false');
  } catch {
    productGrid.innerHTML = '<p class="empty-state">The shop is taking a little breather. Refresh to try again.</p>';
    productGrid.setAttribute('aria-busy', 'false');
  }
}

init();
