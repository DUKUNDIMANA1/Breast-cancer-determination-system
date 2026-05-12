/**
 * Rwanda Locations API Integration
 * Enhanced address system using RapidAPI Rwanda Locations API
 */

class RwandaLocationsAPI {
    constructor() {
        this.baseURL = 'https://rwanda-locations.p.rapidapi.com';
        this.apiKey = ''; // Will be set from server
        this.cache = new Map();
        this.cacheTimeout = 3600000; // 1 hour in milliseconds
        this.fallbackData = null;
        this.useFallback = false;
    }

    async initialize() {
        try {
            // Get API key from server
            const response = await fetch('/api/rwanda-locations/config');
            const config = await response.json();
            this.apiKey = config.apiKey;
            
            if (!this.apiKey) {
                console.warn('API key not found, using fallback data');
                this.useFallback = true;
                await this.loadFallbackData();
            }
        } catch (error) {
            console.error('Failed to initialize API:', error);
            this.useFallback = true;
            await this.loadFallbackData();
        }
    }

    async loadFallbackData() {
        try {
            const response = await fetch('/static/js/address_data.js');
            const text = await response.text();
            // Extract the addressData object from the JS file
            const match = text.match(/const addressData\s*=\s*({[\s\S]*});/);
            if (match) {
                this.fallbackData = eval('(' + match[1] + ')');
            }
        } catch (error) {
            console.error('Failed to load fallback data:', error);
        }
    }

    getCacheKey(endpoint, params = {}) {
        return `${endpoint}_${JSON.stringify(params)}`;
    }

    getFromCache(cacheKey) {
        const cached = this.cache.get(cacheKey);
        if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
            return cached.data;
        }
        return null;
    }

    setCache(cacheKey, data) {
        this.cache.set(cacheKey, {
            data: data,
            timestamp: Date.now()
        });
    }

    async makeRequest(endpoint, params = {}) {
        if (this.useFallback) {
            return this.getFallbackData(endpoint, params);
        }

        const cacheKey = this.getCacheKey(endpoint, params);
        const cached = this.getFromCache(cacheKey);
        if (cached) {
            return cached;
        }

        try {
            const url = new URL(endpoint, this.baseURL);
            Object.keys(params).forEach(key => {
                if (params[key]) {
                    url.searchParams.append(key, params[key]);
                }
            });

            const response = await fetch(url.toString(), {
                method: 'GET',
                headers: {
                    'X-RapidAPI-Key': this.apiKey,
                    'X-RapidAPI-Host': 'rwanda-locations.p.rapidapi.com',
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`API request failed: ${response.status}`);
            }

            const data = await response.json();
            this.setCache(cacheKey, data);
            return data;

        } catch (error) {
            console.error('API request failed:', error);
            // Fallback to local data if API fails
            this.useFallback = true;
            await this.loadFallbackData();
            return this.getFallbackData(endpoint, params);
        }
    }

    getFallbackData(endpoint, params = {}) {
        if (!this.fallbackData) {
            return { data: [] };
        }

        // Map API endpoints to fallback data structure
        if (endpoint.includes('provinces')) {
            return { data: this.getProvincesFromFallback() };
        } else if (endpoint.includes('districts')) {
            return { data: this.getDistrictsFromFallback(params.province_id) };
        } else if (endpoint.includes('sectors')) {
            return { data: this.getSectorsFromFallback(params.province_id, params.district_id) };
        } else if (endpoint.includes('cells')) {
            return { data: this.getCellsFromFallback(params.province_id, params.district_id, params.sector_id) };
        } else if (endpoint.includes('villages')) {
            return { data: this.getVillagesFromFallback(params.province_id, params.district_id, params.sector_id, params.cell_id) };
        }

        return { data: [] };
    }

    getProvincesFromFallback() {
        if (!this.fallbackData) return [];
        
        return Object.keys(this.fallbackData).map(provinceKey => ({
            id: provinceKey,
            name: provinceKey.replace(/([A-Z])/g, ' $1').trim(),
            code: provinceKey.substring(0, 2).toUpperCase()
        }));
    }

    getDistrictsFromFallback(provinceId) {
        if (!this.fallbackData || !provinceId) return [];
        
        const province = this.fallbackData[provinceId];
        if (!province) return [];

        return Object.keys(province).map(districtKey => ({
            id: districtKey,
            name: districtKey.replace(/([A-Z])/g, ' $1').trim(),
            province_id: provinceId
        }));
    }

    getSectorsFromFallback(provinceId, districtId) {
        if (!this.fallbackData || !provinceId || !districtId) return [];
        
        const province = this.fallbackData[provinceId];
        if (!province) return [];

        const district = province[districtId];
        if (!district) return [];

        return Object.keys(district).map(sectorKey => ({
            id: sectorKey,
            name: sectorKey.replace(/([A-Z])/g, ' $1').trim(),
            district_id: districtId,
            province_id: provinceId
        }));
    }

    getCellsFromFallback(provinceId, districtId, sectorId) {
        if (!this.fallbackData || !provinceId || !districtId || !sectorId) return [];
        
        const province = this.fallbackData[provinceId];
        if (!province) return [];

        const district = province[districtId];
        if (!district) return [];

        const sector = district[sectorId];
        if (!sector) return [];

        return Object.keys(sector).map(cellKey => ({
            id: cellKey,
            name: cellKey.replace(/([A-Z])/g, ' $1').trim(),
            sector_id: sectorId,
            district_id: districtId,
            province_id: provinceId
        }));
    }

    getVillagesFromFallback(provinceId, districtId, sectorId, cellId) {
        if (!this.fallbackData || !provinceId || !districtId || !sectorId || !cellId) return [];
        
        const province = this.fallbackData[provinceId];
        if (!province) return [];

        const district = province[districtId];
        if (!district) return [];

        const sector = district[sectorId];
        if (!sector) return [];

        const cell = sector[cellId];
        if (!cell) return [];

        return cell.map(village => ({
            id: village.id || village.name.toLowerCase().replace(/\s+/g, '_'),
            name: village.name || village,
            cell_id: cellId,
            sector_id: sectorId,
            district_id: districtId,
            province_id: provinceId
        }));
    }

    async getProvinces() {
        const result = await this.makeRequest('/provinces');
        return result.data || [];
    }

    async getDistricts(provinceId) {
        const result = await this.makeRequest('/districts', { province_id: provinceId });
        return result.data || [];
    }

    async getSectors(districtId) {
        const result = await this.makeRequest('/sectors', { district_id: districtId });
        return result.data || [];
    }

    async getCells(sectorId) {
        const result = await this.makeRequest('/cells', { sector_id: sectorId });
        return result.data || [];
    }

    async getVillages(cellId) {
        const result = await this.makeRequest('/villages', { cell_id: cellId });
        return result.data || [];
    }

    async searchLocations(query, level = 'all') {
        const result = await this.makeRequest('/search', { q: query, level: level });
        return result.data || [];
    }

    async getLocationHierarchy() {
        if (this.useFallback && this.fallbackData) {
            return this.fallbackData;
        }

        try {
            const provinces = await this.getProvinces();
            const hierarchy = {};

            for (const province of provinces) {
                hierarchy[province.id] = {
                    ...province,
                    districts: {}
                };

                const districts = await this.getDistricts(province.id);
                for (const district of districts) {
                    hierarchy[province.id].districts[district.id] = {
                        ...district,
                        sectors: {}
                    };

                    const sectors = await this.getSectors(district.id);
                    for (const sector of sectors) {
                        hierarchy[province.id].districts[district.id].sectors[sector.id] = {
                            ...sector,
                            cells: {}
                        };

                        const cells = await this.getCells(sector.id);
                        for (const cell of cells) {
                            hierarchy[province.id].districts[district.id].sectors[sector.id].cells[cell.id] = {
                                ...cell,
                                villages: {}
                            };

                            const villages = await this.getVillages(cell.id);
                            for (const village of villages) {
                                hierarchy[province.id].districts[district.id].sectors[sector.id].cells[cell.id].villages[village.id] = village;
                            }
                        }
                    }
                }
            }

            return hierarchy;
        } catch (error) {
            console.error('Failed to get location hierarchy:', error);
            return this.fallbackData || {};
        }
    }
}

// Enhanced dropdown population functions
class AddressDropdownManager {
    constructor() {
        this.api = new RwandaLocationsAPI();
        this.selectors = {
            province: null,
            district: null,
            sector: null,
            cell: null,
            village: null
        };
        this.currentData = {
            provinces: [],
            districts: [],
            sectors: [],
            cells: [],
            villages: []
        };
    }

    async initialize() {
        await this.api.initialize();
        this.setupSelectors();
        this.setupEventListeners();
        await this.loadProvinces();
    }

    setupSelectors() {
        this.selectors.province = document.getElementById('province');
        this.selectors.district = document.getElementById('district');
        this.selectors.sector = document.getElementById('sector');
        this.selectors.cell = document.getElementById('cell');
        this.selectors.village = document.getElementById('village');
    }

    setupEventListeners() {
        if (this.selectors.province) {
            this.selectors.province.addEventListener('change', () => this.onProvinceChange());
        }
        if (this.selectors.district) {
            this.selectors.district.addEventListener('change', () => this.onDistrictChange());
        }
        if (this.selectors.sector) {
            this.selectors.sector.addEventListener('change', () => this.onSectorChange());
        }
        if (this.selectors.cell) {
            this.selectors.cell.addEventListener('change', () => this.onCellChange());
        }
    }

    async loadProvinces() {
        try {
            const provinces = await this.api.getProvinces();
            this.currentData.provinces = provinces;
            this.populateDropdown(this.selectors.province, provinces, 'id', 'name', 'Select Province...');
        } catch (error) {
            console.error('Failed to load provinces:', error);
        }
    }

    async onProvinceChange() {
        const provinceId = this.selectors.province.value;
        this.resetDependentDropdowns(['district', 'sector', 'cell', 'village']);

        if (provinceId) {
            try {
                const districts = await this.api.getDistricts(provinceId);
                this.currentData.districts = districts;
                this.populateDropdown(this.selectors.district, districts, 'id', 'name', 'Select District...');
                this.selectors.district.disabled = false;
            } catch (error) {
                console.error('Failed to load districts:', error);
            }
        }
    }

    async onDistrictChange() {
        const provinceId = this.selectors.province.value;
        const districtId = this.selectors.district.value;
        this.resetDependentDropdowns(['sector', 'cell', 'village']);

        if (districtId) {
            try {
                const sectors = await this.api.getSectors(districtId);
                this.currentData.sectors = sectors;
                this.populateDropdown(this.selectors.sector, sectors, 'id', 'name', 'Select Sector...');
                this.selectors.sector.disabled = false;
            } catch (error) {
                console.error('Failed to load sectors:', error);
            }
        }
    }

    async onSectorChange() {
        const districtId = this.selectors.district.value;
        const sectorId = this.selectors.sector.value;
        this.resetDependentDropdowns(['cell', 'village']);

        if (sectorId) {
            try {
                const cells = await this.api.getCells(sectorId);
                this.currentData.cells = cells;
                this.populateDropdown(this.selectors.cell, cells, 'id', 'name', 'Select Cell...');
                this.selectors.cell.disabled = false;
            } catch (error) {
                console.error('Failed to load cells:', error);
            }
        }
    }

    async onCellChange() {
        const sectorId = this.selectors.sector.value;
        const cellId = this.selectors.cell.value;
        this.resetDependentDropdowns(['village']);

        if (cellId) {
            try {
                const villages = await this.api.getVillages(cellId);
                this.currentData.villages = villages;
                this.populateDropdown(this.selectors.village, villages, 'id', 'name', 'Select Village...');
                this.selectors.village.disabled = false;
            } catch (error) {
                console.error('Failed to load villages:', error);
            }
        }
    }

    resetDependentDropdowns(dropdowns) {
        dropdowns.forEach(name => {
            const select = this.selectors[name];
            if (select) {
                select.innerHTML = `<option value="">Select ${name.charAt(0).toUpperCase() + name.slice(1)}...</option>`;
                select.disabled = true;
            }
        });
    }

    populateDropdown(selectElement, data, valueField, textField, placeholder) {
        if (!selectElement) return;

        selectElement.innerHTML = `<option value="">${placeholder}</option>`;
        
        data.forEach(item => {
            const option = document.createElement('option');
            option.value = item[valueField];
            option.textContent = item[textField];
            selectElement.appendChild(option);
        });
    }

    // Method to set existing values (for edit forms)
    async setExistingValues(values) {
        if (values.province) {
            this.selectors.province.value = values.province;
            await this.onProvinceChange();
            
            if (values.district) {
                this.selectors.district.value = values.district;
                await this.onDistrictChange();
                
                if (values.sector) {
                    this.selectors.sector.value = values.sector;
                    await this.onSectorChange();
                    
                    if (values.cell) {
                        this.selectors.cell.value = values.cell;
                        await this.onCellChange();
                        
                        if (values.village) {
                            this.selectors.village.value = values.village;
                        }
                    }
                }
            }
        }
    }
}

// Initialize the address dropdown manager when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('province')) {
        window.addressManager = new AddressDropdownManager();
        window.addressManager.initialize();
    }
});

// Export for use in other scripts
window.RwandaLocationsAPI = RwandaLocationsAPI;
window.AddressDropdownManager = AddressDropdownManager;
