// Settings for graph.jsx
// TODO: Try not to hardcode
// TODO: Change ä,ö,ü

/**
 * dict for graph node positions
 */
export const node_coordinates_dict: { [node_name: string]: string[]} = {
    // Quarto
    "Spiel_Spiel": ["100", "100"],
    "Gesellschaftsspiel_Spiel": ["0", "250"],
    "Komplex_Spiel": ["100", "200"],
    "Brettspiel_Spiel": ["0", "200"],
    "Zehn_Minuten_Spiel": ["200", "200"],

    // Spielbrett
    "Spiel_Spielbrett": ["100", "100"],
    "Spielbrett_Spielbrett": ["50", "200"],
    "Feld_Spielbrett": ["0", "300"],
    "sechzehn_Spielbrett": ["0", "400"],
    "Spielbestandteil_Spielbrett": ["100", "300"],
    "Figurenvorrat_Spielbrett": ["150", "200"],

    // Spielfiguren
    "Spiel_Spielfiguren": ["100", "100"],
    "Spielfigur_Spielfiguren": ["100", "200"],
    "sechzehn_Spielfiguren": ["0", "300"],
    "Figurenmerkmal_Spielfiguren": ["100", "300"],
    "vier_Spielfiguren": ["0", "400"],
    "Farbe_Spielfiguren": ["50", "400"],
    "Grösse_Spielfiguren": ["100", "400"],
    "Form_Spielfiguren": ["150", "400"],
    "Struktur_Spielfiguren": ["200", "400"],

    // Spieler
    "Spiel_Spieler": ["100", "100"],
    "Spieler_Spieler": ["100", "200"],
    "zwei_Spieler": ["0", "300"],
    "Abwechselnd_Spieler": ["100", "300"],
    "Gegner_Spieler": ["200", "300"],

    // Spielziel
    "Spiel_Spielziel": ["100", "100"],
    "Reihe_Spielziel": ["0", "300"],
    "Ziel_Spielziel": ["100", "200"],
    "Anordnung_Spielziel": ["200", "300"],
    "Rufen_Spielziel": ["0", "400"],
    "Siegbedingung_Spielziel": ["50", "400"],
    "Figuren_Spielziel": ["150", "400"],
    "drei_Spielziel": ["350", "400"],
    "Figurenmerkmal_Spielziel": ["-50", "400"],
    "Horizontal_Spielziel": ["200", "400"],
    "Vertikal_Spielziel": ["250", "400"],
    "Diagonal_Spielziel": ["300", "400"],
    "vier_Spielziel": ["100", "400"],



    // Spielzüge
    "Spiel_Spielzüge": ["150", "200"],
    "Spielzug_Spielzüge": ["100", "100"],
    "Spielname_Spiel_Spielzüge": ["-100", "400"],
    "zwei_Spielzüge": ["0", "200"],
    "Rufen_Spielzüge": ["0", "300"],
    "Setzen_Spielzüge": ["100", "300"],
    "Wählen_Spielzüge": ["400", "300"],
    "Runde_Spielzüge": ["150", "250"],
    "Aktion_Spielzüge": ["0", "400"],
    "Spielfigur_Spielzüge": ["300", "400"],
    "Feld_Spielzüge": ["0", "500"],
    "Ausgewählt_Spielzüge": ["100", "500"],
    "Gegner_Spielzüge": ["400", "400"],
    "Figurenvorrat_Spielzüge": ["500", "300"],
    "Final_Spielzüge": ["50", "500"],
    "Spielbrett_Spielzüge": ["150", "500"],

    // Ende
    "Spielausgang_Ende": ["100", "200"],
    "Spiel_Ende": ["100", "100"],
    "drei_Ende": ["0", "400"],
    "Sieg_Ende": ["100", "400"],
    "Rufen_Ende": ["100", "500"],
    "Unentschieden_Ende": ["50", "400"],
    "Niederlage_Ende": ["150", "400"],
    "Reihe_Ende": ["200", "200"],
    "Siegchance_Ende": ["200", "300"],

    // Strategien
    "Spiel_Strategien": ["100", "100"],
    "Taktik_Strategien": ["100", "200"],
    "Kombinierbarkeit_Strategien": ["0", "300"],
    "Passiv_Strategien": ["100", "300"],
    "Aktiv_Strategien": ["150", "300"],
    "Blocken_Strategien": ["100", "400"],
}

/**
 * dict for graph colors.
 * Order needs to be adjusted if global plan was changed because the order is used for node categories.
 */
export const color_dict: { [block: string]: string} = {
    "Spiel": "#84598e",
    "Spielbrett": "#46327e",
    "Spielfiguren": "#54b4a4",
    "Spieler": "#846899",
    "Spielzüge": "#1ca384",
    "Spielziel": "#4cc46c",
    "Ende": "#fbe424",
    "Strategien": "#a3db3c",
}

/**
 * dict for curveness parameters
 * Curveness is needed for triple with the same subject and object but different verb
 */
export const curveness_dict: { [triple: string]: number} = {
    "(Gegner, sein, Spieler)": 0.2,
    "(Setzen, folgen_auf, Waehlen)": 0.1,
    "(Waehlen, für, Gegner)": 0.3,
}