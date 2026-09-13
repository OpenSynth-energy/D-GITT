"""
Constants for the RTE7000 baseline reconstruction package.
"""

# ─────────────────────────────────────────────
# RTE regions -> éCO2mix file names
# ─────────────────────────────────────────────

RTE_REGION_TO_ECO2MIX_REGION: dict[str, str] = {
    "Auvergne-Rhône-Alpes": "Auvergne-Rhône-Alpes",
    "Bourgogne-Franche-Comté": "Bourgogne-Franche-Comté",
    "Bretagne": "Bretagne",
    "Centre-Val de Loire": "Centre-Val-de-Loire",
    "Grand Est": "Grand-Est",
    "Hauts-de-France": "Hauts-de-France",
    "Île-de-France": "Ile-de-France",
    "Normandie": "Normandie",
    "Nouvelle-Aquitaine": "Nouvelle-Aquitaine",
    "Occitanie": "Occitanie",
    "Pays de la Loire": "Pays-de-la-Loire",
    "Provence-Alpes-Côte d'Azur": "PACA",
}


# ─────────────────────────────────────────────
# éCO2mix energy type <-> XIIDM energy_source
# ─────────────────────────────────────────────

ENERGY_SOURCE_TO_FILIERE: dict[str, str] = {
    "NUCLEAR": "Nucléaire",
    "HYDRO": "Hydraulique",
    "WIND": "Eolien",
    "SOLAR": "Solaire",
    "THERMAL": "Thermique",
    "OTHER": "Thermique",
}

# ─────────────────────────────────────────────
# éCO2mix filière names -> English display names
# ─────────────────────────────────────────────

FILIERE_EN: dict[str, str] = {
    "Nucléaire": "Nuclear",
    "Hydraulique": "Hydro",
    "Eolien": "Wind",
    "Solaire": "Solar",
    "Thermique": "Thermal",
    "Bioénergies": "Bioenergy",
}

ECO2MIX_PRODUCTION_COLS: list[str] = [
    "Thermique",
    "Nucléaire",
    "Eolien",
    "Solaire",
    "Hydraulique",
]

# ─────────────────────────────────────────────
# Interconnections: dangling line name prefix -> country
# ─────────────────────────────────────────────

COUNTRY_FROM_INTERCONNECTION: dict[str, str] = {
    "FR_ES": "Spain",
    "FR_BE": "Belgium",
    "FR_DE": "Germany",
    "FR_CH": "Switzerland",
    "FR_IT": "Italy",
    "FR_GB": "United Kingdom",
    "FR_LU": "Luxembourg",
}

COUNTRY_ALIASES: dict[str, str] = {
    "BE": "Belgium",
    "Belgium": "Belgium",

    "DE": "Germany",
    "DE_LU": "Germany",
    "DE-LU": "Germany",
    "Germany": "Germany",
    "Luxembourg": "Germany",

    "ES": "Spain",
    "Spain": "Spain",

    "GB": "United Kingdom",
    "UK": "United Kingdom",
    "United Kingdom": "United Kingdom",

    "IT": "Italy",
    "IT_NORTH": "Italy",
    "IT-North": "Italy",
    "Italy": "Italy",

    "CH": "Switzerland",
    "Switzerland": "Switzerland",
}


# ─────────────────────────────────────────────
# French department -> RTE region (ODRÉ geographic file)
# ─────────────────────────────────────────────

DEPT_TO_REGION_RTE: dict[str, str] = {
    # Auvergne-Rhône-Alpes
    "Ain": "Auvergne-Rhône-Alpes",
    "Allier": "Auvergne-Rhône-Alpes",
    "Ardèche": "Auvergne-Rhône-Alpes",
    "Cantal": "Auvergne-Rhône-Alpes",
    "Drôme": "Auvergne-Rhône-Alpes",
    "Haute-Loire": "Auvergne-Rhône-Alpes",
    "Haute-Savoie": "Auvergne-Rhône-Alpes",
    "Isère": "Auvergne-Rhône-Alpes",
    "Loire": "Auvergne-Rhône-Alpes",
    "Puy-de-Dôme": "Auvergne-Rhône-Alpes",
    "Rhône": "Auvergne-Rhône-Alpes",
    "Savoie": "Auvergne-Rhône-Alpes",

    # Bourgogne-Franche-Comté
    "Côte-d'Or": "Bourgogne-Franche-Comté",
    "Doubs": "Bourgogne-Franche-Comté",
    "Haute-Saône": "Bourgogne-Franche-Comté",
    "Jura": "Bourgogne-Franche-Comté",
    "Nièvre": "Bourgogne-Franche-Comté",
    "Saône-et-Loire": "Bourgogne-Franche-Comté",
    "Territoire de Belfort": "Bourgogne-Franche-Comté",
    "Yonne": "Bourgogne-Franche-Comté",

    # Bretagne
    "Côtes-d'Armor": "Bretagne",
    "Finistère": "Bretagne",
    "Ille-et-Vilaine": "Bretagne",
    "Morbihan": "Bretagne",

    # Centre-Val de Loire
    "Cher": "Centre-Val de Loire",
    "Eure-et-Loir": "Centre-Val de Loire",
    "Indre": "Centre-Val de Loire",
    "Indre-et-Loire": "Centre-Val de Loire",
    "Loir-et-Cher": "Centre-Val de Loire",
    "Loiret": "Centre-Val de Loire",

    # Grand Est
    "Ardennes": "Grand Est",
    "Aube": "Grand Est",
    "Bas-Rhin": "Grand Est",
    "Haute-Marne": "Grand Est",
    "Haut-Rhin": "Grand Est",
    "Marne": "Grand Est",
    "Meurthe-et-Moselle": "Grand Est",
    "Meuse": "Grand Est",
    "Moselle": "Grand Est",
    "Vosges": "Grand Est",

    # Hauts-de-France
    "Aisne": "Hauts-de-France",
    "Nord": "Hauts-de-France",
    "Oise": "Hauts-de-France",
    "Pas-de-Calais": "Hauts-de-France",
    "Somme": "Hauts-de-France",

    # Île-de-France
    "Essonne": "Île-de-France",
    "Hauts-de-Seine": "Île-de-France",
    "Paris": "Île-de-France",
    "Seine-et-Marne": "Île-de-France",
    "Seine-Saint-Denis": "Île-de-France",
    "Val-d'Oise": "Île-de-France",
    "Val-de-Marne": "Île-de-France",
    "Yvelines": "Île-de-France",

    # Normandie
    "Calvados": "Normandie",
    "Eure": "Normandie",
    "Manche": "Normandie",
    "Orne": "Normandie",
    "Seine-Maritime": "Normandie",

    # Nouvelle-Aquitaine
    "Charente": "Nouvelle-Aquitaine",
    "Charente-Maritime": "Nouvelle-Aquitaine",
    "Corrèze": "Nouvelle-Aquitaine",
    "Creuse": "Nouvelle-Aquitaine",
    "Deux-Sèvres": "Nouvelle-Aquitaine",
    "Dordogne": "Nouvelle-Aquitaine",
    "Gironde": "Nouvelle-Aquitaine",
    "Haute-Vienne": "Nouvelle-Aquitaine",
    "Landes": "Nouvelle-Aquitaine",
    "Lot-et-Garonne": "Nouvelle-Aquitaine",
    "Pyrénées-Atlantiques": "Nouvelle-Aquitaine",
    "Vienne": "Nouvelle-Aquitaine",

    # Occitanie
    "Ariège": "Occitanie",
    "Aude": "Occitanie",
    "Aveyron": "Occitanie",
    "Gard": "Occitanie",
    "Gers": "Occitanie",
    "Haute-Garonne": "Occitanie",
    "Hautes-Pyrénées": "Occitanie",
    "Hérault": "Occitanie",
    "Lot": "Occitanie",
    "Lozère": "Occitanie",
    "Pyrénées-Orientales": "Occitanie",
    "Tarn": "Occitanie",
    "Tarn-et-Garonne": "Occitanie",

    # Pays de la Loire
    "Loire-Atlantique": "Pays de la Loire",
    "Maine-et-Loire": "Pays de la Loire",
    "Mayenne": "Pays de la Loire",
    "Sarthe": "Pays de la Loire",
    "Vendée": "Pays de la Loire",

    # Provence-Alpes-Côte d'Azur
    "Alpes-de-Haute-Provence": "Provence-Alpes-Côte d'Azur",
    "Alpes-Maritimes": "Provence-Alpes-Côte d'Azur",
    "Bouches-du-Rhône": "Provence-Alpes-Côte d'Azur",
    "Hautes-Alpes": "Provence-Alpes-Côte d'Azur",
    "Var": "Provence-Alpes-Côte d'Azur",
    "Vaucluse": "Provence-Alpes-Côte d'Azur",
}