/**
 * phone_picker.js — Custom country-code phone picker with real flag images
 * Flags served from flagcdn.com (free, no API key, real PNG images).
 *
 * Usage:
 *   PhonePicker.init('wrapper-element-id', 'hidden-input-name', {
 *     defaultCode: '+250',   // optional
 *     initialValue: '',      // optional — pre-fill (e.g. when editing)
 *   });
 *
 * The hidden input (name="contact") will receive the full number e.g. "+250788000001"
 * The backend strips the "+" and country code digits, then validates 10–13 remaining digits.
 */

const PhonePicker = (() => {

  // ── Flag image helper ─────────────────────────────────────────────────────
  // flagcdn.com: free, no API key, real flag images for all ISO 3166-1 alpha-2 codes
  function flagImg(iso2) {
    const code = iso2.toLowerCase();
    return '<img src="https://flagcdn.com/w40/' + code + '.png" srcset="https://flagcdn.com/w80/' + code + '.png 2x" width="24" height="18" alt="' + iso2.toUpperCase() + '" class="phone-picker__flag-img" onerror="this.style.display=\'none\'">';
  }

  // ── Country list: [name, dialCode, iso2, [minDigits, maxDigits]] ──────────
  const COUNTRIES = [
    ['Rwanda',               '+250', 'rw', [9, 9]],
    ['Uganda',               '+256', 'ug', [9, 9]],
    ['Tanzania',             '+255', 'tz', [9, 9]],
    ['Kenya',                '+254', 'ke', [9, 9]],
    ['DR Congo',             '+243', 'cd', [9, 9]],
    ['Burundi',              '+257', 'bi', [8, 8]],
    ['South Africa',         '+27',  'za', [9, 9]],
    ['Nigeria',              '+234', 'ng', [8, 10]],
    ['Ghana',                '+233', 'gh', [9, 9]],
    ['Ethiopia',             '+251', 'et', [9, 9]],
    ['Sudan',                '+249', 'sd', [9, 9]],
    ['South Sudan',          '+211', 'ss', [9, 9]],
    ['Mozambique',           '+258', 'mz', [9, 9]],
    ['Zambia',               '+260', 'zm', [9, 9]],
    ['Zimbabwe',             '+263', 'zw', [9, 9]],
    ['Malawi',               '+265', 'mw', [9, 9]],
    ['Angola',               '+244', 'ao', [9, 9]],
    ['Cameroon',             '+237', 'cm', [9, 9]],
    ['Senegal',              '+221', 'sn', [9, 9]],
    ["Côte d'Ivoire",        '+225', 'ci', [10, 10]],
    ['Morocco',              '+212', 'ma', [9, 9]],
    ['Algeria',              '+213', 'dz', [9, 9]],
    ['Egypt',                '+20',  'eg', [10, 10]],
    ['France',               '+33',  'fr', [9, 9]],
    ['United Kingdom',       '+44',  'gb', [10, 10]],
    ['United States',        '+1',   'us', [10, 10]],
    ['Canada',               '+1',   'ca', [10, 10]],
    ['Germany',              '+49',  'de', [10, 11]],
    ['India',                '+91',  'in', [10, 10]],
    ['China',                '+86',  'cn', [11, 11]],
    ['Brazil',               '+55',  'br', [10, 11]],
    ['Australia',            '+61',  'au', [9, 9]],
    ['Japan',                '+81',  'jp', [10, 11]],
    ['Russia',               '+7',   'ru', [10, 10]],
    ['Saudi Arabia',         '+966', 'sa', [9, 9]],
    ['UAE',                  '+971', 'ae', [9, 9]],
    ['Turkey',               '+90',  'tr', [10, 10]],
    ['Pakistan',             '+92',  'pk', [10, 10]],
    ['Bangladesh',           '+880', 'bd', [10, 10]],
    ['Indonesia',            '+62',  'id', [9, 12]],
    ['Philippines',          '+63',  'ph', [10, 10]],
    ['Mexico',               '+52',  'mx', [10, 10]],
    ['Argentina',            '+54',  'ar', [10, 10]],
    ['Colombia',             '+57',  'co', [10, 10]],
    ['Portugal',             '+351', 'pt', [9, 9]],
    ['Spain',                '+34',  'es', [9, 9]],
    ['Italy',                '+39',  'it', [9, 11]],
    ['Netherlands',          '+31',  'nl', [9, 9]],
    ['Belgium',              '+32',  'be', [9, 9]],
    ['Switzerland',          '+41',  'ch', [9, 9]],
    ['Sweden',               '+46',  'se', [9, 9]],
    ['Norway',               '+47',  'no', [8, 8]],
    ['Denmark',              '+45',  'dk', [8, 8]],
    ['Finland',              '+358', 'fi', [9, 10]],
    ['Poland',               '+48',  'pl', [9, 9]],
    ['Ukraine',              '+380', 'ua', [9, 9]],
    ['Romania',              '+40',  'ro', [9, 9]],
    ['Greece',               '+30',  'gr', [10, 10]],
    ['Czech Republic',       '+420', 'cz', [9, 9]],
    ['Hungary',              '+36',  'hu', [9, 9]],
    ['Slovakia',             '+421', 'sk', [9, 9]],
    ['Austria',              '+43',  'at', [10, 11]],
    ['Israel',               '+972', 'il', [9, 9]],
    ['Iran',                 '+98',  'ir', [10, 10]],
    ['Iraq',                 '+964', 'iq', [10, 10]],
    ['Jordan',               '+962', 'jo', [9, 9]],
    ['Lebanon',              '+961', 'lb', [8, 8]],
    ['Syria',                '+963', 'sy', [9, 9]],
    ['Yemen',                '+967', 'ye', [9, 9]],
    ['Oman',                 '+968', 'om', [8, 8]],
    ['Qatar',                '+974', 'qa', [8, 8]],
    ['Kuwait',               '+965', 'kw', [8, 8]],
    ['Bahrain',              '+973', 'bh', [8, 8]],
    ['Malaysia',             '+60',  'my', [9, 10]],
    ['Singapore',            '+65',  'sg', [8, 8]],
    ['Thailand',             '+66',  'th', [9, 9]],
    ['Vietnam',              '+84',  'vn', [9, 10]],
    ['South Korea',          '+82',  'kr', [9, 10]],
    ['New Zealand',          '+64',  'nz', [8, 9]],
    ['Madagascar',           '+261', 'mg', [9, 9]],
    ['Mauritius',            '+230', 'mu', [8, 8]],
    ['Seychelles',           '+248', 'sc', [7, 7]],
    ['Cape Verde',           '+238', 'cv', [7, 7]],
    ['Sierra Leone',         '+232', 'sl', [8, 8]],
    ['Liberia',              '+231', 'lr', [8, 8]],
    ['Guinea',               '+224', 'gn', [9, 9]],
    ['Guinea-Bissau',        '+245', 'gw', [9, 9]],
    ['Gambia',               '+220', 'gm', [7, 7]],
    ['Mali',                 '+223', 'ml', [8, 8]],
    ['Burkina Faso',         '+226', 'bf', [8, 8]],
    ['Niger',                '+227', 'ne', [8, 8]],
    ['Chad',                 '+235', 'td', [8, 8]],
    ['Central African Rep.', '+236', 'cf', [8, 8]],
    ['Gabon',                '+241', 'ga', [8, 8]],
    ['Republic of Congo',    '+242', 'cg', [9, 9]],
    ['Equatorial Guinea',    '+240', 'gq', [9, 9]],
    ['São Tomé & Príncipe',  '+239', 'st', [7, 7]],
    ['Djibouti',             '+253', 'dj', [8, 8]],
    ['Somalia',              '+252', 'so', [8, 9]],
    ['Eritrea',              '+291', 'er', [7, 7]],
    ['Comoros',              '+269', 'km', [7, 7]],
    ['Mauritania',           '+222', 'mr', [8, 8]],
    ['Lesotho',              '+266', 'ls', [8, 8]],
    ['Eswatini',             '+268', 'sz', [8, 8]],
    ['Botswana',             '+267', 'bw', [8, 8]],
    ['Namibia',              '+264', 'na', [9, 9]],
    ['Togo',                 '+228', 'tg', [8, 8]],
    ['Benin',                '+229', 'bj', [8, 8]],
  ];

  // Preferred countries shown first (East Africa first)
  const PREFERRED = ['rw', 'ug', 'tz', 'ke', 'cd', 'bi'];

  function sortedCountries() {
    const preferred = COUNTRIES.filter(c => PREFERRED.includes(c[2]));
    const rest = COUNTRIES.filter(c => !PREFERRED.includes(c[2]))
                          .sort((a, b) => a[0].localeCompare(b[0]));
    return [...preferred, ...rest];
  }

  // Local number placeholder examples per country
  function getPlaceholder(c) {
    const ex = {
      'rw': '788 000 000', 'ug': '712 000 000', 'tz': '712 000 000',
      'ke': '712 000 000', 'cd': '812 000 000', 'bi': '79 000 000',
      'us': '202 555 0100', 'gb': '7700 900000', 'fr': '6 12 34 56 78',
      'de': '151 23456789', 'in': '98765 43210', 'cn': '131 0000 0000',
      'za': '71 000 0000',  'ng': '802 000 0000', 'gh': '24 000 0000',
    };
    return ex[c[2]] || '7XX XXX XXX';
  }

  // ── Build the picker ──────────────────────────────────────────────────────
  function buildPicker(wrapperId, hiddenName, opts) {
    opts = opts || {};
    const wrapper = document.getElementById(wrapperId);
    if (!wrapper) return null;

    const defaultCode  = opts.defaultCode  || '+250';
    const initialValue = opts.initialValue || '';
    const hintId       = opts.hintId       || (wrapperId + '-hint');

    const countries = sortedCountries();

    // Find default country by dial code
    let defaultCountry = countries.find(c => c[1] === defaultCode) || countries[0];

    // If initialValue starts with '+', detect country from it
    let initialLocal = initialValue;
    if (initialValue && initialValue.startsWith('+')) {
      for (const c of countries) {
        if (initialValue.startsWith(c[1])) {
          defaultCountry = c;
          initialLocal = initialValue.slice(c[1].length);
          break;
        }
      }
    }

    // ── Render HTML ──────────────────────────────────────────────────────────
    wrapper.innerHTML = `
      <div class="phone-picker" id="${wrapperId}-picker">
        <div class="phone-picker__box">
          <button type="button" class="phone-picker__trigger" id="${wrapperId}-flag-btn"
                  aria-label="Select country code" aria-expanded="false">
            <span class="phone-picker__flag">${flagImg(defaultCountry[2])}</span>
            <span class="phone-picker__caret">▾</span>
            <span class="phone-picker__code">${defaultCountry[1]}</span>
          </button>
          <div class="phone-picker__divider"></div>
          <input type="tel" class="phone-picker__input"
                 id="${wrapperId}-number"
                 placeholder="${getPlaceholder(defaultCountry)}"
                 maxlength="15"
                 autocomplete="tel-national"
                 value="${initialLocal}"
                 required>
        </div>
        <div class="phone-picker__dropdown" id="${wrapperId}-dropdown">
          <div class="phone-picker__search-wrap">
            <input type="text" class="phone-picker__search" placeholder="Search country…"
                   id="${wrapperId}-search" autocomplete="off">
          </div>
          <ul class="phone-picker__list" id="${wrapperId}-list" role="listbox">
            ${countries.map((c, i) => '<li class="phone-picker__item' + (i < PREFERRED.length ? ' phone-picker__item--preferred' : '') + '" data-idx="' + i + '" role="option" tabindex="-1"><span class="phone-picker__item-flag">' + flagImg(c[2]) + '</span><span class="phone-picker__item-name">' + c[0] + '</span><span class="phone-picker__item-code">' + c[1] + '</span></li>').join('')}
          </ul>
        </div>
        <input type="hidden" name="${hiddenName}" id="${wrapperId}-hidden"
               value="${initialValue ? defaultCountry[1] + initialLocal : ''}">
        <small class="phone-picker__hint" id="${hintId}"></small>
      </div>
    `;

    // ── Wire up behaviour ────────────────────────────────────────────────────
    const picker   = wrapper.querySelector('.phone-picker');
    const flagBtn  = wrapper.querySelector(`#${wrapperId}-flag-btn`);
    const dropdown = wrapper.querySelector(`#${wrapperId}-dropdown`);
    const searchEl = wrapper.querySelector(`#${wrapperId}-search`);
    const list     = wrapper.querySelector(`#${wrapperId}-list`);
    const numberEl = wrapper.querySelector(`#${wrapperId}-number`);
    const hiddenEl = wrapper.querySelector(`#${wrapperId}-hidden`);
    const hintEl   = document.getElementById(hintId);

    let selected = defaultCountry;

    function selectCountry(c) {
      selected = c;
      flagBtn.querySelector('.phone-picker__flag').innerHTML = flagImg(c[2]);
      flagBtn.querySelector('.phone-picker__code').textContent = c[1];
      numberEl.placeholder = getPlaceholder(c);
      closeDropdown();
      numberEl.focus();
      updateHidden();
      validateNumber();
    }

    function openDropdown() {
      dropdown.classList.add('open');
      flagBtn.setAttribute('aria-expanded', 'true');
      searchEl.value = '';
      filterList('');
      searchEl.focus();
    }

    function closeDropdown() {
      dropdown.classList.remove('open');
      flagBtn.setAttribute('aria-expanded', 'false');
    }

    function filterList(q) {
      const term = q.toLowerCase();
      list.querySelectorAll('.phone-picker__item').forEach(li => {
        const name = li.querySelector('.phone-picker__item-name').textContent.toLowerCase();
        const code = li.dataset.code;
        li.hidden = !(name.includes(term) || code.includes(term));
      });
    }

    function updateHidden() {
      const digits = numberEl.value.replace(/\D/g, '');
      hiddenEl.value = digits ? selected[1] + digits : '';
    }

    function validateNumber() {
      const digits = numberEl.value.replace(/\D/g, '');
      if (numberEl.value !== digits) numberEl.value = digits;

      const min = selected[3][0];
      const max = selected[3][1];

      if (!hintEl) return digits.length >= min && digits.length <= max;

      if (digits.length === 0) {
        hintEl.textContent = 'Enter local number (digits only)';
        hintEl.style.color = '';
        return false;
      }
      if (digits.length < min) {
        hintEl.textContent = `Too short — need at least ${min} digits for ${selected[0]}.`;
        hintEl.style.color = 'var(--danger, #e53e3e)';
        return false;
      }
      if (digits.length > max) {
        hintEl.textContent = `Too long — max ${max} digits for ${selected[0]}.`;
        hintEl.style.color = 'var(--danger, #e53e3e)';
        return false;
      }
      hintEl.textContent = `✓ ${selected[1]} ${digits}`;
      hintEl.style.color = 'var(--success, #38a169)';
      return true;
    }

    // ── Events ───────────────────────────────────────────────────────────────
    flagBtn.addEventListener('click', () => {
      dropdown.classList.contains('open') ? closeDropdown() : openDropdown();
    });

    searchEl.addEventListener('input', e => filterList(e.target.value));

    list.addEventListener('click', e => {
      const li = e.target.closest('.phone-picker__item');
      if (!li) return;
      const idx = parseInt(li.dataset.idx, 10);
      if (!isNaN(idx) && countries[idx]) selectCountry(countries[idx]);
    });

    searchEl.addEventListener('keydown', e => {
      if (e.key === 'ArrowDown') {
        const first = list.querySelector('.phone-picker__item:not([hidden])');
        if (first) first.focus();
        e.preventDefault();
      }
      if (e.key === 'Escape') closeDropdown();
    });

    list.addEventListener('keydown', e => {
      const items = [...list.querySelectorAll('.phone-picker__item:not([hidden])')];
      const idx   = items.indexOf(document.activeElement);
      if (e.key === 'ArrowDown' && idx < items.length - 1) { items[idx+1].focus(); e.preventDefault(); }
      if (e.key === 'ArrowUp')   { idx > 0 ? items[idx-1].focus() : searchEl.focus(); e.preventDefault(); }
      if (e.key === 'Enter' && idx >= 0) items[idx].click();
      if (e.key === 'Escape') closeDropdown();
    });

    document.addEventListener('click', e => {
      if (!picker.contains(e.target)) closeDropdown();
    });

    numberEl.addEventListener('input', () => { updateHidden(); validateNumber(); });

    const form = wrapper.closest('form');
    if (form) {
      form.addEventListener('submit', e => {
        if (!validateNumber()) {
          e.preventDefault();
          numberEl.focus();
        } else {
          updateHidden();
        }
      });
    }

    if (initialLocal) validateNumber();

    return { selectCountry, validateNumber, getValue: () => hiddenEl.value };
  }

  return { init: buildPicker };
})();
