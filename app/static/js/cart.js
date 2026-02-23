// =============================================================================
// Cart Management - Vanilla JS with localStorage
// =============================================================================

const CART_STORAGE_KEY = "cart-items";

// -----------------------------------------------------------------------------
// Cart Data Management
// -----------------------------------------------------------------------------

/**
 * Get the current cart items from localStorage.
 * @returns {Array<{id: string, name: string, price: number, quantity: number, slug: string, image: string}>}
 */
function getCart() {
  try {
    const raw = localStorage.getItem(CART_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

/**
 * Save cart items to localStorage.
 * @param {Array} items
 */
function saveCart(items) {
  localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(items));
}

// -----------------------------------------------------------------------------
// Cart Operations
// -----------------------------------------------------------------------------

/**
 * Add an item to the cart or increment its quantity if it already exists.
 * @param {string} id - Product ID
 * @param {string} name - Product name
 * @param {number} price - Price in cents
 * @param {string} slug - Product slug for URL
 * @param {string} image - Image URL
 */
function addToCart(id, name, price, slug, image) {
  const items = getCart();
  const existing = items.find(function (item) {
    return String(item.id) === String(id);
  });

  if (existing) {
    existing.quantity += 1;
  } else {
    items.push({
      id: String(id),
      name: name,
      price: price,
      quantity: 1,
      slug: slug,
      image: image || "",
    });
  }

  saveCart(items);
  updateCartBadge();
  showToast(name + " added to cart", "success");
}

/**
 * Remove an item from the cart entirely.
 * @param {string} id - Product ID
 */
function removeFromCart(id) {
  var items = getCart().filter(function (item) {
    return String(item.id) !== String(id);
  });
  saveCart(items);
  updateCartBadge();
  renderCartPage();
  showToast("Item removed from cart", "success");
}

/**
 * Update the quantity of a specific cart item.
 * Removes the item if quantity drops to 0 or below.
 * @param {string} id - Product ID
 * @param {number} quantity - New quantity
 */
function updateQuantity(id, quantity) {
  var items = getCart();

  if (quantity <= 0) {
    items = items.filter(function (item) {
      return String(item.id) !== String(id);
    });
  } else {
    var existing = items.find(function (item) {
      return String(item.id) === String(id);
    });
    if (existing) {
      existing.quantity = quantity;
    }
  }

  saveCart(items);
  updateCartBadge();
  renderCartPage();
}

/**
 * Clear the entire cart.
 */
function clearCart() {
  saveCart([]);
  updateCartBadge();
  renderCartPage();
}

/**
 * Get the total price of all items in the cart (in cents).
 * @returns {number}
 */
function getCartTotal() {
  return getCart().reduce(function (sum, item) {
    return sum + item.price * item.quantity;
  }, 0);
}

/**
 * Get the total number of items in the cart (sum of quantities).
 * @returns {number}
 */
function getCartCount() {
  return getCart().reduce(function (sum, item) {
    return sum + item.quantity;
  }, 0);
}

// -----------------------------------------------------------------------------
// Price Formatting
// -----------------------------------------------------------------------------

/**
 * Format a price in cents to a display string like "$24.99".
 * @param {number} cents
 * @returns {string}
 */
function formatPrice(cents) {
  var dollars = (cents / 100).toFixed(2);
  return "$" + dollars;
}

// -----------------------------------------------------------------------------
// UI Updates
// -----------------------------------------------------------------------------

/**
 * Update the cart badge count in the header.
 * Shows the badge when count > 0, hides it when count is 0.
 */
function updateCartBadge() {
  var count = getCartCount();
  var badge = document.getElementById("cart-badge");
  var badgeMobile = document.getElementById("cart-badge-mobile");

  [badge, badgeMobile].forEach(function (el) {
    if (!el) return;
    if (count > 0) {
      el.textContent = count > 99 ? "99+" : String(count);
      el.classList.remove("hidden");
    } else {
      el.textContent = "0";
      el.classList.add("hidden");
    }
  });
}

/**
 * Show a toast notification that auto-dismisses after 3 seconds.
 * @param {string} message - The message to display
 * @param {string} [type="success"] - "success" or "error"
 */
function showToast(message, type) {
  type = type || "success";
  var container = document.getElementById("toast-container");
  if (!container) return;

  var toast = document.createElement("div");
  toast.className = type === "error" ? "toast-error" : "toast-success";

  // Icon
  var iconSvg = "";
  if (type === "success") {
    iconSvg =
      '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>';
  } else {
    iconSvg =
      '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>';
  }

  toast.innerHTML = iconSvg + "<span>" + escapeHtml(message) + "</span>";
  container.appendChild(toast);

  // Auto-dismiss after 3 seconds
  setTimeout(function () {
    toast.style.transition = "opacity 0.3s ease, transform 0.3s ease";
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    setTimeout(function () {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    }, 300);
  }, 3000);
}

/**
 * Escape HTML special characters to prevent XSS.
 * @param {string} str
 * @returns {string}
 */
function escapeHtml(str) {
  var div = document.createElement("div");
  div.appendChild(document.createTextNode(str));
  return div.innerHTML;
}

// -----------------------------------------------------------------------------
// Cart Page Rendering
// -----------------------------------------------------------------------------

/**
 * Render the cart page contents. Only runs if #cart-page is present in the DOM.
 * Toggles between empty and filled states, renders item cards, and updates totals.
 */
function renderCartPage() {
  var cartPage = document.getElementById("cart-page");
  if (!cartPage) return;

  var items = getCart();
  var emptyEl = document.getElementById("cart-empty");
  var filledEl = document.getElementById("cart-filled");
  var itemsContainer = document.getElementById("cart-items");
  var subtotalEl = document.getElementById("cart-subtotal");
  var totalEl = document.getElementById("cart-total");

  if (items.length === 0) {
    // Show empty state
    if (emptyEl) emptyEl.classList.remove("hidden");
    if (filledEl) filledEl.classList.add("hidden");
    return;
  }

  // Show filled state
  if (emptyEl) emptyEl.classList.add("hidden");
  if (filledEl) filledEl.classList.remove("hidden");

  // Render cart items
  if (itemsContainer) {
    itemsContainer.innerHTML = items.map(function (item) {
      return buildCartItemCard(item);
    }).join("");
  }

  // Update totals
  var total = getCartTotal();
  if (subtotalEl) subtotalEl.textContent = formatPrice(total);
  if (totalEl) totalEl.textContent = formatPrice(total);
}

/**
 * Build the HTML for a single cart item card.
 * @param {{id: string, name: string, price: number, quantity: number, slug: string, image: string}} item
 * @returns {string}
 */
function buildCartItemCard(item) {
  var lineTotal = item.price * item.quantity;
  var escapedName = escapeHtml(item.name);
  var escapedId = escapeHtml(String(item.id));
  var escapedSlug = escapeHtml(item.slug || "");

  var imageHtml;
  if (item.image) {
    imageHtml =
      '<img src="' +
      escapeHtml(item.image) +
      '" alt="' +
      escapedName +
      '" class="w-full h-full object-cover">';
  } else {
    imageHtml =
      '<div class="w-full h-full flex items-center justify-center text-xs text-[hsl(var(--muted-foreground))]">No Image</div>';
  }

  return (
    '<div class="card">' +
      '<div class="p-4 flex items-center gap-4">' +
        // Image
        '<div class="w-20 h-20 bg-[hsl(var(--muted))] rounded overflow-hidden flex-shrink-0">' +
          imageHtml +
        "</div>" +
        // Name and unit price
        '<div class="flex-1 min-w-0">' +
          '<a href="/products/' + escapedSlug + '" class="font-medium hover:underline line-clamp-1">' +
            escapedName +
          "</a>" +
          '<p class="text-sm text-[hsl(var(--muted-foreground))]">' +
            formatPrice(item.price) +
          "</p>" +
        "</div>" +
        // Quantity controls
        '<div class="flex items-center gap-2">' +
          '<button onclick="updateQuantity(\'' + escapedId + "', " + (item.quantity - 1) + ')" class="btn-outline btn-icon h-8 w-8">' +
            '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/></svg>' +
          "</button>" +
          '<span class="w-8 text-center text-sm font-medium">' + item.quantity + "</span>" +
          '<button onclick="updateQuantity(\'' + escapedId + "', " + (item.quantity + 1) + ')" class="btn-outline btn-icon h-8 w-8">' +
            '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>' +
          "</button>" +
        "</div>" +
        // Line total
        '<p class="font-semibold w-24 text-right">' + formatPrice(lineTotal) + "</p>" +
        // Remove button
        '<button onclick="removeFromCart(\'' + escapedId + '\')" class="btn-ghost btn-icon">' +
          '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>' +
        "</button>" +
      "</div>" +
    "</div>"
  );
}

// -----------------------------------------------------------------------------
// Initialization
// -----------------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", function () {
  updateCartBadge();
  renderCartPage();
});

// -----------------------------------------------------------------------------
// Expose all functions globally for onclick handlers in templates
// -----------------------------------------------------------------------------

window.getCart = getCart;
window.saveCart = saveCart;
window.addToCart = addToCart;
window.removeFromCart = removeFromCart;
window.updateQuantity = updateQuantity;
window.clearCart = clearCart;
window.getCartTotal = getCartTotal;
window.getCartCount = getCartCount;
window.formatPrice = formatPrice;
window.updateCartBadge = updateCartBadge;
window.showToast = showToast;
window.renderCartPage = renderCartPage;
