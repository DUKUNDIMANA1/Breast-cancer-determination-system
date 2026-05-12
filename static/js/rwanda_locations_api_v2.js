/**
 * Rwanda Locations API v2 Integration
 * Uses PublicAPI.dev Rwanda Locations API for real-time data
 */

class RwandaLocationsManager {
    constructor() {
        this.cache = {};
        this.cacheTimeout = 300000; // 5 minutes cache
        this.apiBase = '/api/rwanda-locations-v2';
    }

    // Helper function to check cache validity
    isCacheValid(cacheKey) {
        if (!this.cache[cacheKey]) return false;
        const now = Date.now();
        return (now - this.cache[cacheKey].timestamp) < this.cacheTimeout;
    }

    // Helper function to get from cache
    getFromCache(cacheKey) {
        if (this.isCacheValid(cacheKey)) {
            return this.cache[cacheKey].data;
        }
        return null;
    }

    // Helper function to cache data
    cacheData(cacheKey, data) {
        this.cache[cacheKey] = {
            data: data,
            timestamp: Date.now()
        };
    }

    // Generic API call function
    async apiCall(endpoint, params = {}) {
        try {
            const url = new URL(`${this.apiBase}${endpoint}`, window.location.origin);
            Object.keys(params).forEach(key => {
                if (params[key]) {
                    url.searchParams.append(key, params[key]);
                }
            });

            const response = await fetch(url.toString());
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            return result.data || [];
        } catch (error) {
            console.error(`API call failed for ${endpoint}:`, error);
            return [];
        }
    }

    // Get provinces
    async getProvinces() {
        const cacheKey = 'provinces';
        
        // Check cache first
        const cached = this.getFromCache(cacheKey);
        if (cached) {
            return cached;
        }

        try {
            const provinces = await this.apiCall('/provinces');
            
            // Transform to our format
            const formattedProvinces = provinces.map(province => ({
                value: province.name.toLowerCase().replace(/\s+/g, '-'),
                name: province.name,
                capital: province.capital,
                population: province.population
            }));

            // Cache the result
            this.cacheData(cacheKey, formattedProvinces);
            return formattedProvinces;
        } catch (error) {
            console.error('Error fetching provinces:', error);
            return this.getFallbackProvinces();
        }
    }

    // Get districts by province
    async getDistricts(provinceName) {
        const cacheKey = `districts_${provinceName}`;
        
        // Check cache first
        const cached = this.getFromCache(cacheKey);
        if (cached) {
            return cached;
        }

        try {
            const districts = await this.apiCall('/districts', { province: provinceName });
            
            // Transform to our format
            const formattedDistricts = districts.map(district => ({
                value: district.name.toLowerCase().replace(/\s+/g, '-'),
                name: district.name,
                population: district.population,
                province: district.province
            }));

            // Cache the result
            this.cacheData(cacheKey, formattedDistricts);
            return formattedDistricts;
        } catch (error) {
            console.error('Error fetching districts:', error);
            return this.getFallbackDistricts(provinceName);
        }
    }

    // Get sectors by district
    async getSectors(districtName) {
        const cacheKey = `sectors_${districtName}`;
        
        // Check cache first
        const cached = this.getFromCache(cacheKey);
        if (cached) {
            return cached;
        }

        try {
            const sectors = await this.apiCall('/sectors', { district: districtName });
            
            // Transform to our format
            const formattedSectors = sectors.map(sector => ({
                value: sector.name.toLowerCase().replace(/\s+/g, '-'),
                name: sector.name,
                population: sector.population,
                district: sector.district
            }));

            // Cache the result
            this.cacheData(cacheKey, formattedSectors);
            return formattedSectors;
        } catch (error) {
            console.error('Error fetching sectors:', error);
            return this.getFallbackSectors(districtName);
        }
    }

    // Fallback data for provinces
    getFallbackProvinces() {
        return [
            { value: 'kigali-city', name: 'Kigali City', capital: 'Kigali', population: 1350201 },
            { value: 'northern-province', name: 'Northern Province', capital: 'Musanze', population: 2027811 },
            { value: 'southern-province', name: 'Southern Province', capital: 'Nyanza', population: 2684849 },
            { value: 'eastern-province', name: 'Eastern Province', capital: 'Rwamagana', population: 3327396 },
            { value: 'western-province', name: 'Western Province', capital: 'Karongi', population: 2996328 }
        ];
    }

    // Fallback data for districts
    getFallbackDistricts(provinceName) {
        const fallbackData = {
            'Kigali City': [
                { value: 'gasabo', name: 'Gasabo', population: 530918, province: 'Kigali City' },
                { value: 'kicukiro', name: 'Kicukiro', population: 351262, province: 'Kigali City' },
                { value: 'nyarugenge', name: 'Nyarugenge', population: 284739, province: 'Kigali City' }
            ],
            'Northern Province': [
                { value: 'burera', name: 'Burera', population: 439747, province: 'Northern Province' },
                { value: 'gicumbi', name: 'Gicumbi', population: 474399, province: 'Northern Province' },
                { value: 'musanze', name: 'Musanze', population: 369273, province: 'Northern Province' }
            ],
            'Southern Province': [
                { value: 'nyanza', name: 'Nyanza', population: 323719, province: 'Southern Province' },
                { value: 'huye', name: 'Huye', population: 331008, province: 'Southern Province' }
            ],
            'Eastern Province': [
                { value: 'rwamagana', name: 'Rwamagana', population: 313514, province: 'Eastern Province' },
                { value: 'nyagatare', name: 'Nyagatare', population: 466944, province: 'Eastern Province' }
            ],
            'Western Province': [
                { value: 'karongi', name: 'Karongi', population: 332539, province: 'Western Province' },
                { value: 'rubavu', name: 'Rubavu', population: 403662, province: 'Western Province' }
            ]
        };
        
        return fallbackData[provinceName] || [];
    }

    // Fallback data for sectors
    getFallbackSectors(districtName) {
        const fallbackData = {
            'Gasabo': [
                { value: 'gisozi', name: 'Gisozi', population: 107649, district: 'Gasabo' },
                { value: 'kimironko', name: 'Kimironko', population: 89023, district: 'Gasabo' },
                { value: 'bumbogo', name: 'Bumbogo', population: 75432, district: 'Gasabo' },
                { value: 'jali', name: 'Jali', population: 68234, district: 'Gasabo' },
                { value: 'kacyiru', name: 'Kacyiru', population: 85123, district: 'Gasabo' }
            ],
            'Kicukiro': [
                { value: 'gahanga', name: 'Gahanga', population: 98234, district: 'Kicukiro' },
                { value: 'kagarama', name: 'Kagarama', population: 87654, district: 'Kicukiro' },
                { value: 'kicukiro', name: 'Kicukiro', population: 92345, district: 'Kicukiro' }
            ],
            'Nyarugenge': [
                { value: 'nyarugenge', name: 'Nyarugenge', population: 78456, district: 'Nyarugenge' },
                { value: 'kigali', name: 'Kigali', population: 85678, district: 'Nyarugenge' }
            ],
            'Burera': [
                { value: 'bungwe', name: 'Bungwe', population: 65432, district: 'Burera' },
                { value: 'coko', name: 'Coko', population: 54321, district: 'Burera' }
            ],
            'Musanze': [
                { value: 'muhoza', name: 'Muhoza', population: 87654, district: 'Musanze' },
                { value: 'kinigi', name: 'Kinigi', population: 76543, district: 'Musanze' }
            ]
        };
        
        return fallbackData[districtName] || [];
    }

    // Get cells and villages (fallback since API doesn't provide these)
    getCellsAndVillages(districtName, sectorName) {
        const fallbackData = {
            'Gasabo': {
                'Bumbogo': {
                    'kabuye': ['Kabuye', 'Ruhanga', 'Karambo', 'Gasharu', 'Kigarama'],
                    'nyagatare': ['Nyagatare', 'Kagina', 'Gatovu', 'Karehe', 'Kigarama'],
                    'karama': ['Karama', 'Ruhanga', 'Kigarama', 'Gatovu', 'Rugarama']
                },
                'Jali': {
                    'bisenga': ['Bisenga', 'Gakenyeri', 'Gasiza'],
                    'ruhanga': ['Rugende', 'Ruhanga', 'Mirama', 'Nyagacyamo'],
                    'kabuga': ['Kabuga', 'Kalisimbi', 'Amahoro', 'Masango']
                },
                'Kacyiru': {
                    'kamatamu': ['Kabare', 'Nyagacyamu', 'Cyimana', 'Bukinanyana'],
                    'kamutwa': ['Umutekano', 'Gasabo', 'Umuko', 'Kanserege'],
                    'kibaza': ['Nyange', 'Ihuriro', 'Kabagari', 'Ubumwe']
                }
            },
            'Kicukiro': {
                'Gahanga': {
                    'gahanga': ['Gahanga', 'Kinyinya', 'Masaka', 'Nyarugunga'],
                    'kagarama': ['Kagarama', 'Kicukiro', 'Nyarugunga', 'Umusanga']
                },
                'Kagarama': {
                    'kagarama': ['Kagarama', 'Kicukiro', 'Nyarugunga', 'Umusanga'],
                    'nyabugogo': ['Nyabugogo', 'Gikondo', 'Kicukiro']
                }
            },
            'Nyarugenge': {
                'Nyarugenge': {
                    'kigali': ['Rwesero', 'Mwendo', 'Nyabugogo'],
                    'nyarugenge': ['Nyarugenge', 'Ruhanga', 'Kigali']
                }
            }
        };

        const district = fallbackData[districtName];
        if (!district || !district[sectorName]) {
            return { cells: [], villages: {} };
        }

        const cells = Object.keys(district[sectorName]).map(cellName => ({
            value: cellName,
            name: cellName
        }));

        const villages = district[sectorName];

        return { cells, villages };
    }
}

// Initialize the manager
window.rwandaLocationsManager = new RwandaLocationsManager();

// Helper function to populate dropdowns
function populateDropdown(selectElement, options, defaultText = "Select...") {
    selectElement.innerHTML = `<option value="">${defaultText}</option>`;
    options.forEach(option => {
        const optionElement = document.createElement('option');
        optionElement.value = option.value;
        optionElement.textContent = option.name;
        selectElement.appendChild(optionElement);
    });
}

// Initialize address dropdowns
document.addEventListener('DOMContentLoaded', function() {
    console.log('Rwanda Locations API v2 initializing...');
    
    // Get all select elements
    const provinceSelect = document.getElementById('province');
    const districtSelect = document.getElementById('district');
    const sectorSelect = document.getElementById('sector');
    const cellSelect = document.getElementById('cell');
    const villageSelect = document.getElementById('village');
    
    if (!provinceSelect || !districtSelect || !sectorSelect || !cellSelect || !villageSelect) {
        console.log('Address dropdown elements not found');
        return;
    }
    
    console.log('All address elements found');
    
    // Load provinces on page load
    loadProvinces();
    
    // Province change event
    provinceSelect.addEventListener('change', async function() {
        const selectedProvince = this.value;
        const selectedProvinceName = this.options[this.selectedIndex].text;
        
        console.log('Province changed:', { value: selectedProvince, name: selectedProvinceName });
        
        // Reset dependent dropdowns
        resetDropdowns(['district', 'sector', 'cell', 'village']);
        
        if (selectedProvince) {
            districtSelect.disabled = false;
            await loadDistricts(selectedProvinceName);
        }
    });
    
    // District change event
    districtSelect.addEventListener('change', async function() {
        const selectedDistrict = this.value;
        const selectedDistrictName = this.options[this.selectedIndex].text;
        
        console.log('District changed:', { value: selectedDistrict, name: selectedDistrictName });
        
        // Reset dependent dropdowns
        resetDropdowns(['sector', 'cell', 'village']);
        
        if (selectedDistrict) {
            sectorSelect.disabled = false;
            await loadSectors(selectedDistrictName);
        }
    });
    
    // Sector change event
    sectorSelect.addEventListener('change', async function() {
        const selectedSector = this.value;
        const selectedSectorName = this.options[this.selectedIndex].text;
        const selectedDistrictName = districtSelect.options[districtSelect.selectedIndex].text;
        
        console.log('Sector changed:', { value: selectedSector, name: selectedSectorName });
        
        // Reset dependent dropdowns
        resetDropdowns(['cell', 'village']);
        
        if (selectedSector) {
            cellSelect.disabled = false;
            await loadCellsAndVillages(selectedDistrictName, selectedSectorName);
        }
    });
    
    // Cell change event
    cellSelect.addEventListener('change', function() {
        const selectedCell = this.value;
        const selectedCellName = this.options[this.selectedIndex].text;
        const selectedSectorName = sectorSelect.options[sectorSelect.selectedIndex].text;
        const selectedDistrictName = districtSelect.options[districtSelect.selectedIndex].text;
        
        console.log('Cell changed:', { value: selectedCell, name: selectedCellName });
        
        // Reset village dropdown
        villageSelect.innerHTML = '<option value="">Select Village...</option>';
        villageSelect.disabled = true;
        
        if (selectedCell) {
            villageSelect.disabled = false;
            loadVillages(selectedDistrictName, selectedSectorName, selectedCellName);
        }
    });
    
    // Helper functions
    async function loadProvinces() {
        try {
            console.log('Loading provinces...');
            const provinces = await window.rwandaLocationsManager.getProvinces();
            console.log('Provinces loaded:', provinces);
            populateDropdown(provinceSelect, provinces, "Select Province...");
        } catch (error) {
            console.error('Error loading provinces:', error);
        }
    }
    
    async function loadDistricts(provinceName) {
        try {
            console.log('Loading districts for:', provinceName);
            const districts = await window.rwandaLocationsManager.getDistricts(provinceName);
            console.log('Districts loaded:', districts);
            populateDropdown(districtSelect, districts, "Select District...");
        } catch (error) {
            console.error('Error loading districts:', error);
        }
    }
    
    async function loadSectors(districtName) {
        try {
            console.log('Loading sectors for:', districtName);
            const sectors = await window.rwandaLocationsManager.getSectors(districtName);
            console.log('Sectors loaded:', sectors);
            populateDropdown(sectorSelect, sectors, "Select Sector...");
        } catch (error) {
            console.error('Error loading sectors:', error);
        }
    }
    
    async function loadCellsAndVillages(districtName, sectorName) {
        try {
            console.log('Loading cells and villages for:', districtName, sectorName);
            const { cells } = window.rwandaLocationsManager.getCellsAndVillages(districtName, sectorName);
            console.log('Cells loaded:', cells);
            populateDropdown(cellSelect, cells, "Select Cell...");
        } catch (error) {
            console.error('Error loading cells:', error);
        }
    }
    
    function loadVillages(districtName, sectorName, cellName) {
        try {
            console.log('Loading villages for:', districtName, sectorName, cellName);
            const { villages } = window.rwandaLocationsManager.getCellsAndVillages(districtName, sectorName);
            const villageList = villages[cellName] || [];
            console.log('Villages loaded:', villageList);
            
            const villageOptions = villageList.map(village => ({
                value: village,
                name: village
            }));
            
            populateDropdown(villageSelect, villageOptions, "Select Village...");
        } catch (error) {
            console.error('Error loading villages:', error);
        }
    }
    
    function resetDropdowns(dropdowns) {
        dropdowns.forEach(dropdownId => {
            const element = document.getElementById(dropdownId);
            if (element) {
                element.innerHTML = '<option value="">Select...</option>';
                element.disabled = true;
            }
        });
    }
    
    console.log('Rwanda Locations API v2 initialized successfully');
});
