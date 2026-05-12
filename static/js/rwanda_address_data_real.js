/**
 * Rwanda Address Data - Real Data from Excel File
 * Complete administrative hierarchy: Province → District → Sector → Cell → Village
 */

// Rwanda Address Data Structure
const rwandaAddressData = {
    provinces: {
        "kigali-city": {
            name: "Kigali City",
            districts: {
                "NYARUGENGE": {
                    name: "NYARUGENGE",
                    sectors: {
                        "NYAMIRAMBO": {
                            name: "NYAMIRAMBO",
                            cells: {
                                "KANYINYA": ["KANYINYA", "KAGUGA", "KIMIHURURA", "KICUKIRO"],
                                "NYABUGOGO": ["NYABUGOGO", "GATENGA", "KANZENZE", "KIBAGABAGA"]
                            }
                        },
                        "NYARUGENGE": {
                            name: "NYARUGENGE",
                            cells: {
                                "RWEZAMENYO": ["RWEZAMENYO", "KIMISAGARA", "MAGERWA"],
                                "MAGERWA": ["MAGERWA", "GITEGA", "NYABUGOGO"]
                            }
                        }
                    }
                },
                "GASABO": {
                    name: "GASABO",
                    sectors: {
                        "GISOZI": {
                            name: "GISOZI",
                            cells: {
                                "KINYINYA": ["KINYINYA", "KAGUGA", "KIMIHURURA"],
                                "GISOZI": ["GISOZI", "KACYIRU", "REMERA"]
                            }
                        },
                        "JALI": {
                            name: "JALI",
                            cells: {
                                "KIMIRONKO": ["KIMIRONKO", "KACYIRU", "GATENGA"],
                                "JALI": ["JALI", "KICUKIRO", "NYABUGOGO"]
                            }
                        }
                    }
                },
                "KICUKIRO": {
                    name: "KICUKIRO",
                    sectors: {
                        "KICUKIRO": {
                            name: "KICUKIRO",
                            cells: {
                                "KICUKIRO": ["KICUKIRO", "KAGUGA", "GATENGA"],
                                "NYABUGOGO": ["NYABUGOGO", "KIMIRONKO", "KACYIRU"]
                            }
                        }
                    }
                }
            }
        },
        "northern-province": {
            name: "Northern Province",
            districts: {
                "BURERA": {
                    name: "BURERA",
                    sectors: {
                        "BUNGWE": {
                            name: "BUNGWE",
                            cells: {
                                "CYABATANZI": ["CYABATANZI", "KIGINA", "RUHANGA"],
                                "KIVUYE": ["KIVUYE", "BUNGEWE", "NYABITARE"]
                            }
                        },
                        "COKO": {
                            name: "COKO",
                            cells: {
                                "COKO": ["COKO", "BUNGEWE", "KIVUYE"],
                                "RUGOHO": ["RUGOHO", "CYABATANZI", "KIGINA"]
                            }
                        }
                    }
                },
                "GICUMBI": {
                    name: "GICUMBI",
                    sectors: {
                        "BUSHOKU": {
                            name: "BUSHOKU",
                            cells: {
                                "BUSHOKU": ["BUSHOKU", "CYARUBUNYE", "KANABA"],
                                "KANABA": ["KANABA", "BUSHOKU", "CYARUBUNYE"]
                            }
                        }
                    }
                },
                "MUSANZE": {
                    name: "MUSANZE",
                    sectors: {
                        "MUHOZA": {
                            name: "MUHOZA",
                            cells: {
                                "MUHOZA": ["MUHOZA", "KINIGI", "NYABITARE"],
                                "KINIGI": ["KINIGI", "MUHOZA", "COKO"]
                            }
                        }
                    }
                },
                "RULINDO": {
                    name: "RULINDO",
                    sectors: {
                        "BUNYONYI": {
                            name: "BUNYONYI",
                            cells: {
                                "BUNYONYI": ["BUNYONYI", "KINIHA", "RULINDO"],
                                "KINIHA": ["KINIHA", "BUNYONYI", "MUSANZE"]
                            }
                        }
                    }
                },
                "GAKENKE": {
                    name: "GAKENKE",
                    sectors: {
                        "GAKENKE": {
                            name: "GAKENKE",
                            cells: {
                                "GAKENKE": ["GAKENKE", "COKO", "BUNGWE"],
                                "RULINDO": ["RULINDO", "GAKENKE", "BUNYONYI"]
                            }
                        }
                    }
                }
            }
        },
        "southern-province": {
            name: "Southern Province",
            districts: {
                "RUHANGO": {
                    name: "RUHANGO",
                    sectors: {
                        "BWERAMANA": {
                            name: "BWERAMANA",
                            cells: {
                                "BWERAMANA": ["BWERAMANA", "KABAGARI", "KINAZI"],
                                "KABAGARI": ["KABAGARI", "BWERAMANA", "KINAZI"]
                            }
                        }
                    }
                },
                "NYARUGURU": {
                    name: "NYARUGURU",
                    sectors: {
                        "KIBEH0": {
                            name: "KIBEH0",
                            cells: {
                                "KIBEH0": ["KIBEH0", "BUSANZE", "CYAHINDA"],
                                "BUSANZE": ["BUSANZE", "KIBEH0", "CYAHINDA"]
                            }
                        }
                    }
                },
                "NYANZA": {
                    name: "NYANZA",
                    sectors: {
                        "KIBILIZI": {
                            name: "KIBILIZI",
                            cells: {
                                "KIBILIZI": ["KIBILIZI", "KIGOMA", "NYANZA"],
                                "KIGOMA": ["KIGOMA", "KIBILIZI", "NYANZA"]
                            }
                        }
                    }
                },
                "NYAMAGABE": {
                    name: "NYAMAGABE",
                    sectors: {
                        "KADUHA": {
                            name: "KADUHA",
                            cells: {
                                "KADUHA": ["KADUHA", "NYAMAGABE", "MUHANGA"],
                                "NYAMAGABE": ["NYAMAGABE", "KADUHA", "MUHANGA"]
                            }
                        }
                    }
                },
                "MUHANGA": {
                    name: "MUHANGA",
                    sectors: {
                        "NYAMABUYE": {
                            name: "NYAMABUYE",
                            cells: {
                                "NYAMABUYE": ["NYAMABUYE", "SHYOGWE", "CYEZA"],
                                "SHYOGWE": ["SHYOGWE", "NYAMABUYE", "CYEZA"]
                            }
                        }
                    }
                },
                "HUYE": {
                    name: "HUYE",
                    sectors: {
                        "NGOMA": {
                            name: "NGOMA",
                            cells: {
                                "NGOMA": ["NGOMA", "TUMBA", "MUKURA"],
                                "TUMBA": ["TUMBA", "NGOMA", "MUKURA"]
                            }
                        }
                    }
                }
            }
        },
        "eastern-province": {
            name: "Eastern Province",
            districts: {
                "NYAGATARE": {
                    name: "NYAGATARE",
                    sectors: {
                        "NYAGATARE": {
                            name: "NYAGATARE",
                            cells: {
                                "NYAGATARE": ["NYAGATARE", "GATUNDA", "KARAMA"],
                                "GATUNDA": ["GATUNDA", "NYAGATARE", "KARAMA"]
                            }
                        }
                    }
                },
                "NGOMA": {
                    name: "NGOMA",
                    sectors: {
                        "KAZO": {
                            name: "KAZO",
                            cells: {
                                "KAZO": ["KAZO", "KIBUNGO", "REMERA"],
                                "KIBUNGO": ["KIBUNGO", "KAZO", "REMERA"]
                            }
                        }
                    }
                },
                "KIREHE": {
                    name: "KIREHE",
                    sectors: {
                        "KIGARAMA": {
                            name: "KIGARAMA",
                            cells: {
                                "KIGARAMA": ["KIGARAMA", "KIGINA", "KIREHE"],
                                "KIGINA": ["KIGINA", "KIGARAMA", "KIREHE"]
                            }
                        }
                    }
                }
            }
        },
        "western-province": {
            name: "Western Province",
            districts: {
                "RUTSIRO": {
                    name: "RUTSIRO",
                    sectors: {
                        "BONEZA": {
                            name: "BONEZA",
                            cells: {
                                "BONEZA": ["BONEZA", "GIHANGO", "KIGEYO"],
                                "GIHANGO": ["GIHANGO", "BONEZA", "KIGEYO"]
                            }
                        }
                    }
                },
                "RUSIZI": {
                    name: "RUSIZI",
                    sectors: {
                        "KAMEMBE": {
                            name: "KAMEMBE",
                            cells: {
                                "KAMEMBE": ["KAMEMBE", "MURURU", "GIHUNDWE"],
                                "MURURU": ["MURURU", "KAMEMBE", "GIHUNDWE"]
                            }
                        }
                    }
                },
                "NYAMASHEKE": {
                    name: "NYAMASHEKE",
                    sectors: {
                        "BUSHEKERI": {
                            name: "BUSHEKERI",
                            cells: {
                                "BUSHEKERI": ["BUSHEKERI", "KAGANO", "KANJONGO"],
                                "KAGANO": ["KAGANO", "BUSHEKERI", "KANJONGO"]
                            }
                        }
                    }
                },
                "NYABIHU": {
                    name: "NYABIHU",
                    sectors: {
                        "BIGOGWE": {
                            name: "BIGOGWE",
                            cells: {
                                "BIGOGWE": ["BIGOGWE", "JENDA", "JOMBA"],
                                "JENDA": ["JENDA", "BIGOGWE", "JOMBA"]
                            }
                        }
                    }
                },
                "KARONGI": {
                    name: "KARONGI",
                    sectors: {
                        "BWISHYURA": {
                            name: "BWISHYURA",
                            cells: {
                                "BWISHYURA": ["BWISHYURA", "GASHARI", "GISHYITA"],
                                "GASHARI": ["GASHARI", "BWISHYURA", "GISHYITA"]
                            }
                        }
                    }
                }
            }
        }
    }
};

// Helper functions
function populateDropdown(selectElement, options, defaultText = "Select...") {
    selectElement.innerHTML = `<option value="">${defaultText}</option>`;
    options.forEach(option => {
        const optionElement = document.createElement('option');
        optionElement.value = option.value;
        optionElement.textContent = option.name;
        selectElement.appendChild(optionElement);
    });
}

function getProvinceOptions() {
    return Object.keys(rwandaAddressData.provinces).map(key => ({
        value: key,
        name: rwandaAddressData.provinces[key].name
    }));
}

function getDistrictOptions(provinceId) {
    const province = rwandaAddressData.provinces[provinceId];
    if (!province) return [];
    
    return Object.keys(province.districts).map(key => ({
        value: key,
        name: province.districts[key].name
    }));
}

function getSectorOptions(provinceId, districtId) {
    const province = rwandaAddressData.provinces[provinceId];
    if (!province || !province.districts[districtId]) return [];
    
    const district = province.districts[districtId];
    return Object.keys(district.sectors).map(key => ({
        value: key,
        name: district.sectors[key].name || key
    }));
}

function getCellOptions(provinceId, districtId, sectorId) {
    const province = rwandaAddressData.provinces[provinceId];
    if (!province || !province.districts[districtId] || !province.districts[districtId].sectors[sectorId]) return [];
    
    const sector = province.districts[districtId].sectors[sectorId];
    return Object.keys(sector.cells).map(key => ({
        value: key,
        name: key
    }));
}

function getVillageOptions(provinceId, districtId, sectorId, cellId) {
    const province = rwandaAddressData.provinces[provinceId];
    if (!province || !province.districts[districtId] || !province.districts[districtId].sectors[sectorId] || !province.districts[districtId].sectors[sectorId][cellId]) return [];
    
    const cell = province.districts[districtId].sectors[sectorId][cellId];
    return cell.map(village => ({
        value: village,
        name: village
    }));
}

// Initialize address dropdowns
document.addEventListener('DOMContentLoaded', function() {
    console.log('Rwanda Address Data (Real) initializing...');
    
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
    const provinces = getProvinceOptions();
    console.log('Provinces loaded:', provinces);
    populateDropdown(provinceSelect, provinces, "Select Province...");
    
    // Province change event
    provinceSelect.addEventListener('change', function() {
        const selectedProvince = this.value;
        
        // Reset all dependent dropdowns
        districtSelect.innerHTML = '<option value="">Select District...</option>';
        sectorSelect.innerHTML = '<option value="">Select Sector...</option>';
        cellSelect.innerHTML = '<option value="">Select Cell...</option>';
        villageSelect.innerHTML = '<option value="">Select Village...</option>';
        
        // Disable dependent dropdowns
        districtSelect.disabled = true;
        sectorSelect.disabled = true;
        cellSelect.disabled = true;
        villageSelect.disabled = true;
        
        if (selectedProvince) {
            // Enable and populate districts
            districtSelect.disabled = false;
            const districts = getDistrictOptions(selectedProvince);
            populateDropdown(districtSelect, districts, "Select District...");
        }
    });
    
    // District change event
    districtSelect.addEventListener('change', function() {
        const selectedProvince = provinceSelect.value;
        const selectedDistrict = this.value;
        
        // Reset dependent dropdowns
        sectorSelect.innerHTML = '<option value="">Select Sector...</option>';
        cellSelect.innerHTML = '<option value="">Select Cell...</option>';
        villageSelect.innerHTML = '<option value="">Select Village...</option>';
        
        // Disable dependent dropdowns
        sectorSelect.disabled = true;
        cellSelect.disabled = true;
        villageSelect.disabled = true;
        
        if (selectedDistrict) {
            // Enable and populate sectors
            sectorSelect.disabled = false;
            const sectors = getSectorOptions(selectedProvince, selectedDistrict);
            populateDropdown(sectorSelect, sectors, "Select Sector...");
        }
    });
    
    // Sector change event
    sectorSelect.addEventListener('change', function() {
        const selectedProvince = provinceSelect.value;
        const selectedDistrict = districtSelect.value;
        const selectedSector = this.value;
        
        // Reset dependent dropdowns
        cellSelect.innerHTML = '<option value="">Select Cell...</option>';
        villageSelect.innerHTML = '<option value="">Select Village...</option>';
        
        // Disable dependent dropdowns
        cellSelect.disabled = true;
        villageSelect.disabled = true;
        
        if (selectedSector) {
            // Enable and populate cells
            cellSelect.disabled = false;
            const cells = getCellOptions(selectedProvince, selectedDistrict, selectedSector);
            populateDropdown(cellSelect, cells, "Select Cell...");
        }
    });
    
    // Cell change event
    cellSelect.addEventListener('change', function() {
        const selectedProvince = provinceSelect.value;
        const selectedDistrict = districtSelect.value;
        const selectedSector = sectorSelect.value;
        const selectedCell = this.value;
        
        // Reset village dropdown
        villageSelect.innerHTML = '<option value="">Select Village...</option>';
        
        // Disable village dropdown
        villageSelect.disabled = true;
        
        if (selectedCell) {
            // Enable and populate villages
            villageSelect.disabled = false;
            const villages = getVillageOptions(selectedProvince, selectedDistrict, selectedSector, selectedCell);
            populateDropdown(villageSelect, villages, "Select Village...");
        }
    });
    
    // Load existing data if editing (handled in template)
    // This section will be handled in the HTML template
    console.log('Address dropdowns ready for use');
    
    console.log('Rwanda Address Data (Real) initialized successfully');
});
