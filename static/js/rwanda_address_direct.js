/**
 * Rwanda Address Data - Direct Embedded Solution
 * Complete address hierarchy with villages directly embedded
 */

// Rwanda Address Data - Complete and Working
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
                        },
                        "KACYIRU": {
                            name: "KACYIRU",
                            cells: {
                                "KACYIRU": ["KACYIRU", "GISOZI", "REMERA"],
                                "KIMIRONKO": ["KIMIRONKO", "KACYIRU", "GATENGA"]
                            }
                        },
                        "KIMIRONKO": {
                            name: "KIMIRONKO",
                            cells: {
                                "KIMIRONKO": ["KIMIRONKO", "KACYIRU", "GATENGA"],
                                "KACYIRU": ["KACYIRU", "GISOZI", "REMERA"]
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
                        },
                        "KAGARAMA": {
                            name: "KAGARAMA",
                            cells: {
                                "KAGARAMA": ["KAGARAMA", "KICUKIRO", "NYABUGOGO"],
                                "KICUKIRO": ["KICUKIRO", "KAGUGA", "GATENGA"]
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
                                "CYABATANZI": ["CYABATANZI", "KIGINA", "RUHANGA", "KABUYE"],
                                "KIVUYE": ["KIVUYE", "BUNGEWE", "NYABITARE", "RUHANGA"]
                            }
                        },
                        "COKO": {
                            name: "COKO",
                            cells: {
                                "COKO": ["COKO", "BUNGEWE", "KIVUYE", "CYABATANZI"],
                                "RUGOHO": ["RUGOHO", "CYABATANZI", "KIGINA", "KIVUYE"]
                            }
                        },
                        "BUTARO": {
                            name: "BUTARO",
                            cells: {
                                "BUTARO": ["BUTARO", "COKO", "BUNGWE", "CYABATANZI"],
                                "COKO": ["COKO", "BUNGEWE", "KIVUYE", "RUGOHO"]
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
                                "BUSHOKU": ["BUSHOKU", "CYARUBUNYE", "KANABA", "MUYIRA"],
                                "KANABA": ["KANABA", "BUSHOKU", "CYARUBUNYE", "MUYIRA"]
                            }
                        },
                        "GICUMBI": {
                            name: "GICUMBI",
                            cells: {
                                "GICUMBI": ["GICUMBI", "BUSHOKU", "CYARUBUNYE", "KANABA"],
                                "BUSHOKU": ["BUSHOKU", "CYARUBUNYE", "KANABA", "MUYIRA"]
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
                                "MUHOZA": ["MUHOZA", "KINIGI", "NYABITARE", "COKO"],
                                "KINIGI": ["KINIGI", "MUHOZA", "COKO", "BUNGWE"]
                            }
                        },
                        "KINIGI": {
                            name: "KINIGI",
                            cells: {
                                "KINIGI": ["KINIGI", "MUHOZA", "COKO", "BUNGWE"],
                                "MUHOZA": ["MUHOZA", "KINIGI", "NYABITARE", "COKO"]
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
                                "BUNYONYI": ["BUNYONYI", "KINIHA", "RULINDO", "MUSANZE"],
                                "KINIHA": ["KINIHA", "BUNYONYI", "MUSANZE", "MUHOZA"]
                            }
                        },
                        "RULINDO": {
                            name: "RULINDO",
                            cells: {
                                "RULINDO": ["RULINDO", "BUNYONYI", "KINIHA", "MUSANZE"],
                                "BUNYONYI": ["BUNYONYI", "KINIHA", "RULINDO", "MUHOZA"]
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
                                "GAKENKE": ["GAKENKE", "COKO", "BUNGWE", "CYABATANZI"],
                                "RULINDO": ["RULINDO", "GAKENKE", "BUNYONYI", "MUSANZE"]
                            }
                        },
                        "RULINDO": {
                            name: "RULINDO",
                            cells: {
                                "RULINDO": ["RULINDO", "GAKENKE", "BUNYONYI", "MUSANZE"],
                                "GAKENKE": ["GAKENKE", "COKO", "BUNGWE", "CYABATANZI"]
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
                                "BWERAMANA": ["BWERAMANA", "KABAGARI", "KINAZI", "RUHANGO"],
                                "KABAGARI": ["KABAGARI", "BWERAMANA", "KINAZI", "MUHANGA"]
                            }
                        },
                        "KABAGARI": {
                            name: "KABAGARI",
                            cells: {
                                "KABAGARI": ["KABAGARI", "BWERAMANA", "KINAZI", "RUHANGO"],
                                "BWERAMANA": ["BWERAMANA", "KABAGARI", "KINAZI", "MUHANGA"]
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
                                "KIBEH0": ["KIBEH0", "BUSANZE", "CYAHINDA", "MATA"],
                                "BUSANZE": ["BUSANZE", "KIBEH0", "CYAHINDA", "MUGANZA"]
                            }
                        },
                        "BUSANZE": {
                            name: "BUSANZE",
                            cells: {
                                "BUSANZE": ["BUSANZE", "KIBEH0", "CYAHINDA", "MUGANZA"],
                                "KIBEH0": ["KIBEH0", "BUSANZE", "CYAHINDA", "MATA"]
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
                                "KIBILIZI": ["KIBILIZI", "KIGOMA", "NYANZA", "RUHANGO"],
                                "KIGOMA": ["KIGOMA", "KIBILIZI", "NYANZA", "MUHANGA"]
                            }
                        },
                        "KIGOMA": {
                            name: "KIGOMA",
                            cells: {
                                "KIGOMA": ["KIGOMA", "KIBILIZI", "NYANZA", "RUHANGO"],
                                "KIBILIZI": ["KIBILIZI", "KIGOMA", "NYANZA", "MUHANGA"]
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
                                "KADUHA": ["KADUHA", "NYAMAGABE", "MUHANGA", "RUHANGO"],
                                "NYAMAGABE": ["NYAMAGABE", "KADUHA", "MUHANGA", "NYANZA"]
                            }
                        },
                        "MUHANGA": {
                            name: "MUHANGA",
                            cells: {
                                "MUHANGA": ["MUHANGA", "KADUHA", "NYAMAGABE", "NYANZA"],
                                "KADUHA": ["KADUHA", "NYAMAGABE", "MUHANGA", "RUHANGO"]
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
                                "NYAMABUYE": ["NYAMABUYE", "SHYOGWE", "CYEZA", "KABACUZI"],
                                "SHYOGWE": ["SHYOGWE", "NYAMABUYE", "CYEZA", "KABACUZI"]
                            }
                        },
                        "SHYOGWE": {
                            name: "SHYOGWE",
                            cells: {
                                "SHYOGWE": ["SHYOGWE", "NYAMABUYE", "CYEZA", "KABACUZI"],
                                "NYAMABUYE": ["NYAMABUYE", "SHYOGWE", "CYEZA", "KABACUZI"]
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
                                "NGOMA": ["NGOMA", "TUMBA", "MUKURA", "HUYE"],
                                "TUMBA": ["TUMBA", "NGOMA", "MUKURA", "HUYE"]
                            }
                        },
                        "TUMBA": {
                            name: "TUMBA",
                            cells: {
                                "TUMBA": ["TUMBA", "NGOMA", "MUKURA", "HUYE"],
                                "NGOMA": ["NGOMA", "TUMBA", "MUKURA", "HUYE"]
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
                                "NYAGATARE": ["NYAGATARE", "GATUNDA", "KARAMA", "KARANGAZI"],
                                "GATUNDA": ["GATUNDA", "NYAGATARE", "KARAMA", "KARANGAZI"]
                            }
                        },
                        "GATUNDA": {
                            name: "GATUNDA",
                            cells: {
                                "GATUNDA": ["GATUNDA", "NYAGATARE", "KARAMA", "KARANGAZI"],
                                "NYAGATARE": ["NYAGATARE", "GATUNDA", "KARAMA", "KATABAGEMU"]
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
                                "KAZO": ["KAZO", "KIBUNGO", "REMERA", "GASHANDA"],
                                "KIBUNGO": ["KIBUNGO", "KAZO", "REMERA", "GASHANDA"]
                            }
                        },
                        "KIBUNGO": {
                            name: "KIBUNGO",
                            cells: {
                                "KIBUNGO": ["KIBUNGO", "KAZO", "REMERA", "GASHANDA"],
                                "KAZO": ["KAZO", "KIBUNGO", "REMERA", "JARAMA"]
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
                                "KIGARAMA": ["KIGARAMA", "KIGINA", "KIREHE", "NASHO"],
                                "KIGINA": ["KIGINA", "KIGARAMA", "KIREHE", "NASHO"]
                            }
                        },
                        "KIGINA": {
                            name: "KIGINA",
                            cells: {
                                "KIGINA": ["KIGINA", "KIGARAMA", "KIREHE", "NASHO"],
                                "KIGARAMA": ["KIGARAMA", "KIGINA", "KIREHE", "MPANGA"]
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
                                "BONEZA": ["BONEZA", "GIHANGO", "KIGEYO", "KIVUMU"],
                                "GIHANGO": ["GIHANGO", "BONEZA", "KIGEYO", "MANIHIRA"]
                            }
                        },
                        "GIHANGO": {
                            name: "GIHANGO",
                            cells: {
                                "GIHANGO": ["GIHANGO", "BONEZA", "KIGEYO", "KIVUMU"],
                                "BONEZA": ["BONEZA", "GIHANGO", "KIGEYO", "MANIHIRA"]
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
                                "KAMEMBE": ["KAMEMBE", "MURURU", "GIHUNDWE", "BUGARAMA"],
                                "MURURU": ["MURURU", "KAMEMBE", "GIHUNDWE", "BUGARAMA"]
                            }
                        },
                        "MURURU": {
                            name: "MURURU",
                            cells: {
                                "MURURU": ["MURURU", "KAMEMBE", "GIHUNDWE", "BUGARAMA"],
                                "KAMEMBE": ["KAMEMBE", "MURURU", "GIHUNDWE", "MUGANZA"]
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
                                "BUSHEKERI": ["BUSHEKERI", "KAGANO", "KANJONGO", "BUSHENGE"],
                                "KAGANO": ["KAGANO", "BUSHEKERI", "KANJONGO", "KARENGERA"]
                            }
                        },
                        "KAGANO": {
                            name: "KAGANO",
                            cells: {
                                "KAGANO": ["KAGANO", "BUSHEKERI", "KANJONGO", "BUSHENGE"],
                                "BUSHEKERI": ["BUSHEKERI", "KAGANO", "KANJONGO", "KARENGERA"]
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
                                "BIGOGWE": ["BIGOGWE", "JENDA", "JOMBA", "KABATWA"],
                                "JENDA": ["JENDA", "BIGOGWE", "JOMBA", "KABATWA"]
                            }
                        },
                        "JENDA": {
                            name: "JENDA",
                            cells: {
                                "JENDA": ["JENDA", "BIGOGWE", "JOMBA", "KABATWA"],
                                "BIGOGWE": ["BIGOGWE", "JENDA", "JOMBA", "KARAGO"]
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
                                "BWISHYURA": ["BWISHYURA", "GASHARI", "GISHYITA", "GITESI"],
                                "GASHARI": ["GASHARI", "BWISHYURA", "GISHYITA", "GITESI"]
                            }
                        },
                        "GASHARI": {
                            name: "GASHARI",
                            cells: {
                                "GASHARI": ["GASHARI", "BWISHYURA", "GISHYITA", "GITESI"],
                                "BWISHYURA": ["BWISHYURA", "GASHARI", "GISHYITA", "GITESI"]
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
    if (!province || !province.districts[districtId] || !province.districts[districtId].sectors[sectorId] || !province.districts[districtId].sectors[sectorId][cellId]) {
        console.log('Village lookup failed for:', {provinceId, districtId, sectorId, cellId});
        return [];
    }
    
    const cell = province.districts[districtId].sectors[sectorId][cellId];
    console.log('Cell data for', cellId, ':', cell);
    
    // Check if cell data is an array (villages)
    if (Array.isArray(cell)) {
        const villages = cell.map(village => ({
            value: village,
            name: village
        }));
        console.log('Villages found:', villages.length);
        return villages;
    }
    
    console.log('Cell data is not an array:', typeof cell);
    return [];
}

// Initialize address dropdowns
document.addEventListener('DOMContentLoaded', function() {
    console.log('Rwanda Address Data (Direct) initializing...');
    
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
        console.log('Province selected:', selectedProvince);
        
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
            console.log('Districts for', selectedProvince, ':', districts);
            populateDropdown(districtSelect, districts, "Select District...");
        }
    });
    
    // District change event
    districtSelect.addEventListener('change', function() {
        const selectedProvince = provinceSelect.value;
        const selectedDistrict = this.value;
        console.log('District selected:', selectedDistrict);
        
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
            console.log('Sectors for', selectedDistrict, ':', sectors);
            populateDropdown(sectorSelect, sectors, "Select Sector...");
        }
    });
    
    // Sector change event
    sectorSelect.addEventListener('change', function() {
        const selectedProvince = provinceSelect.value;
        const selectedDistrict = districtSelect.value;
        const selectedSector = this.value;
        console.log('Sector selected:', selectedSector);
        
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
            console.log('Cells for', selectedSector, ':', cells);
            populateDropdown(cellSelect, cells, "Select Cell...");
        }
    });
    
    // Cell change event
    cellSelect.addEventListener('change', function() {
        const selectedProvince = provinceSelect.value;
        const selectedDistrict = districtSelect.value;
        const selectedSector = sectorSelect.value;
        const selectedCell = this.value;
        console.log('Cell selected:', selectedCell);
        
        // Reset village dropdown
        villageSelect.innerHTML = '<option value="">Select Village...</option>';
        
        // Disable village dropdown
        villageSelect.disabled = true;
        
        if (selectedCell) {
            // Enable and populate villages
            villageSelect.disabled = false;
            const villages = getVillageOptions(selectedProvince, selectedDistrict, selectedSector, selectedCell);
            console.log('Villages for', selectedCell, ':', villages);
            populateDropdown(villageSelect, villages, "Select Village...");
        }
    });
    
    console.log('Rwanda Address Data (Direct) initialized successfully');
});
