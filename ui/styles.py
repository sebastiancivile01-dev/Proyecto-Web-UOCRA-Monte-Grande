import streamlit as st


def aplicar_estilos_globales():
    
    st.markdown("""
    <style>
    /* 1. FONDO GLOBAL DE LA APLICACIÓN */
    .stApp {
        background-image: url("https://raw.githubusercontent.com/sebastiancivile01-dev/Proyecto-Web-UOCRA-Monte-Grande/main/banner_uocra.jpg"); 
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    
    /* 2. CAJA BLANCA SEMITRANSPARENTE (Protege la lectura de los módulos) */
    .block-container {
        background-color: rgba(255, 255, 255, 0.95) !important;
        padding: 2rem 3rem !important;
        border-radius: 15px;
        box-shadow: 0px 8px 25px rgba(0,0,0,0.2);
        margin-top: 40px;
        margin-bottom: 40px;
    }

/* 3. COLORES INSTITUCIONALES Y BOTONES */
    h1, h2, h3 { color: #0033A0 !important; }
    
    div.stButton > button { 
        background-color: #0033A0 !important; 
        color: #ffffff !important; /* Blanco forzado */
        border-radius: 5px !important; 
        border: 1px solid #0033A0 !important; 
    }
    /* Forzamos que cualquier texto adentro del botón también sea blanco */
    div.stButton > button p, div.stButton > button span, div.stButton > button * { 
        color: #ffffff !important; 
    }
    div.stButton > button:hover { 
        background-color: #002277 !important; 
        color: #ffffff !important; 
        border: 1px solid #002277 !important; 
    }
    
    }
    /* Forzamos que las letras del menú se lean oscuro y en negrita */
    [data-testid="stSidebar"] .stRadio p { 
        color: #111111 !important; 
        font-weight: 600 !important; 
    }
    
    /* 4. SISTEMA DE TARJETAS KPI PROFESIONALES */
    .tarjeta-kpi {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.08);
        border-left: 6px solid #0033A0;
        text-align: center;
        margin-bottom: 20px;
    }
    .tarjeta-kpi.verde { border-left-color: #28a745; }
    .tarjeta-kpi.naranja { border-left-color: #fd7e14; }
    .tarjeta-kpi.violeta { border-left-color: #8A2BE2; }
    .tarjeta-kpi.rojo { border-left-color: #dc3545; }
    .kpi-titulo { color: #6c757d; font-size: 0.9rem; font-weight: bold; text-transform: uppercase; margin-bottom: 5px; }
    .kpi-valor { color: #212529; font-size: 2.2rem; font-weight: 900; margin: 0; }
    
    /* 5. CASILLEROS, FORMULARIOS Y ANTI MODO OSCURO (iOS) */
    /* Títulos arriba de las cajas */
    label, label p, label div {
        color: #222222 !important;
        font-weight: 600 !important;
    }
    
    /* El fondo de la caja: Un celeste/azul pastel muy clarito */
    div[data-baseweb="input"] > div, 
    div[data-baseweb="select"] > div, 
    div[data-baseweb="textarea"] > div {
        background-color: #e6f2ff !important; /* Celeste claro institucional */
        border: 1px solid #0033A0 !important;
        border-radius: 6px !important;
    }

    /* El texto que el usuario escribe adentro (El parche para iPhone) */
    input, textarea, div[data-baseweb="select"] {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important; /* Esto evita que iOS lo haga invisible */
        background-color: transparent !important;
    }
    
    /* 6. ARREGLO DE PESTAÑAS (TABS) - ANTI MODO OSCURO */
    button[data-baseweb="tab"] p {
        color: #555555 !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] p {
        color: #0033A0 !important; /* Azul UOCRA para la activa */
        font-size: 1.05rem !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        border-bottom: 3px solid #0033A0 !important;
    }
    button[data-baseweb="tab"] {
        background-color: transparent !important;
    }

    /* ======================================================= */
    /* 📱 MODO CELULAR (SOLO SE ACTIVA EN PANTALLAS CHICAS)    */
    /* ======================================================= */
    @media (max-width: 768px) {
        /* 1. Ajuste de la caja principal para que no rebalse */
        .block-container {
            padding: 1.5rem 1rem !important; 
            margin-top: 5px !important;
            max-width: 100vw !important;
            border-radius: 0px !important; /* En celular queda mejor sin bordes curvos a los lados */
        }
        
        /* 2. EL MAPA: Forzamos a que respete los límites de la pantalla del celular */
        iframe {
            max-width: 100% !important;
            height: 450px !important;
        }

        /* 3. Achicamos los títulos */
        h1 { font-size: 1.6rem !important; }
        h2 { font-size: 1.4rem !important; }
        h3 { font-size: 1.2rem !important; }
        
        /* 4. Botones y KPIs anchos */
        .stButton > button {
            width: 100% !important; 
            padding: 12px !important;
            font-size: 1.1rem !important;
            margin-bottom: 5px !important;
        }
        .kpi-valor { font-size: 2.2rem !important; }
        .tarjeta-kpi { padding: 15px !important; }
        
        /* 5. EL MENÚ: Desactivamos la orden que lo rompía, ahora se oculta solo */
        [data-testid="stSidebar"] {
            min-width: 0 !important;
            max-width: 85vw !important;
        }
    }
    </style>
""", unsafe_allow_html=True)


def aplicar_estilos_login():
    st.markdown("""
        <style>
        .stApp {
            background-image: url("https://raw.githubusercontent.com/sebastiancivile01-dev/Proyecto-Web-UOCRA-Monte-Grande/main/banner_uocra.jpg");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }

        [data-testid="stHeader"], [data-testid="stAppViewContainer"] {
            background: rgba(0,0,0,0) !important;
        }

        [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {
            background-color: rgba(255, 255, 255, 0.95);
            padding: 3rem;
            border-radius: 15px;
            box-shadow: 0px 8px 25px rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center !important;
        }
        </style>
    """, unsafe_allow_html=True)


def aplicar_estilos_mapa():
    st.markdown("""
        <style>
        iframe {
            border: 3px solid #000000 !important;
            border-radius: 8px;
            box-shadow: 0px 5px 15px rgba(0,0,0,0.3);
        }
        </style>
    """, unsafe_allow_html=True)



