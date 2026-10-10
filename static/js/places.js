/**
 * Suggest Places - Multi-Place Repeating Card Form Logic
 * Matches the reference screenshot:
 * - Left: Tall portrait image with "★ Primary Image" badge
 * - Right: Clean grid with "Things to See & Do" placed directly below "Short Description"
 */

let placeCounter = 0;

// Curated high-res default photos
const defaultPlacePhotos = [
  "https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?auto=format&fit=crop&w=1200&q=80", // Alleppey Backwaters
  "https://images.unsplash.com/photo-1544735716-392fe2489ffa?auto=format&fit=crop&w=1200&q=80", // Munnar Tea Gardens
  "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?auto=format&fit=crop&w=1200&q=80", // Fort Kochi
  "https://images.unsplash.com/photo-1566837945700-30057527ade0?auto=format&fit=crop&w=1200&q=80", // Kashmir
  "https://images.unsplash.com/photo-1537996194471-e657df975ab4?auto=format&fit=crop&w=1200&q=80"  // Bali
];

function createPlaceCardHTML(index, number) {
  const defaultPhoto = defaultPlacePhotos[(number - 1) % defaultPlacePhotos.length];

  return `
    <div class="place-card-repeater" id="placeCard_${index}" data-index="${index}">
      
      <!-- Top Action Controls matching reference screenshot -->
      <div class="place-card-header">
        <button type="button" class="btn-remove-card" onclick="removePlaceCard(${index})">
          <i class="bi bi-trash3"></i> Remove
        </button>
        <button type="button" class="btn-add-card" onclick="addPlaceCard()">
          <i class="bi bi-plus-lg"></i> Add Another Place
        </button>
      </div>

      <div class="row g-4 align-items-stretch">
        <!-- LEFT COLUMN: Tall Portrait Image Preview with Primary Image Badge -->
        <div class="col-lg-3 col-md-4">
          <div class="place-hero-portrait-frame">
            <span class="primary-image-badge">
              <i class="bi bi-star-fill text-warning"></i> Primary Image
            </span>
            <img id="imgPreview_${index}" src="${defaultPhoto}" alt="Place ${number}">
          </div>
          <!-- Hidden inputs for file & URL -->
          <input type="file" id="fileInput_${index}" name="image_file_${index}" class="d-none" accept="image/*" onchange="previewUploadedImage(this, ${index})">
          <input type="hidden" id="imageUrl_${index}" name="image_url_${index}" value="${defaultPhoto}">
        </div>

        <!-- RIGHT AREA: Form fields grid -->
        <div class="col-lg-9 col-md-8 d-flex flex-column justify-content-between">
          <div class="row g-3">
            
            <!-- ROW 1: Place Name and Category -->
            <div class="col-md-7">
              <label class="tp-field-label">
                <i class="bi bi-geo-alt-fill text-tp-teal"></i> Place Name <span class="text-danger">*</span>
              </label>
              <div class="tp-input-group">
                <span class="input-icon"><i class="bi bi-geo-alt"></i></span>
                <input type="text" name="place_name_${index}" class="form-control" required placeholder="e.g., Alleppey Backwaters">
              </div>
            </div>

            <div class="col-md-5">
              <label class="tp-field-label">
                <i class="bi bi-tag-fill text-tp-teal"></i> Category <span class="text-danger">*</span>
              </label>
              <div class="tp-input-group">
                <span class="input-icon"><i class="bi bi-leaf"></i></span>
                <select name="category_${index}" class="form-select" required>
                  <option value="Nature" selected>Nature</option>
                  <option value="Beach">Beach</option>
                  <option value="Historical">Historical</option>
                  <option value="Mountain">Mountain</option>
                  <option value="Adventure">Adventure</option>
                  <option value="Food">Food</option>
                  <option value="Culture">Culture</option>
                </select>
              </div>
            </div>

            <!-- ROW 2: Short Description -->
            <div class="col-12">
              <label class="tp-field-label">
                <i class="bi bi-file-text-fill text-tp-teal"></i> Short Description <span class="text-danger">*</span>
              </label>
              <div class="tp-textarea-wrapper">
                <textarea name="short_description_${index}" rows="2" maxlength="500" required 
                          oninput="updateCharCount(this, 'descCount_${index}')" 
                          placeholder="A serene network of canals, lakes and lagoons with lush greenery..."></textarea>
                <span class="tp-char-count" id="descCount_${index}">0/500</span>
              </div>
            </div>

            <!-- ROW 3: Things to See & Do (BELOW Short Description as requested) -->
            <div class="col-12">
              <label class="tp-field-label">
                <i class="bi bi-binoculars-fill text-tp-teal"></i> Things to See & Do <span class="text-danger">*</span>
              </label>
              <div class="tp-textarea-wrapper">
                <textarea name="things_to_see_${index}" rows="3" maxlength="1000" required 
                          oninput="updateCharCount(this, 'thingsCount_${index}', 1000)"
                          placeholder="• Houseboat cruise&#10;• Village walk&#10;• Bird watching&#10;• Local markets"></textarea>
                <span class="tp-char-count" id="thingsCount_${index}">0/1000</span>
              </div>
            </div>

            <!-- ROW 4: Best Time to Visit, Estimated Cost / Person, Recommended Duration -->
            <div class="col-md-4">
              <label class="tp-field-label">
                <i class="bi bi-calendar3-event-fill text-tp-teal"></i> Best Time to Visit <span class="text-danger">*</span>
              </label>
              <div class="tp-input-group">
                <span class="input-icon"><i class="bi bi-calendar3"></i></span>
                <input type="text" name="best_time_to_visit_${index}" class="form-control" required placeholder="Oct – Mar">
              </div>
            </div>

            <div class="col-md-4">
              <label class="tp-field-label">
                <i class="bi bi-credit-card-2-front-fill text-tp-teal"></i> Estimated Cost / Person <span class="text-danger">*</span>
              </label>
              <div class="tp-input-group justify-content-between">
                <span class="input-icon fw-bold">₹</span>
                <input type="number" name="estimated_cost_min_${index}" class="form-control text-center px-1" min="0" step="50" required placeholder="1000" style="max-width: 85px;">
                <span class="text-muted small px-1">–</span>
                <input type="number" name="estimated_cost_max_${index}" class="form-control text-center px-1" min="0" step="50" required placeholder="2500" style="max-width: 85px;">
              </div>
            </div>

            <div class="col-md-4">
              <label class="tp-field-label">
                <i class="bi bi-clock-fill text-tp-teal"></i> Recommended Duration <span class="text-danger">*</span>
              </label>
              <div class="tp-input-group">
                <span class="input-icon"><i class="bi bi-clock"></i></span>
                <input type="text" name="recommended_duration_${index}" class="form-control" required placeholder="1 – 2 days">
              </div>
            </div>

            <!-- ROW 5: Image Controls and Address -->
            <div class="col-md-6">
              <label class="tp-field-label">
                <i class="bi bi-image-fill text-tp-teal"></i> Image URL / Upload Image <span class="text-danger">*</span>
              </label>
              <div class="tp-image-upload-box">
                <div class="thumb-mini-wrapper">
                  <img id="thumbMini_${index}" src="${defaultPhoto}" alt="Thumbnail" class="thumb-mini-img">
                </div>
                <button type="button" class="btn-tp-upload-action" onclick="document.getElementById('fileInput_${index}').click()">
                  <i class="bi bi-cloud-arrow-up"></i> Upload Photo
                </button>
                <button type="button" class="btn-tp-upload-action" onclick="promptImageUrl(${index})">
                  <i class="bi bi-link-45deg"></i> Web URL
                </button>
              </div>
            </div>

            <div class="col-md-6">
              <label class="tp-field-label">
                <i class="bi bi-pin-map-fill text-tp-teal"></i> Address (Optional)
              </label>
              <div class="tp-input-group">
                <span class="input-icon"><i class="bi bi-geo-alt"></i></span>
                <input type="text" name="address_${index}" class="form-control" placeholder="e.g., Alleppey, Alappuzha, Kerala, India">
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  `;
}

function updateCharCount(el, counterId, maxLen = 500) {
  const counter = document.getElementById(counterId);
  if (counter) {
    counter.textContent = `${el.value.length}/${el.maxLength || maxLen}`;
  }
}

function promptImageUrl(index) {
  const current = document.getElementById(`imageUrl_${index}`).value;
  const newUrl = prompt("Enter an Image Web URL (http/https):", current);
  if (newUrl && (newUrl.startsWith('http://') || newUrl.startsWith('https://'))) {
    previewUrlImage(newUrl, index);
  }
}

function addPlaceCard() {
  const container = document.getElementById('placesContainer');
  if (!container) return;

  const currentCards = container.querySelectorAll('.place-card-repeater');
  const newNumber = currentCards.length + 1;
  const newIndex = placeCounter++;

  const wrapper = document.createElement('div');
  wrapper.innerHTML = createPlaceCardHTML(newIndex, newNumber).trim();
  container.appendChild(wrapper.firstChild);
}

function removePlaceCard(index) {
  const container = document.getElementById('placesContainer');
  if (!container) return;

  const card = document.getElementById(`placeCard_${index}`);
  if (card) {
    const totalCards = container.querySelectorAll('.place-card-repeater').length;
    if (totalCards <= 1) {
      alert('You must have at least one place card in your submission.');
      return;
    }
    card.remove();
  }
}

function previewUploadedImage(input, index) {
  if (input.files && input.files[0]) {
    const reader = new FileReader();
    reader.onload = function (e) {
      const heroPreview = document.getElementById(`imgPreview_${index}`);
      const miniThumb = document.getElementById(`thumbMini_${index}`);
      if (heroPreview) heroPreview.src = e.target.result;
      if (miniThumb) miniThumb.src = e.target.result;
    };
    reader.readAsDataURL(input.files[0]);
  }
}

function previewUrlImage(url, index) {
  if (url && (url.startsWith('http://') || url.startsWith('https://'))) {
    const heroPreview = document.getElementById(`imgPreview_${index}`);
    const miniThumb = document.getElementById(`thumbMini_${index}`);
    const hiddenUrl = document.getElementById(`imageUrl_${index}`);
    if (heroPreview) heroPreview.src = url;
    if (miniThumb) miniThumb.src = url;
    if (hiddenUrl) hiddenUrl.value = url;
  }
}

document.addEventListener('DOMContentLoaded', function () {
  const container = document.getElementById('placesContainer');
  if (container && container.children.length === 0) {
    addPlaceCard();
  }
});
