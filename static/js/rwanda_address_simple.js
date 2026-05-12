// Simple Rwanda Address Implementation
// Provides basic administrative divisions for Rwanda

// Initialize dropdowns when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Rwanda address system...');

    // Enable all dropdowns
    enableDropdown('province');
    enableDropdown('district');
    enableDropdown('sector');
    enableDropdown('cell');
    enableDropdown('village');

    // Initialize with fallback data
    initializeWithFallbackData();
});

// Helper function to enable dropdowns
window.enableDropdown = function(dropdownId) {
    const dropdown = document.getElementById(dropdownId);
    if (dropdown) {
        dropdown.disabled = false;
    }
};

// Initialize with fallback data
function initializeWithFallbackData() {
    // Basic fallback data
    const fallbackProvinces = [
        { id: 'kigali', name: 'Kigali City' },
        { id: 'northern', name: 'Northern Province' },
        { id: 'southern', name: 'Southern Province' },
        { id: 'eastern', name: 'Eastern Province' },
        { id: 'western', name: 'Western Province' }
    ];

    // Populate provinces
    const provinceOptions = ['<option value="">Select Province...</option>'];
    fallbackProvinces.forEach(province => {
        provinceOptions.push(`<option value="${province.id}">${province.name}</option>`);
    });

    const provinceSelect = document.getElementById('province');
    if (provinceSelect) {
        provinceSelect.innerHTML = provinceOptions.join('');
    }
}

// Handle dropdown changes
document.addEventListener('DOMContentLoaded', function() {
    // Province change
    const provinceSelect = document.getElementById('province');
    if (provinceSelect) {
        provinceSelect.addEventListener('change', function() {
            console.log('Province changed to:', this.value);

            // Reset and disable lower dropdowns
            const districtSelect = document.getElementById('district');
            const sectorSelect = document.getElementById('sector');
            const cellSelect = document.getElementById('cell');
            const villageSelect = document.getElementById('village');

            districtSelect.disabled = true;
            sectorSelect.disabled = true;
            cellSelect.disabled = true;
            villageSelect.disabled = true;

            if (this.value) {
                getDistrictOptions(this.value).then(options => {
                    console.log('District options:', options);
                    populateDropdown('district', options);
                    districtSelect.disabled = false;

                    // Reset lower dropdowns
                    populateDropdown('sector', ['<option value="">Select Sector...</option>']);
                    populateDropdown('cell', ['<option value="">Select Cell...</option>']);
                    populateDropdown('village', ['<option value="">Select Village...</option>']);
                });
            } else {
                populateDropdown('district', ['<option value="">Select District...</option>']);
            }
        });
    }

    // District change
    const districtSelect = document.getElementById('district');
    if (districtSelect) {
        districtSelect.addEventListener('change', function() {
            console.log('District changed to:', this.value);

            // Reset and disable lower dropdowns
            const sectorSelect = document.getElementById('sector');
            const cellSelect = document.getElementById('cell');
            const villageSelect = document.getElementById('village');

            sectorSelect.disabled = true;
            cellSelect.disabled = true;
            villageSelect.disabled = true;

            if (this.value) {
                getSectorOptions(this.value).then(options => {
                    console.log('Sector options:', options);
                    populateDropdown('sector', options);
                    sectorSelect.disabled = false;

                    // Reset lower dropdowns
                    populateDropdown('cell', ['<option value="">Select Cell...</option>']);
                    populateDropdown('village', ['<option value="">Select Village...</option>']);
                });
            } else {
                populateDropdown('sector', ['<option value="">Select Sector...</option>']);
            }
        });
    }

    // Sector change
    const sectorSelect = document.getElementById('sector');
    if (sectorSelect) {
        sectorSelect.addEventListener('change', function() {
            console.log('Sector changed to:', this.value);

            // Reset and disable lower dropdowns
            const cellSelect = document.getElementById('cell');
            const villageSelect = document.getElementById('village');

            cellSelect.disabled = true;
            villageSelect.disabled = true;

            if (this.value) {
                getCellOptions(this.value).then(options => {
                    console.log('Cell options:', options);
                    populateDropdown('cell', options);
                    cellSelect.disabled = false;

                    // Reset village dropdown
                    populateDropdown('village', ['<option value="">Select Village...</option>']);
                });
            } else {
                populateDropdown('cell', ['<option value="">Select Cell...</option>']);
            }
        });
    }

    // Cell change
    const cellSelect = document.getElementById('cell');
    if (cellSelect) {
        cellSelect.addEventListener('change', function() {
            console.log('Cell changed to:', this.value);

            // Reset village dropdown
            const villageSelect = document.getElementById('village');
            villageSelect.disabled = true;

            if (this.value) {
                getVillageOptions(this.value).then(options => {
                    console.log('Village options:', options);
                    populateDropdown('village', options);
                    villageSelect.disabled = false;
                });
            } else {
                populateDropdown('village', ['<option value="">Select Village...</option>']);
            }
        });
    }
});

// Populate dropdown function
window.populateDropdown = function(selectId, options) {
    const select = document.getElementById(selectId);
    if (select) {
        select.innerHTML = options.join('');
    }
};

// Get district options
window.getDistrictOptions = async function(provinceId) {
    const options = ['<option value="">Select District...</option>'];

    // Fallback data for districts
    const fallbackDistricts = {
        'kigali': [
            { id: 'gasabo', name: 'Gasabo' },
            { id: 'kicukiro', name: 'Kicukiro' },
            { id: 'nyarugenge', name: 'Nyarugenge' }
        ],
        'northern': [
            { id: 'burera', name: 'Burera' },
            { id: 'gakenke', name: 'Gakenke' },
            { id: 'gicumbi', name: 'Gicumbi' },
            { id: 'musanze', name: 'Musanze' },
            { id: 'ruhango', name: 'Ruhango' },
            { id: 'rulindo', name: 'Rulindo' }
        ],
        'southern': [
            { id: 'huye', name: 'Huye' },
            { id: 'kamonyi', name: 'Kamonyi' },
            { id: 'muhanga', name: 'Muhanga' },
            { id: 'nyamagabe', name: 'Nyamagabe' },
            { id: 'nyaruguru', name: 'Nyaruguru' },
            { id: 'nyanza', name: 'Nyanza' },
            { id: 'ruhango', name: 'Ruhango' }
        ],
        'eastern': [
            { id: 'bugesera', name: 'Bugesera' },
            { id: 'gatsibo', name: 'Gatsibo' },
            { id: 'kayonza', name: 'Kayonza' },
            { id: 'ngoma', name: 'Ngoma' },
            { id: 'nyagatare', name: 'Nyagatare' },
            { id: 'rwamagana', name: 'Rwamagana' }
        ],
        'western': [
            { id: 'karongi', name: 'Karongi' },
            { id: 'ngororero', name: 'Ngororero' },
            { id: 'nyabihu', name: 'Nyabihu' },
            { id: 'nyamasheke', name: 'Nyamasheke' },
            { id: 'rubavu', name: 'Rubavu' },
            { id: 'rusizi', name: 'Rusizi' },
            { id: 'rutsiro', name: 'Rutsiro' }
        ]
    };

    try {
        // Use fallback data if npm package fails to load
        if (fallbackDistricts[provinceId]) {
            fallbackDistricts[provinceId].forEach(district => {
                options.push(`<option value="${district.id}">${district.name}</option>`);
            });
        }
    } catch (error) {
        console.error('Error fetching districts:', error);
    }

    return options;
};

// Get sector options
window.getSectorOptions = async function(districtId) {
    const options = ['<option value="">Select Sector...</option>'];

    // Fallback data for sectors (simplified)
    const fallbackSectors = {
        'gasabo': [
            { id: 'busanza', name: 'Busanza' },
            { id: 'jali', name: 'Jali' },
            { id: 'kacyiru', name: 'Kacyiru' },
            { id: 'kinyinya', name: 'Kinyinya' },
            { id: 'remera', name: 'Remera' },
            { id: 'rubengera', name: 'Rubengera' },
            { id: 'rwezamenyo', name: 'Rwezamenyo' }
        ],
        'kicukiro': [
            { id: 'gahanga', name: 'Gahanga' },
            { id: 'gikondo', name: 'Gikondo' },
            { id: ' Kanombe', name: 'Kanombe' },
            { id: 'kicukiro', name: 'Kicukiro' },
            { id: 'nyarugenge', name: 'Nyarugenge' }
        ],
        'nyarugenge': [
            { id: 'gikondo', name: 'Gikondo' },
            { id: 'kabusunzu', name: 'Kabusunzu' },
            { id: 'kacyiru', name: 'Kacyiru' },
            { id: 'nyarugenge', name: 'Nyarugenge' },
            { id: 'rwezamenyo', name: 'Rwezamenyo' }
        ]
    };

    try {
        // Use fallback data if npm package fails to load
        if (fallbackSectors[districtId]) {
            fallbackSectors[districtId].forEach(sector => {
                options.push(`<option value="${sector.id}">${sector.name}</option>`);
            });
        }
    } catch (error) {
        console.error('Error fetching sectors:', error);
    }

    return options;
};

// Get cell options
window.getCellOptions = async function(sectorId) {
    const options = ['<option value="">Select Cell...</option>'];

    // Fallback data for cells (simplified)
    const fallbackCells = {
        'busanza': [
            { id: 'busanza1', name: 'Busanza 1' },
            { id: 'busanza2', name: 'Busanza 2' }
        ],
        'jali': [
            { id: 'jali1', name: 'Jali 1' },
            { id: 'jali2', name: 'Jali 2' }
        ],
        'kacyiru': [
            { id: 'kacyiru1', name: 'Kacyiru 1' },
            { id: 'kacyiru2', name: 'Kacyiru 2' }
        ]
    };

    try {
        // Use fallback data if npm package fails to load
        if (fallbackCells[sectorId]) {
            fallbackCells[sectorId].forEach(cell => {
                options.push(`<option value="${cell.id}">${cell.name}</option>`);
            });
        }
    } catch (error) {
        console.error('Error fetching cells:', error);
    }

    return options;
};

// Get village options
window.getVillageOptions = async function(cellId) {
    const options = ['<option value="">Select Village...</option>'];

    // Fallback data for villages (simplified)
    const fallbackVillages = {
        'busanza1': [
            { id: 'busanza1-1', name: 'Busanza 1-1' },
            { id: 'busanza1-2', name: 'Busanza 1-2' }
        ],
        'busanza2': [
            { id: 'busanza2-1', name: 'Busanza 2-1' },
            { id: 'busanza2-2', name: 'Busanza 2-2' }
        ],
        'jali1': [
            { id: 'jali1-1', name: 'Jali 1-1' },
            { id: 'jali1-2', name: 'Jali 1-2' }
        ],
        'jali2': [
            { id: 'jali2-1', name: 'Jali 2-1' },
            { id: 'jali2-2', name: 'Jali 2-2' }
        ],
        'kacyiru1': [
            { id: 'kacyiru1-1', name: 'Kacyiru 1-1' },
            { id: 'kacyiru1-2', name: 'Kacyiru 1-2' }
        ],
        'kacyiru2': [
            { id: 'kacyiru2-1', name: 'Kacyiru 2-1' },
            { id: 'kacyiru2-2', name: 'Kacyiru 2-2' }
        ]
    };

    try {
        // Use fallback data if npm package fails to load
        if (fallbackVillages[cellId]) {
            fallbackVillages[cellId].forEach(village => {
                options.push(`<option value="${village.id}">${village.name}</option>`);
            });
        }
    } catch (error) {
        console.error('Error fetching villages:', error);
    }

    return options;
};
