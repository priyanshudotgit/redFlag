/**
 * redFlag Client Enhancements
 * Minimal vanilla JS for progressive enhancement without client frameworks
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Menu Toggle
  const mobileMenuBtn = document.getElementById('mobile-menu-btn');
  const mobileMenu = document.getElementById('mobile-menu');

  if (mobileMenuBtn && mobileMenu) {
    mobileMenuBtn.addEventListener('click', () => {
      const isExpanded = mobileMenuBtn.getAttribute('aria-expanded') === 'true';
      mobileMenuBtn.setAttribute('aria-expanded', !isExpanded);
      mobileMenu.classList.toggle('hidden');
    });
  }

  // 2. Reference Code Clipboard Copy
  const copyBtn = document.getElementById('copy-ref-btn');
  const refCodeEl = document.getElementById('ref-code-value');

  if (copyBtn && refCodeEl) {
    copyBtn.addEventListener('click', async () => {
      const text = refCodeEl.textContent.trim();
      try {
        await navigator.clipboard.writeText(text);
        const originalText = copyBtn.innerHTML;
        copyBtn.innerHTML = `
          <svg class="w-4 h-4 text-emerald-600 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
          Copied!
        `;
        setTimeout(() => {
          copyBtn.innerHTML = originalText;
        }, 3000);
      } catch (err) {
        console.error('Failed to copy reference code:', err);
      }
    });
  }

  // 3. Geolocation Autofill for Report Form
  const geoBtn = document.getElementById('fetch-geo-btn');
  const latInput = document.getElementById('id_latitude');
  const lngInput = document.getElementById('id_longitude');
  const addressInput = document.getElementById('id_address');
  const geoStatus = document.getElementById('geo-status');

  if (geoBtn && latInput && lngInput && addressInput) {
    geoBtn.addEventListener('click', () => {
      if (!navigator.geolocation) {
        if (geoStatus) geoStatus.textContent = 'Geolocation not supported by this browser.';
        return;
      }

      if (geoStatus) geoStatus.textContent = 'Acquiring GPS coordinates...';
      geoBtn.disabled = true;

      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const lat = position.coords.latitude;
          const lng = position.coords.longitude;
          latInput.value = lat.toFixed(6);
          lngInput.value = lng.toFixed(6);

          if (geoStatus) {
            geoStatus.textContent = `Coordinates captured: ${lat.toFixed(4)}, ${lng.toFixed(4)}`;
          }

          // Reverse geocode via OpenStreetMap Nominatim
          try {
            const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`, {
              headers: { 'Accept': 'application/json' }
            });
            if (res.ok) {
              const data = await res.json();
              if (data && data.display_name && !addressInput.value.trim()) {
                addressInput.value = data.display_name;
              }
            }
          } catch (e) {
            console.log('Reverse geocoding unavailable or offline; coordinates saved.');
          } finally {
            geoBtn.disabled = false;
          }
        },
        (error) => {
          geoBtn.disabled = false;
          if (geoStatus) {
            geoStatus.textContent = 'Unable to retrieve location. Please input address manually.';
          }
        },
        { timeout: 10000, enableHighAccuracy: true }
      );
    });
  }

  // 4. Dismissible Alerts
  document.querySelectorAll('.alert-dismiss-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const alert = e.target.closest('.alert-box');
      if (alert) alert.remove();
    });
  });
});

