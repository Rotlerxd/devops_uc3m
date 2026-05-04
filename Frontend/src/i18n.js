import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

// Aquí definimos los dos idiomas requeridos para la inspección manual
const resources = {
  es: {
    translation: {
      "Dashboard Global - NewsRadar": "Dashboard Global - NewsRadar",
      "Noticias Procesadas (24h)": "Noticias Procesadas (24h)",
      "Alertas Activas": "Alertas Activas",
      "Fuentes Monitorizadas": "Fuentes Monitorizadas",
      "DISTRIBUCIÓN POR CATEGORÍA IPTC": "DISTRIBUCIÓN POR CATEGORÍA IPTC",
      "TENDENCIAS (WORD CLOUD)": "TENDENCIAS (WORD CLOUD)",
      "cambiar_idioma": "Switch to English"
    }
  },
  en: {
    translation: {
      "Dashboard Global - NewsRadar": "Global Dashboard - NewsRadar",
      "Noticias Procesadas (24h)": "Processed News (24h)",
      "Alertas Activas": "Active Alerts",
      "Fuentes Monitorizadas": "Monitored Sources",
      "DISTRIBUCIÓN POR CATEGORÍA IPTC": "IPTC CATEGORY DISTRIBUTION",
      "TENDENCIAS (WORD CLOUD)": "TRENDS (WORD CLOUD)",
      "cambiar_idioma": "Cambiar a Español"
    }
  }
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: "es", // Idioma por defecto al entrar
    interpolation: {
      escapeValue: false 
    }
  });

export default i18n;