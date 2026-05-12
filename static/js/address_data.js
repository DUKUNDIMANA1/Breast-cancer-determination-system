// Rwanda Administrative Data Structure
const rwandaAddressData = {
    provinces: {
        "kigali": {
            name: "City of Kigali",
            districts: {
                "gasabo": {
                    name: "Gasabo",
                    sectors: {
                        "bumbogo": {
                            name: "Bumbogo",
                            cells: {
                                "kabuye": ["Kabuye", "Ruhanga", "Karambo", "Gasharu", "Kigarama"],
                                "nyagatare": ["Nyagatare", "Kagina", "Gatovu", "Karehe", "Kigarama"],
                                "karama": ["Karama", "Ruhanga", "Kigarama", "Gatovu", "Rugarama"]
                            }
                        },
                        "gatsata": {
                            name: "Gatsata",
                            cells: {
                                "karuruma": ["Karuruma", "Akamamana", "Busasamana", "Muremera", "Bigega"],
                                "nyamabuye": ["Mpakabavu", "Kibaya", "Runyonza", "Musango", "Haniika"],
                                "nyamugali": ["Akarubimbura", "Nyakariba", "Akamwunguzi", "Kanyonyomba"]
                            }
                        },
                        "jali": {
                            name: "Jali",
                            cells: {
                                "bisenga": ["Bisenga", "Gakenyeri", "Gasiza"],
                                "ruhanga": ["Rugende", "Ruhanga", "Mirama", "Nyagacyamo"],
                                "kabuga": ["Kabuga", "Kalisimbi", "Amahoro", "Masango"]
                            }
                        },
                        "kacyiru": {
                            name: "Kacyiru",
                            cells: {
                                "kamatamu": ["Kabare", "Nyagacyamu", "Cyimana", "Bukinanyana"],
                                "kamutwa": ["Umutekano", "Gasabo", "Umuko", "Kanserege"],
                                "kibaza": ["Nyange", "Ihuriro", "Kabagari", "Ubumwe"]
                            }
                        },
                        "kimironko": {
                            name: "Kimironko",
                            cells: {
                                "gasaza": ["Gasaza", "Kigufi", "Karuruma", "Rwampara"],
                                "gasura": ["Kigufi", "Kazi", "Gikombe", "Gashinya"],
                                "gatunga": ["Karama", "Nyange", "Burungero", "Agasharu"]
                            }
                        },
                        "kigali": {
                            name: "Kigali",
                            cells: {
                                "rwesero": ["Musimba", "Muruhogo", "Rwesero", "Kukimana"],
                                "mwendo": ["Cyarumanzi", "Amajyambe", "Utubungo", "Isangano"],
                                "nyabugogo": ["Nyabikoni", "Kiruhura", "Ibuyerihets", "Giticyinyoni"]
                            }
                        },
                        "kinyinya": {
                            name: "Kinyinya",
                            cells: {
                                "kagugu": ["Kadobogo", "Kabuhunde", "Gicikiza", "Rukingu"],
                                "gacuriro": ["Urubanda", "Bishikiri", "Cyeru", "Akanyamugabo"],
                                "gasharu": ["Gasharu", "Agatare", "Kami", "Rwankuba"]
                            }
                        },
                        "nduba": {
                            name: "Nduba",
                            cells: {
                                "shango": ["Ndandoye", "Akazi", "Kaduha", "Nyamigina"],
                                "gasura": ["Kigufi", "Kazi", "Gikombe", "Gashinya"],
                                "gatunga": ["Karama", "Nyange", "Burungero", "Agasharu"]
                            }
                        },
                        "remera": {
                            name: "Remera",
                            cells: {
                                "nyarutarama": ["Gishushu", "Kamahwa", "Nyarutarama", "Juru"],
                                "rukiri": ["Zuba", "Rumuri", "Kwezi", "Ubumwe"],
                                "nyabisindu": ["Kinunga", "Rugarama", "Gihogere", "Kagara"]
                            }
                        },
                        "rusororo": {
                            name: "Rusororo",
                            cells: {
                                "bisenga": ["Bisenga", "Gakenyeri", "Gasiza"],
                                "ruhanga": ["Rugende", "Ruhanga", "Mirama", "Nyagacyamo"],
                                "kabuga": ["Kabuga", "Kalisimbi", "Amahoro", "Masango"]
                            }
                        },
                        "rulindo": {
                            name: "Rulindo",
                            cells: {
                                "kabuga": ["Kabuga", "Kalisimbi", "Amahoro", "Masango"],
                                "nyabugogo": ["Nyabikoni", "Kiruhura", "Ibuyerihets"],
                                "nyarutarama": ["Gishushu", "Kamahwa", "Nyarutarama", "Juru"]
                            }
                        }
                    }
                },
                "kicukiro": {
                    name: "Kicukiro",
                    districts: {
                        "gahanga": {
                            name: "Gahanga",
                            sectors: {
                                "gahanga": ["Gahanga", "Kagarama", "Kavumu", "Rugarama"],
                                "kabeza": ["Kabeza", "Kalisimbi", "Amahoro", "Masango"],
                                "nyarugunga": ["Nyarugunga", "Kigarama", "Kavumu", "Rugarama"]
                            }
                        },
                        "gikondo": {
                            name: "Gikondo",
                            sectors: {
                                "kagunga": ["Kagunga", "Kabuye", "Rebero", "Gatare"],
                                "kanserege": ["Kanserege", "Marembo", "Kiganda"],
                                "kinunga": ["Ruganwa", "Kigugu", "Kinunga"]
                            }
                        },
                        "kagarama": {
                            name: "Kagarama",
                            sectors: {
                                "nyarurama": ["Twishorezo", "Kivu", "Karuyenzi", "Rebero"],
                                "bwerankoli": ["Nyenyeri", "Kimisange", "Ituze", "Gakokobe"],
                                "kigarama": ["Amahoro", "Byimana", "Mumataba", "Umucyo"]
                            }
                        },
                        "kicukiro": {
                            name: "Kicukiro",
                            sectors: {
                                "kicukiro": ["Kicukiro", "Ubumwe", "Triangle", "Isoko"],
                                "ngoma": ["AHITEGEYE", "Rugero", "Isangano", "Intaho"],
                                "gasharu": ["Umunyinya", "Amajyambe", "Sakirwa", "Gasharu"]
                            }
                        },
                        "kanyinya": {
                            name: "Kanyinya",
                            sectors: {
                                "nyamweru": ["Irembo", "Itaba", "Rwampara", "Kiberinka"],
                                "cyivugiza": ["Muhabura", "Munini", "Mahoro", "Gabiro"],
                                "gasharu": ["Kagunga", "Rwintare", "Karukoro", "Kigarama"]
                            }
                        },
                        "kibagabaga": {
                            name: "Kibagabaga",
                            sectors: {
                                "kibagabaga": ["Kalisimbi", "Muhabura", "Gabiro", "Butanyerera"],
                                "bibare": ["Injanji", "Imitari", "Inshuti", "Kabeza"],
                                "nyarubuyye": ["Nyarubuyye", "Kigarama", "Kavumu", "Rugarama"]
                            }
                        },
                        "masaka": {
                            name: "Masaka",
                            sectors: {
                                "gako": ["Gihuhe", "Rugende", "Butare", "Gicaca"],
                                "rusheshe": ["Cyankongi", "Cyeru", "Gatare", "Kagese"],
                                "mbabe": ["Kamashashi", "Ngarama", "Murambi", "Sangano"]
                            }
                        },
                        "nyarugunga": {
                            name: "Nyarugunga",
                            sectors: {
                                "kamashashi": ["Akindege", "Indatwa", "Intwari", "Kabagendwa"],
                                "rwimbogo": ["Igabiro", "Kabaya", "Kanogo", "Marembo"],
                                "nonko": ["Nyarutovu", "Gasaraba", "Gihanga", "Gitara"]
                            }
                        },
                        "niboye": {
                            name: "Niboye",
                            sectors: {
                                "gatare": ["Taba", "Gatare", "Rurembo", "Kamahoro"],
                                "niboye": ["Kanunga", "Mwijuto", "Mwijabo", "Nyarubande"],
                                "nyakabanda": ["Bukinanyana", "Karama", "Bumanzi", "Rugwiro"]
                            }
                        }
                    }
                },
                "nyarugenge": {
                    name: "Nyarugenge",
                    districts: {
                        "nyarugenge": {
                            name: "Nyarugenge",
                            sectors: {
                                "nyarugenge": ["Rwampara", "Umucyo", "Intwali", "Amahoro"],
                                "agatare": ["Umucyo", "Umurava", "Meraneza", "Agatare"],
                                "biryogo": ["Umurimo", "Biryogo", "Isoko", "Gabiro"]
                            }
                        },
                        "nyamirambo": {
                            name: "Nyamirambo",
                            sectors: {
                                "nyamirambo": ["Nyamirambo", "Ruhanga", "Kinyana", "Rugarama"],
                                "cyivugiza": ["Muhabura", "Munini", "Mahoro", "Gabiro"],
                                "gasharu": ["Kagunga", "Rwintare", "Karukoro", "Kigarama"]
                            }
                        },
                        "rwezamenyo": {
                            name: "Rwezamenyo",
                            sectors: {
                                "rwezamenyo": ["Madjengo", "Amahoro", "Abatarushwa", "Inkeragutabara"],
                                "kabuguru": ["Muhuza", "Murambi", "Muhoza", "Mumararungu"],
                                "nyakabanda": ["Munini", "Kokobe", "Gasiza", "Akinkware"]
                            }
                        },
                        "kimisagara": {
                            name: "Kimisagara",
                            sectors: {
                                "kimisagara": ["Nyamabuye", "Nyabugogo", "Kimisagara", "Kove"],
                                "katabaro": ["Mpazi", "Kamahoro", "Ubumwe", "Umubano"],
                                "kamuhoza": ["Ituze", "Mataba", "Rurama", "Karwangabo"]
                            }
                        },
                        "muhima": {
                            name: "Muhima",
                            sectors: {
                                "kabasengerezi": ["Ikana", "Icyeza", "Intwari", "Kabasengerezi"],
                                "nyabugogo": ["Indatwa", "Abeza", "Rwezangoro", "Umutekano"],
                                "amahoro": ["Ubuhezi", "Yamaha", "Kabahizi", "Minitrape"]
                            }
                        },
                        "nyabugogo": {
                            name: "Nyabugogo",
                            sectors: {
                                "nyabugogo": ["Nyabikoni", "Kiruhura", "Ibuyerihets", "Giticyinyoni"],
                                "kigali": ["Gisenga", "Kadobogo", "Rubuye", "Rugwengeri"],
                                "rurima": ["Ruhango", "Ryamakomali", "Ruriba", "Tubungo"]
                            }
                        }
                    }
                }
            }
        },
        "northern": {
            name: "Northern Province",
            districts: {
                "burera": {
                    name: "Burera",
                    sectors: {
                        "bungwe": ["Bungwe", "Kivumu", "Ruhondo", "Muro"],
                        "butaro": ["Butaro", "Kivumu", "Ruhondo", "Muro"],
                        "cyeru": ["Cyeru", "Kivumu", "Ruhondo", "Muro"],
                        "gahunga": ["Gahunga", "Kivumu", "Ruhondo", "Muro"],
                        "gicumbi": ["Gicumbi", "Kivumu", "Ruhondo", "Muro"],
                        "kivuye": ["Kivuye", "Kivumu", "Ruhondo", "Muro"],
                        "kivugiza": ["Kivugiza", "Kivumu", "Ruhondo", "Muro"],
                        "ngoma": ["Ngoma", "Kivumu", "Ruhondo", "Muro"],
                        "rushaki": ["Rushaki", "Kivumu", "Ruhondo", "Muro"],
                        "rugarama": ["Rugarama", "Kivumu", "Ruhondo", "Muro"],
                        "rusizi": ["Rusizi", "Kivumu", "Ruhondo", "Muro"],
                        "rwerere": ["Rwerere", "Kivumu", "Ruhondo", "Muro"],
                        "shyorongi": ["Shyorongi", "Kivumu", "Ruhondo", "Muro"],
                        "tumba": ["Tumba", "Kivumu", "Ruhondo", "Muro"]
                    }
                },
                "gakenke": {
                    name: "Gakenke",
                    sectors: {
                        "coko": ["Coko", "Kivumu", "Ruhondo", "Muro"],
                        "gashenyi": ["Gashenyi", "Kivumu", "Ruhondo", "Muro"],
                        "gikumbu": ["Gikumbu", "Kivumu", "Ruhondo", "Muro"],
                        "janja": ["Janja", "Kivumu", "Ruhondo", "Muro"],
                        "karambo": ["Karambo", "Kivumu", "Ruhondo", "Muro"],
                        "kivuruga": ["Kivuruga", "Kivumu", "Ruhondo", "Muro"],
                        "muyongwe": ["Muyongwe", "Kivumu", "Ruhondo", "Muro"],
                        "mugunga": ["Mugunga", "Kivumu", "Ruhondo", "Muro"],
                        "nyabikenke": ["Nyabikenke", "Kivumu", "Ruhondo", "Muro"],
                        "nyange": ["Nyange", "Kivumu", "Ruhondo", "Muro"],
                        "ruli": ["Ruli", "Kivumu", "Ruhondo", "Muro"],
                        "rusasa": ["Rusasa", "Kivumu", "Ruhondo", "Muro"]
                    }
                },
                "gicumbi": {
                    name: "Gicumbi",
                    sectors: {
                        "bukure": ["Bukure", "Kivumu", "Ruhondo", "Muro"],
                        "bwisige": ["Bwisige", "Kivumu", "Ruhondo", "Muro"],
                        "cyumba": ["Cyumba", "Kivumu", "Ruhondo", "Muro"],
                        "gicumbi": ["Gicumbi", "Kivumu", "Ruhondo", "Muro"],
                        "kaniga": ["Kaniga", "Kivumu", "Ruhondo", "Muro"],
                        "kageyo": ["Kageyo", "Kivumu", "Ruhondo", "Muro"],
                        "kivuye": ["Kivuye", "Kivumu", "Ruhondo", "Muro"],
                        "mukarange": ["Mukarange", "Kivumu", "Ruhondo", "Muro"],
                        "mukoto": ["Mukoto", "Kivumu", "Ruhondo", "Muro"],
                        "musha": ["Musha", "Kivumu", "Ruhondo", "Muro"],
                        "nyagatare": ["Nyagatare", "Kivumu", "Ruhondo", "Muro"],
                        "nyamiyaga": ["Nyamiyaga", "Kivumu", "Ruhondo", "Muro"],
                        "rubaya": ["Rubaya", "Kivumu", "Ruhondo", "Muro"],
                        "rushaki": ["Rushaki", "Kivumu", "Ruhondo", "Muro"],
                        "shangasha": ["Shangasha", "Kivumu", "Ruhondo", "Muro"]
                    }
                },
                "musanze": {
                    name: "Musanze",
                    sectors: {
                        "gashaki": ["Gashaki", "Kivumu", "Ruhondo", "Muro"],
                        "gatare": ["Gatare", "Kivumu", "Ruhondo", "Muro"],
                        "kinigi": ["Kinigi", "Kivumu", "Ruhondo", "Muro"],
                        "muhoza": ["Muhoza", "Kivumu", "Ruhondo", "Muro"],
                        "mukingo": ["Mukingo", "Kivumu", "Ruhondo", "Muro"],
                        "musanze": ["Musanze", "Kivumu", "Ruhondo", "Muro"],
                        "nyabugogo": ["Nyabugogo", "Kivumu", "Ruhondo", "Muro"],
                        "nyange": ["Nyange", "Kivumu", "Ruhondo", "Muro"],
                        "rwanda": ["Rwanda", "Kivumu", "Ruhondo", "Muro"],
                        "singati": ["Singati", "Kivumu", "Ruhondo", "Muro"]
                    }
                },
                "rulindo": {
                    name: "Rulindo",
                    sectors: {
                        "base": ["Base", "Kivumu", "Ruhondo", "Muro"],
                        "burega": ["Burega", "Kivumu", "Ruhondo", "Muro"],
                        "buyoga": ["Buyoga", "Kivumu", "Ruhondo", "Muro"],
                        "cyungo": ["Cyungo", "Kivumu", "Ruhondo", "Muro"],
                        "kinihira": ["Kinihira", "Kivumu", "Ruhondo", "Muro"],
                        "masoro": ["Masoro", "Kivumu", "Ruhondo", "Muro"],
                        "mbogo": ["Mbogo", "Kivumu", "Ruhondo", "Muro"],
                        "murambi": ["Murambi", "Kivumu", "Ruhondo", "Muro"],
                        "ngoma": ["Ngoma", "Kivumu", "Ruhondo", "Muro"],
                        "ntongwe": ["Ntongwe", "Kivumu", "Ruhondo", "Muro"],
                        "rusiga": ["Rusiga", "Kivumu", "Ruhondo", "Muro"],
                        "shyorongi": ["Shyorongi", "Kivumu", "Ruhondo", "Muro"]
                    }
                }
            }
        },
        "southern": {
            name: "Southern Province",
            districts: {
                "gisagara": {
                    name: "Gisagara",
                    sectors: {
                        "gikonko": ["Gikonko", "Kivumu", "Ruhondo", "Muro"],
                        "mugombwa": ["Mugombwa", "Kivumu", "Ruhondo", "Muro"],
                        "muganza": ["Muganza", "Kivumu", "Ruhondo", "Muro"],
                        "musha": ["Musha", "Kivumu", "Ruhondo", "Muro"],
                        "mukindo": ["Mukindo", "Kivumu", "Ruhondo", "Muro"],
                        "ndora": ["Ndora", "Kivumu", "Ruhondo", "Muro"],
                        "nyamagabe": ["Nyamagabe", "Kivumu", "Ruhondo", "Muro"],
                        "save": ["Save", "Kivumu", "Ruhondo", "Muro"],
                        "kansi": ["Kansi", "Kivumu", "Ruhondo", "Muro"],
                        "kibirizi": ["Kibirizi", "Kivumu", "Ruhondo", "Muro"],
                        "mubano": ["Mubano", "Kivumu", "Ruhondo", "Muro"]
                    }
                },
                "huye": {
                    name: "Huye",
                    sectors: {
                        "mbazi": ["Mbazi", "Kivumu", "Ruhondo", "Muro"],
                        "kinazi": ["Kinazi", "Kivumu", "Ruhondo", "Muro"],
                        "simbi": ["Simbi", "Kivumu", "Ruhondo", "Muro"],
                        "maraba": ["Maraba", "Kivumu", "Ruhondo", "Muro"],
                        "rwaniro": ["Rwaniro", "Kivumu", "Ruhondo", "Muro"],
                        "rusatira": ["Rusatira", "Kivumu", "Ruhondo", "Muro"],
                        "huye": ["Huye", "Kivumu", "Ruhondo", "Muro"],
                        "gishamvu": ["Gishamvu", "Kivumu", "Ruhondo", "Muro"],
                        "mukura": ["Mukura", "Kivumu", "Ruhondo", "Muro"],
                        "ruhashya": ["Ruhashya", "Kivumu", "Ruhondo", "Muro"],
                        "tumba": ["Tumba", "Kivumu", "Ruhondo", "Muro"],
                        "kivumu": ["Kivumu", "Kivumu", "Ruhondo", "Muro"],
                        "ngoma": ["Ngoma", "Kivumu", "Ruhondo", "Muro"],
                        "cyarwa": ["Cyarwa", "Kivumu", "Ruhondo", "Muro"]
                    }
                },
                "kamonyi": {
                    name: "Kamonyi",
                    sectors: {
                        "gacurabwenge": ["Gacurabwenge", "Kivumu", "Ruhondo", "Muro"],
                        "karama": ["Karama", "Kivumu", "Ruhondo", "Muro"],
                        "kayenzi": ["Kayenzi", "Kivumu", "Ruhondo", "Muro"],
                        "kigoma": ["Kigoma", "Kivumu", "Ruhondo", "Muro"],
                        "mugina": ["Mugina", "Kivumu", "Ruhondo", "Muro"],
                        "murambi": ["Murambi", "Kivumu", "Ruhondo", "Muro"],
                        "ngaruka": ["Ngaruka", "Kivumu", "Ruhondo", "Muro"],
                        "nyamiyaga": ["Nyamiyaga", "Kivumu", "Ruhondo", "Muro"],
                        "nyarubaka": ["Nyarubaka", "Kivumu", "Ruhondo", "Muro"],
                        "nyarusange": ["Nyarusange", "Kivumu", "Ruhondo", "Muro"],
                        "runda": ["Runda", "Kivumu", "Ruhondo", "Muro"],
                        "rukoma": ["Rukoma", "Kivumu", "Ruhondo", "Muro"]
                    }
                },
                "muhanga": {
                    name: "Muhanga",
                    sectors: {
                        "cyeza": ["Cyeza", "Kivumu", "Ruhondo", "Muro"],
                        "kibangu": ["Kibangu", "Kivumu", "Ruhondo", "Muro"],
                        "kivumu": ["Kivumu", "Kivumu", "Ruhondo", "Muro"],
                        "mushishiro": ["Mushishiro", "Kivumu", "Ruhondo", "Muro"],
                        "muyira": ["Muyira", "Kivumu", "Ruhondo", "Muro"],
                        "nyabiramba": ["Nyabiramba", "Kivumu", "Ruhondo", "Muro"],
                        "nyamabuye": ["Nyamabuye", "Kivumu", "Ruhondo", "Muro"],
                        "rongi": ["Rongi", "Kivumu", "Ruhondo", "Muro"],
                        "rugendabari": ["Rugendabari", "Kivumu", "Ruhondo", "Muro"],
                        "shyogwe": ["Shyogwe", "Kivumu", "Ruhondo", "Muro"],
                        "tumba": ["Tumba", "Kivumu", "Ruhondo", "Muro"]
                    }
                },
                "nyamagabe": {
                    name: "Nyamagabe",
                    sectors: {
                        "cyika": ["Cyika", "Kivumu", "Ruhondo", "Muro"],
                        "gasaka": ["Gasaka", "Kivumu", "Ruhondo", "Muro"],
                        "gatare": ["Gatare", "Kivumu", "Ruhondo", "Muro"],
                        "kamegeri": ["Kamegeri", "Kivumu", "Ruhondo", "Muro"],
                        "kibirizi": ["Kibirizi", "Kivumu", "Ruhondo", "Muro"],
                        "kitabi": ["Kitabi", "Kivumu", "Ruhondo", "Muro"],
                        "mugano": ["Mugano", "Kivumu", "Ruhondo", "Muro"],
                        "mushubi": ["Mushubi", "Kivumu", "Ruhondo", "Muro"],
                        "musange": ["Musange", "Kivumu", "Ruhondo", "Muro"],
                        "tambwe": ["Tambwe", "Kivumu", "Ruhondo", "Muro"],
                        "uwinkingi": ["Uwinkingi", "Kivumu", "Ruhondo", "Muro"],
                        "kaduha": ["Kaduha", "Kivumu", "Ruhondo", "Muro"],
                        "kibumbwe": ["Kibumbwe", "Kivumu", "Ruhondo", "Muro"],
                        "nkoman": ["Nkoman", "Kivumu", "Ruhondo", "Muro"],
                        "musebeya": ["Musebeya", "Kivumu", "Ruhondo", "Muro"],
                        "buruhukiro": ["Buruhukiro", "Kivumu", "Ruhondo", "Muro"],
                        "tare": ["Tare", "Kivumu", "Ruhondo", "Muro"]
                    }
                },
                "nyanza": {
                    name: "Nyanza",
                    sectors: {
                        "busoro": ["Busoro", "Kivumu", "Ruhondo", "Muro"],
                        "cyabakamyi": ["Cyabakamyi", "Kivumu", "Ruhondo", "Muro"],
                        "kibingo": ["Kibingo", "Kivumu", "Ruhondo", "Muro"],
                        "kibilizi": ["Kibilizi", "Kivumu", "Ruhondo", "Muro"],
                        "kigoma": ["Kigoma", "Kivumu", "Ruhondo", "Muro"],
                        "muyira": ["Muyira", "Kivumu", "Ruhondo", "Muro"],
                        "rwabicuma": ["Rwabicuma", "Kivumu", "Ruhondo", "Muro"],
                        "busasamana": ["Busasamana", "Kivumu", "Ruhondo", "Muro"],
                        "cyahinda": ["Cyahinda", "Kivumu", "Ruhondo", "Muro"],
                        "mukingo": ["Mukingo", "Kivumu", "Ruhondo", "Muro"],
                        "rwesero": ["Rwesero", "Kivumu", "Ruhondo", "Muro"],
                        "nyagisozi": ["Nyagisozi", "Kivumu", "Ruhondo", "Muro"],
                        "ruramba": ["Ruramba", "Kivumu", "Ruhondo", "Muro"],
                        "kibeho": ["Kibeho", "Kivumu", "Ruhondo", "Muro"],
                        "rusenge": ["Rusenge", "Kivumu", "Ruhondo", "Muro"]
                    }
                },
                "nyaruguru": {
                    name: "Nyaruguru",
                    sectors: {
                        "ruheru": ["Ruheru", "Kivumu", "Ruhondo", "Muro"],
                        "munini": ["Munini", "Kivumu", "Ruhondo", "Muro"],
                        "cyahinda": ["Cyahinda", "Kivumu", "Ruhondo", "Muro"],
                        "nyabimata": ["Nyabimata", "Kivumu", "Ruhondo", "Muro"],
                        "busanze": ["Busanze", "Kivumu", "Ruhondo", "Muro"],
                        "kivu": ["Kivu", "Kivumu", "Ruhondo", "Muro"],
                        "nyagisozi": ["Nyagisozi", "Kivumu", "Ruhondo", "Muro"],
                        "ruramba": ["Ruramba", "Kivumu", "Ruhondo", "Muro"],
                        "kibeho": ["Kibeho", "Kivumu", "Ruhondo", "Muro"],
                        "rusenge": ["Rusenge", "Kivumu", "Ruhondo", "Muro"],
                        "ngoma": ["Ngoma", "Kivumu", "Ruhondo", "Muro"],
                        "ngera": ["Ngera", "Kivumu", "Ruhondo", "Muro"],
                        "muganza": ["Muganza", "Kivumu", "Ruhondo", "Muro"],
                        "mata": ["Mata", "Kivumu", "Ruhondo", "Muro"]
                    }
                },
                "ruhango": {
                    name: "Ruhango",
                    sectors: {
                        "bweramana": ["Bweramana", "Kivumu", "Ruhondo", "Muro"],
                        "byimana": ["Byimana", "Kivumu", "Ruhondo", "Muro"],
                        "kabagari": ["Kabagari", "Kivumu", "Ruhondo", "Muro"],
                        "kinihira": ["Kinihira", "Kivumu", "Ruhondo", "Muro"],
                        "mbuye": ["Mbuye", "Kivumu", "Ruhondo", "Muro"],
                        "mukingo": ["Mukingo", "Kivumu", "Ruhondo", "Muro"],
                        "munini": ["Munini", "Kivumu", "Ruhondo", "Muro"],
                        "mushubati": ["Mushubati", "Kivumu", "Ruhondo", "Muro"],
                        "nyabinoni": ["Nyabinoni", "Kivumu", "Ruhondo", "Muro"],
                        "nyarusange": ["Nyarusange", "Kivumu", "Ruhondo", "Muro"]
                    }
                }
            }
        },
        "eastern": {
            name: "Eastern Province",
            districts: {
                "bugesera": {
                    name: "Bugesera",
                    sectors: {
                        "mareba": ["Mareba", "Kivumu", "Ruhondo", "Muro"],
                        "gashora": ["Gashora", "Kivumu", "Ruhondo", "Muro"],
                        "ntarama": ["Ntarama", "Kivumu", "Ruhondo", "Muro"],
                        "nyarugenge": ["Nyarugenge", "Kivumu", "Ruhondo", "Muro"],
                        "mwogo": ["Mwogo", "Kivumu", "Ruhondo", "Muro"],
                        "nyamata": ["Nyamata", "Kivumu", "Ruhondo", "Muro"],
                        "kamabuye": ["Kamabuye", "Kivumu", "Ruhondo", "Muro"],
                        "ruhuha": ["Ruhuha", "Kivumu", "Ruhondo", "Muro"],
                        "shyara": ["Shyara", "Kivumu", "Ruhondo", "Muro"],
                        "rweru": ["Rweru", "Kivumu", "Ruhondo", "Muro"],
                        "mayange": ["Mayange", "Kivumu", "Ruhondo", "Muro"],
                        "rilima": ["Rilima", "Kivumu", "Ruhondo", "Muro"],
                        "musenyi": ["Musenyi", "Kivumu", "Ruhondo", "Muro"],
                        "juru": ["Juru", "Kivumu", "Ruhondo", "Muro"],
                        "ngeruka": ["Ngeruka", "Kivumu", "Ruhondo", "Muro"]
                    }
                },
                "gatsibo": {
                    name: "Gatsibo",
                    sectors: {
                        "kabarore": ["Kabarore", "Kivumu", "Ruhondo", "Muro"],
                        "kiramuruzi": ["Kiramuruzi", "Kivumu", "Ruhondo", "Muro"],
                        "gitoki": ["Gitoki", "Kivumu", "Ruhondo", "Muro"],
                        "kizimuro": ["Kizimuro", "Kivumu", "Ruhondo", "Muro"],
                        "ngarama": ["Ngarama", "Kivumu", "Ruhondo", "Muro"],
                        "murambi": ["Murambi", "Kivumu", "Ruhondo", "Muro"],
                        "gatsibo": ["Gatsibo", "Kivumu", "Ruhondo", "Muro"],
                        "muhura": ["Muhura", "Kivumu", "Ruhondo", "Muro"],
                        "kiziguro": ["Kiziguro", "Kivumu", "Ruhondo", "Muro"],
                        "kageyo": ["Kageyo", "Kivumu", "Ruhondo", "Muro"],
                        "gasange": ["Gasange", "Kivumu", "Ruhondo", "Muro"],
                        "remera": ["Remera", "Kivumu", "Ruhondo", "Muro"],
                        "nyagahanga": ["Nyagahanga", "Kivumu", "Ruhondo", "Muro"],
                        "kimihurura": ["Kimihurura", "Kivumu", "Ruhondo", "Muro"]
                    }
                },
                "kayonza": {
                    name: "Kayonza",
                    sectors: {
                        "murundi": ["Murundi", "Kivumu", "Ruhondo", "Muro"],
                        "gahini": ["Gahini", "Kivumu", "Ruhondo", "Muro"],
                        "mwiri": ["Mwiri", "Kivumu", "Ruhondo", "Muro"],
                        "rukara": ["Rukara", "Kivumu", "Ruhondo", "Muro"],
                        "mukarange": ["Mukarange", "Kivumu", "Ruhondo", "Muro"],
                        "nyamirama": ["Nyamirama", "Kivumu", "Ruhondo", "Muro"],
                        "ruramira": ["Ruramira", "Kivumu", "Ruhondo", "Muro"],
                        "kabarondo": ["Kabarondo", "Kivumu", "Ruhondo", "Muro"],
                        "rwinkwavu": ["Rwinkwavu", "Kivumu", "Ruhondo", "Muro"],
                        "kabare": ["Kabare", "Kivumu", "Ruhondo", "Muro"],
                        "murama": ["Murama", "Kivumu", "Ruhondo", "Muro"],
                        "ndego": ["Ndego", "Kivumu", "Ruhondo", "Muro"]
                    }
                },
                "kirehe": {
                    name: "Kirehe",
                    sectors: {
                        "gahara": ["Gahara", "Kivumu", "Ruhondo", "Muro"],
                        "kirehe": ["Kirehe", "Kivumu", "Ruhondo", "Muro"],
                        "nyabigega": ["Nyabigega", "Kivumu", "Ruhondo", "Muro"],
                        "nyabikokora": ["Nyabikokora", "Kivumu", "Ruhondo", "Muro"],
                        "rwesero": ["Rwesero", "Kivumu", "Ruhondo", "Muro"],
                        "musaza": ["Musaza", "Kivumu", "Ruhondo", "Muro"],
                        "mpanga": ["Mpanga", "Kivumu", "Ruhondo", "Muro"],
                        "nyarubuye": ["Nyarubuye", "Kivumu", "Ruhondo", "Muro"],
                        "nyarutunga": ["Nyarutunga", "Kivumu", "Ruhondo", "Muro"],
                        "nyabitare": ["Nyabitare", "Kivumu", "Ruhondo", "Muro"],
                        "mahama": ["Mahama", "Kivumu", "Ruhondo", "Muro"]
                    }
                },
                "ngoma": {
                    name: "Ngoma",
                    sectors: {
                        "jarama": ["Jarama", "Kivumu", "Ruhondo", "Muro"],
                        "kazo": ["Kazo", "Kivumu", "Ruhondo", "Muro"],
                        "rukira": ["Rukira", "Kivumu", "Ruhondo", "Muro"],
                        "mutenderi": ["Mutenderi", "Kivumu", "Ruhondo", "Muro"],
                        "nyagasozi": ["Nyagasozi", "Kivumu", "Ruhondo", "Muro"],
                        "murama": ["Murama", "Kivumu", "Ruhondo", "Muro"],
                        "mvumba": ["Mvumba", "Kivumu", "Ruhondo", "Muro"],
                        "mugesera": ["Mugesera", "Kivumu", "Ruhondo", "Muro"],
                        "ntaga": ["Ntaga", "Kivumu", "Ruhondo", "Muro"],
                        "zaza": ["Zaza", "Kivumu", "Ruhondo", "Muro"],
                        "sake": ["Sake", "Kivumu", "Ruhondo", "Muro"],
                        "rukumberi": ["Rukumberi", "Kivumu", "Ruhondo", "Muro"],
                        "kibungo": ["Kibungo", "Kivumu", "Ruhondo", "Muro"],
                        "mahango": ["Mahango", "Kivumu", "Ruhondo", "Muro"],
                        "karembo": ["Karembo", "Kivumu", "Ruhondo", "Muro"]
                    }
                },
                "nyagatare": {
                    name: "Nyagatare",
                    sectors: {
                        "nyagatare": ["Nyagatare", "Kivumu", "Ruhondo", "Muro"],
                        "gatunda": ["Gatunda", "Kivumu", "Ruhondo", "Muro"],
                        "katabagemu": ["Katabagemu", "Kivumu", "Ruhondo", "Muro"],
                        "karangazi": ["Karangazi", "Kivumu", "Ruhondo", "Muro"],
                        "karama": ["Karama", "Kivumu", "Ruhondo", "Muro"],
                        "musheri": ["Musheri", "Kivumu", "Ruhondo", "Muro"],
                        "matimba": ["Matimba", "Kivumu", "Ruhondo", "Muro"],
                        "nyamirama": ["Nyamirama", "Kivumu", "Ruhondo", "Muro"],
                        "kizimba": ["Kizimba", "Kivumu", "Ruhondo", "Muro"],
                        "gashanda": ["Gashanda", "Kivumu", "Ruhondo", "Muro"],
                        "rwempasha": ["Rwempasha", "Kivumu", "Ruhondo", "Muro"],
                        "rugarama": ["Rugarama", "Kivumu", "Ruhondo", "Muro"],
                        "kazaza": ["Kazaza", "Kivumu", "Ruhondo", "Muro"],
                        "kaduha": ["Kaduha", "Kivumu", "Ruhondo", "Muro"],
                        "karama": ["Karama", "Kivumu", "Ruhondo", "Muro"]
                    }
                },
                "rwamagana": {
                    name: "Rwamagana",
                    sectors: {
                        "musha": ["Musha", "Kivumu", "Ruhondo", "Muro"],
                        "muhazi": ["Muhazi", "Kivumu", "Ruhondo", "Muro"],
                        "munyaga": ["Munyaga", "Kivumu", "Ruhondo", "Muro"],
                        "nyakariro": ["Nyakariro", "Kivumu", "Ruhondo", "Muro"],
                        "munyiginya": ["Munyiginya", "Kivumu", "Ruhondo", "Muro"],
                        "muyumbu": ["Muyumbu", "Kivumu", "Ruhondo", "Muro"],
                        "mwulire": ["Mwulire", "Kivumu", "Ruhondo", "Muro"],
                        "rubona": ["Rubona", "Kivumu", "Ruhondo", "Muro"],
                        "fumbwe": ["Fumbwe", "Kivumu", "Ruhondo", "Muro"],
                        "nzige": ["Nzige", "Kivumu", "Ruhondo", "Muro"],
                        "gahengeri": ["Gahengeri", "Kivumu", "Ruhondo", "Muro"],
                        "gishari": ["Gishari", "Kivumu", "Ruhondo", "Muro"]
                    }
                }
            }
        },
        "western": {
            name: "Western Province",
            districts: {
                "karongi": {
                    name: "Karongi",
                    sectors: {
                        "bwishyura": ["Bwishyura", "Kivumu", "Ruhondo", "Muro"],
                        "bwishyura": ["Bwishyura", "Kivumu", "Ruhondo", "Muro"],
                        "gitesi": ["Gitesi", "Kivumu", "Ruhondo", "Muro"],
                        "gishari": ["Gishari", "Kivumu", "Ruhondo", "Muro"],
                        "kayove": ["Kayove", "Kivumu", "Ruhondo", "Muro"],
                        "murambi": ["Murambi", "Kivumu", "Ruhondo", "Muro"],
                        "murunda": ["Murunda", "Kivumu", "Ruhondo", "Muro"],
                        "rugerero": ["Rugerero", "Kivumu", "Ruhondo", "Muro"],
                        "rwankumba": ["Rwankumba", "Kivumu", "Ruhondo", "Muro"],
                        "twumba": ["Twumba", "Kivumu", "Ruhondo", "Muro"]
                    }
                },
                "ngororero": {
                    name: "Ngororero",
                    sectors: {
                        "buhoro": ["Buhoro", "Kivumu", "Ruhondo", "Muro"],
                        "gashari": ["Gashari", "Kivumu", "Ruhondo", "Muro"],
                        "kageyo": ["Kageyo", "Kivumu", "Ruhondo", "Muro"],
                        "kavumu": ["Kavumu", "Kivumu", "Ruhondo", "Muro"],
                        "matyazo": ["Matyazo", "Kivumu", "Ruhondo", "Muro"],
                        "muhanda": ["Muhanda", "Kivumu", "Ruhondo", "Muro"],
                        "muhororo": ["Muhororo", "Kivumu", "Ruhondo", "Muro"],
                        "ngoro": ["Ngoro", "Kivumu", "Ruhondo", "Muro"],
                        "nyange": ["Nyange", "Kivumu", "Ruhondo", "Muro"],
                        "satan": ["Satan", "Kivumu", "Ruhondo", "Muro"]
                    }
                },
                "nyabihu": {
                    name: "Nyabihu",
                    sectors: {
                        "bigiro": ["Bigiro", "Kivumu", "Ruhondo", "Muro"],
                        "jomba": ["Jomba", "Kivumu", "Ruhondo", "Muro"],
                        "jenda": ["Jenda", "Kivumu", "Ruhondo", "Muro"],
                        "kabere": ["Kabere", "Kivumu", "Ruhondo", "Muro"],
                        "karago": ["Karago", "Kivumu", "Ruhondo", "Muro"],
                        "kintobo": ["Kintobo", "Kivumu", "Ruhondo", "Muro"],
                        "mukamira": ["Mukamira", "Kivumu", "Ruhondo", "Muro"],
                        "muramba": ["Muramba", "Kivumu", "Ruhondo", "Muro"],
                        "ruganda": ["Ruganda", "Kivumu", "Ruhondo", "Muro"],
                        "shyira": ["Shyira", "Kivumu", "Ruhondo", "Muro"],
                        "sinzi": ["Sinzi", "Kivumu", "Ruhondo", "Muro"]
                    }
                },
                "nyamasheke": {
                    name: "Nyamasheke",
                    sectors: {
                        "bushekeri": ["Bushekeri", "Kivumu", "Ruhondo", "Muro"],
                        "cyimbogo": ["Cyimbogo", "Kivumu", "Ruhondo", "Muro"],
                        "gihombo": ["Gihombo", "Kivumu", "Ruhondo", "Muro"],
                        "kagano": ["Kagano", "Kivumu", "Ruhondo", "Muro"],
                        "kanjongo": ["Kanjongo", "Kivumu", "Ruhondo", "Muro"],
                        "karengera": ["Karengera", "Kivumu", "Ruhondo", "Muro"],
                        "kirimbi": ["Kirimbi", "Kivumu", "Ruhondo", "Muro"],
                        "macuba": ["Macuba", "Kivumu", "Ruhondo", "Muro"],
                        "nyabugogo": ["Nyabugogo", "Kivumu", "Ruhondo", "Muro"],
                        "rango": ["Rango", "Kivumu", "Ruhondo", "Muro"],
                        "remera": ["Remera", "Kivumu", "Ruhondo", "Muro"],
                        "ruharambo": ["Ruharambo", "Kivumu", "Ruhondo", "Muro"],
                        "shangi": ["Shangi", "Kivumu", "Ruhondo", "Muro"],
                        "toho": ["Toho", "Kivumu", "Ruhondo", "Muro"]
                    }
                },
                "rubavu": {
                    name: "Rubavu",
                    sectors: {
                        "bombogo": ["Bombogo", "Kivumu", "Ruhondo", "Muro"],
                        "bugeshi": ["Bugeshi", "Kivumu", "Ruhondo", "Muro"],
                        "gisenyi": ["Gisenyi", "Kivumu", "Ruhondo", "Muro"],
                        "kanzenze": ["Kanzenze", "Kivumu", "Ruhondo", "Muro"],
                        "kivumu": ["Kivumu", "Kivumu", "Ruhondo", "Muro"],
                        "nyabugogo": ["Nyabugogo", "Kivumu", "Ruhondo", "Muro"],
                        "nyamyumba": ["Nyamyumba", "Kivumu", "Ruhondo", "Muro"],
                        "rubavu": ["Rubavu", "Kivumu", "Ruhondo", "Muro"],
                        "ruganda": ["Ruganda", "Kivumu", "Ruhondo", "Muro"],
                        "nyundo": ["Nyundo", "Kivumu", "Ruhondo", "Muro"],
                        "kivumu": ["Kivumu", "Kivumu", "Ruhondo", "Muro"],
                        "rugerero": ["Rugerero", "Kivumu", "Ruhondo", "Muro"]
                    }
                },
                "rusizi": {
                    name: "Rusizi",
                    sectors: {
                        "bugarama": ["Bugarama", "Kivumu", "Ruhondo", "Muro"],
                        "giheke": ["Giheke", "Kivumu", "Ruhondo", "Muro"],
                        "gihundwe": ["Gihundwe", "Kivumu", "Ruhondo", "Muro"],
                        "gikombe": ["Gikombe", "Kivumu", "Ruhondo", "Muro"],
                        "imena": ["Imena", "Kivumu", "Ruhondo", "Muro"],
                        "kamembe": ["Kamembe", "Kivumu", "Ruhondo", "Muro"],
                        "mururu": ["Mururu", "Kivumu", "Ruhondo", "Muro"],
                        "nyakabuye": ["Nyakabuye", "Kivumu", "Ruhondo", "Muro"],
                        "nkanka": ["Nkanka", "Kivumu", "Ruhondo", "Muro"],
                        "rwimvuna": ["Rwimvuna", "Kivumu", "Ruhondo", "Muro"],
                        "nkombwa": ["Nkombwa", "Kivumu", "Ruhondo", "Muro"]
                    }
                },
                "rutsiro": {
                    name: "Rutsiro",
                    sectors: {
                        "boneza": ["Boneza", "Kivumu", "Ruhondo", "Muro"],
                        "gihango": ["Gihango", "Kivumu", "Ruhondo", "Muro"],
                        "kigeyo": ["Kigeyo", "Kivumu", "Ruhondo", "Muro"],
                        "kivuye": ["Kivuye", "Kivumu", "Ruhondo", "Muro"],
                        "kivumu": ["Kivumu", "Kivumu", "Ruhondo", "Muro"],
                        "murunda": ["Murunda", "Kivumu", "Ruhondo", "Muro"],
                        "musasa": ["Musasa", "Kivumu", "Ruhondo", "Muro"],
                        "mushubati": ["Mushubati", "Kivumu", "Ruhondo", "Muro"],
                        "mushubiro": ["Mushubiro", "Kivumu", "Ruhondo", "Muro"],
                        "nyabirasi": ["Nyabirasi", "Kivumu", "Ruhondo", "Muro"],
                        "ruhango": ["Ruhango", "Kivumu", "Ruhondo", "Muro"],
                        "rusebeya": ["Rusebeya", "Kivumu", "Ruhondo", "Muro"]
                    }
                }
            }
        }
    }
};

// Function to populate dropdown
function populateDropdown(selectElement, options, defaultText = "Select...") {
    selectElement.innerHTML = `<option value="">${defaultText}</option>`;
    options.forEach(option => {
        const optionElement = document.createElement('option');
        optionElement.value = option.value || option;
        optionElement.textContent = option.name || option;
        selectElement.appendChild(optionElement);
    });
}

// Function to get province options
function getProvinceOptions() {
    return Object.keys(rwandaAddressData.provinces).map(key => ({
        value: key,
        name: rwandaAddressData.provinces[key].name
    }));
}

// Function to get district options for a province
function getDistrictOptions(provinceId) {
    const province = rwandaAddressData.provinces[provinceId];
    if (!province) return [];
    
    return Object.keys(province.districts).map(key => ({
        value: key,
        name: province.districts[key].name
    }));
}

// Function to get sector options for a district
function getSectorOptions(provinceId, districtId) {
    const province = rwandaAddressData.provinces[provinceId];
    if (!province || !province.districts[districtId]) return [];
    
    const district = province.districts[districtId];
    return Object.keys(district.sectors).map(key => ({
        value: key,
        name: district.sectors[key].name || key
    }));
}

// Function to get cell options for a sector
function getCellOptions(provinceId, districtId, sectorId) {
    const province = rwandaAddressData.provinces[provinceId];
    if (!province || !province.districts[districtId] || !province.districts[districtId].sectors[sectorId]) return [];
    
    const sector = province.districts[districtId].sectors[sectorId];
    return Object.keys(sector).map(key => ({
        value: key,
        name: key
    }));
}

// Function to get village options for a cell
function getVillageOptions(provinceId, districtId, sectorId, cellId) {
    const province = rwandaAddressData.provinces[provinceId];
    if (!province || !province.districts[districtId] || !province.districts[districtId].sectors[sectorId] || !province.districts[districtId].sectors[sectorId][cellId]) return [];
    
    const cell = province.districts[districtId].sectors[sectorId][cellId];
    return cell.map(village => ({
        value: village,
        name: village
    }));
}
