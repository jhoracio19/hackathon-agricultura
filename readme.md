# Asistente Cafetalero Inteligente

> *"El mejor café de México no debería quedarse en manos de un coyote. Debería llegar directo a tu taza."*

![Python](https://img.shields.io/badge/Python-3.13-blue)
![Django](https://img.shields.io/badge/Django-6.0-green)
![WhatsApp](https://img.shields.io/badge/WhatsApp-Business_API-25D366)
![Gemini](https://img.shields.io/badge/Google-Gemini_2.5_Flash-orange)
![Hackathon](https://img.shields.io/badge/Hackathon-Por_Amor_a_Puebla_2026-red)

---

##  Contexto — Hackatón Por Amor a Puebla 2026

Proyecto desarrollado en **36 horas** durante el Hackatón Por Amor a Puebla 2026, organizado para generar soluciones tecnológicas al Plan Estatal de Desarrollo de Puebla.

**Eje seleccionado:** Transformación Agrícola
**Región objetivo:** Sierra Norte de Puebla
**Problema atacado:** Bajo aprovechamiento del valor del café, dependencia de intermediarios y falta de diversificación de ingresos en familias cafetaleras.

---

## El Problema

Puebla es el **4to productor de café en México**. En la Sierra Norte, más de **40,000 familias cafetaleras** enfrentan tres problemas diarios:

| Problema | Impacto |
|----------|---------|
| Venta a intermediarios (coyotes) | Reciben solo el 30% del precio real |
| Sin acceso a mercados de especialidad | No pueden llegar a tostadoras o exportadores |
| Subproductos desperdiciados | La cáscara y pulpa contaminan ríos |

**Ejemplo real:** Un agricultor de Cuetzalan vende 500 kg de cereza a $13/kg = **$6,500**. El mismo café procesado como Natural vendido directo a una tostadora = **$27,500**. La diferencia se la lleva el intermediario.

---

## ☕ La Solución — CampoAmigo

Asistente cafetalero inteligente que vive donde el agricultor ya está: **WhatsApp**.

Sin descargar nada. Sin internet rápido. Sin saber usar una computadora.

### 7 Funcionalidades del Bot

| # | Comando | Descripción |
|---|---------|-------------|
| 1 | `FOTO` | Diagnóstico de plagas con Gemini Vision AI |
| 2 | `PRECIO` | Precios reales del café en Sierra Norte |
| 3 | `VENDER` | Publica cosecha con variedad, proceso, precio y municipio |
| 4 | `EVENTOS` | Ferias y apoyos para cafetaleros de Puebla |
| 5 | `CLIMA` | Alertas agrícolas cruzadas con cultivo específico por municipio |
| 6 | `MIS COSECHAS` | CRUD completo de cosechas desde WhatsApp |
| 7 | `PLANEAR` | Predicción de siembra con datos climáticos reales |

### Marketplace Web

- Filtros por variedad, municipio, proceso, tipo de productor y ordenamiento
- Etiqueta **Economía Circular** para subproductos
- Etiqueta de proceso: Lavado, Natural, Honey, Anaeróbico
- Contacto directo con el productor por WhatsApp sin intermediarios
- 20 productores verificados con datos del directorio oficial del Gobierno de Puebla

---

## 🏗️ Arquitectura

```
WhatsApp Business API
        ↓
   Django Webhook
        ↓
   ┌────────────────────────────┐
   │     Lógica del Bot         │
   │  Máquina de Estados        │
   │  (15 estados de flujo)     │
   └────────────────────────────┘
        ↓              ↓              ↓
  Gemini Vision   OpenWeather    SQLite DB
  (Plagas + IA)   (Clima real)   (Productores
                                  Cosechas
                                  Eventos)
        ↓
   Django MVT
   Marketplace Web
```

---

## 🛠️ Stack Tecnológico

| Capa | Tecnología |
|------|------------|
| Backend | Django 6.0 + Python 3.13 |
| Base de datos | SQLite |
| Bot | WhatsApp Cloud API |
| IA Vision | Google Gemini 2.5 Flash |
| Clima | OpenWeather API |
| Búsqueda difusa | thefuzz + python-Levenshtein |
| Frontend | Bootstrap 5 + Fredoka + Poppins |
| Deploy | ngrok (desarrollo) |

---

## 🌱 Ejes de la Rúbrica Cubiertos

### Innovación Tecnológica
- Gemini Vision AI para diagnóstico de plagas por foto
- WhatsApp como interfaz conversacional inteligente
- Clima cruzado con cultivo específico por municipio
- Búsqueda difusa para errores de escritura del agricultor
- CRUD completo desde conversación de WhatsApp

### Impacto Social y Ambiental
- Elimina al intermediario — el agricultor recibe precio justo
- Subproductos (cáscara, pulpa) se convierten en productos comercializables
- Lo que contaminaba ríos ahora genera ingresos adicionales
- Acceso a mercados premium para productores sin recursos tecnológicos

### Viabilidad Técnica y Operativa
- Costo operativo menor a $500 MXN/mes
- Sin app que descargar — WhatsApp ya instalado en 94% de smartphones en México
- Escala a nuevos municipios con mínimo esfuerzo técnico
- Modelo de negocio: suscripción para compradores, siempre gratuito para agricultores

### Funcionalidad del Prototipo
- Demo funcional en vivo — no es mockup ni Figma
- 7 funciones completas en el bot
- Marketplace web con 5 filtros simultáneos
- CRUD completo desde conversación de WhatsApp
- Datos reales del directorio oficial del Gobierno de Puebla

### Alineación con Plan Estatal de Desarrollo
- Sierra Norte como región prioritaria del Plan Estatal de Puebla
- Café como producto bandera del estado
- Digitalización del campo como línea estratégica del plan
- Fortalecimiento de la cadena de valor cafetalera

---

## Modelo de Negocio

```
Agricultor     →    SIEMPRE GRATIS
                    Publica, vende y gestiona desde WhatsApp

Comprador      →    Suscripción $299-999 MXN/mes
(tostadoras,        Acceso ilimitado a productores verificados
exportadores,       de Sierra Norte con filtros avanzados
cafeterías)
```

**Costo operativo mensual estimado:**

| Servicio | Costo |
|----------|-------|
| Hosting (Railway/Render) | ~$20 USD/mes |
| WhatsApp Business API | Gratis hasta 1,000 conv/mes |
| Gemini API | Tier gratuito |
| OpenWeather API | Tier gratuito |
| **Total** | **< $500 MXN/mes** |

---

## Cobertura — Sierra Norte de Puebla

```
Cuetzalan del Progreso  •  Xicotepec de Juárez  •  Zihuateutla
Hueytamalco  •  Tlatlauquitepec  •  Tetela de Ocampo  •  Jonotla
Zapotitlán de Méndez  •  Naupan  •  Honey  •  Jalpan  •  Tlaola
Huauchinango  •  Zacatlán  •  Huitzilan de Serdán  •  Zongozotla
San Felipe Tepatlán  •  Cuautempan  •  Teziutlán
```

**Altitud promedio:** 800 - 1,800 msnm

---

## ☕ Variedades, Procesos y Subproductos

### Variedades de Café
Arábica · Garnica · Typica · Bourbon · Cereza · Pergamino · Verde

### Procesos de Transformación
| Proceso | Valor agregado |
|---------|----------------|
|  Lavado | +200% vs cereza cruda |
|  Natural | +300% vs cereza cruda |
|  Honey | +400% vs cereza cruda |
|  Fermentación Anaeróbica | +500% vs cereza cruda |

### Subproductos — Economía Circular 
- **Cáscara de Café** → Mercado de infusiones y tés (Cascara Tea)
- **Pulpa para Abono Orgánico** → Agricultura regenerativa
- **Miel de Flor de Café** → Mercado gourmet
- **Madera de Cafeto** → Industria del ahumado

---

##  Instalación y Configuración

### Requisitos
```bash
Python 3.13+
pip
ngrok
```

### Setup
```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/campoamigo.git
cd campoamigo

# Entorno virtual
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows

# Dependencias
pip install -r requirements.txt

# Variables de entorno
cp .env.example .env
# Editar .env con tus credenciales
```

### Variables de entorno requeridas
```env
SECRET_KEY=tu_django_secret_key
WHATSAPP_TOKEN=tu_token_meta_developer
WHATSAPP_VERIFY_TOKEN=agroscan2026
PHONE_NUMBER_ID=tu_phone_number_id
GEMINI_API_KEY=tu_gemini_api_key
OPENWEATHER_API_KEY=tu_openweather_api_key
```

### Migraciones y datos iniciales
```bash
python manage.py migrate
python manage.py loaddata cafe_sierra_norte
python manage.py loaddata productores_cafe
python manage.py loaddata subproductos_cafe
python manage.py loaddata eventos_cafe
python manage.py loaddata precios_cafe
```

### Levantar el servidor
```bash
# Terminal 1 — Django
python manage.py runserver

# Terminal 2 — ngrok
ngrok http 8000
```

### Configurar Webhook en Meta Developer
1. Copiar URL de ngrok: `https://tu-url.ngrok-free.dev/webhook/`
2. Verify token: `agroscan2026`
3. Suscribir evento: `messages`

---

##  Estructura del Proyecto

```
AgroScan/
├── agroscan/
│   ├── settings.py
│   └── urls.py
├── webhook/
│   ├── views.py          # Bot WhatsApp + Gemini + OpenWeather
│   └── urls.py
├── core/
│   ├── models.py         # Agricultor, Cosecha, Cultivo, Municipio...
│   ├── views.py          # Marketplace web
│   ├── admin.py
│   ├── urls.py
│   ├── templates/core/
│   │   ├── base.html
│   │   ├── home.html     # Marketplace con filtros
│   │   ├── detalle.html  # Detalle de cosecha + contacto WhatsApp
│   │   ├── dashboard.html
│   │   └── eventos.html  # Ferias y eventos cafetaleros
│   └── fixtures/
│       ├── cafe_sierra_norte.json
│       ├── productores_cafe.json
│       ├── subproductos_cafe.json
│       ├── eventos_cafe.json
│       └── precios_cafe.json
├── .env
├── requirements.txt
└── manage.py
```

---

## Impacto Proyectado

| Métrica | Valor |
|---------|-------|
| Familias cafetaleras Sierra Norte | 40,000+ |
| Incremento potencial en ingreso | Hasta 4x vs precio coyote |
| Municipios cubiertos | 19 |
| Subproductos comercializables | 4 |
| Costo de adopción para el agricultor | $0 |
| Costo operativo mensual | < $500 MXN |

---

## Roadmap

- [ ] Piloto con 10 productores reales en Cuetzalan (Oct-Dic 2026)
- [ ] Integración con AMECAFÉ para certificación de origen
- [ ] Sistema de calificaciones entre compradores y productores
- [ ] Soporte para pagos digitales desde WhatsApp
- [ ] Expansión a otras regiones cafetaleras de Puebla (Veracruz, Oaxaca)

---

## 👥 Equipo — PoliDevs

Desarrollado con ❤️ en 36 horas durante el Hackatón Por Amor a Puebla 2026.

| Integrante | Rol |
|------------|-----|
| José Horacio Ahuactzin García | Full Stack Developer |
| [Nombre compañero] | [Rol] |
| [Nombre compañero] | [Rol] |

**Universidad:** Benemérita Universidad Autónoma de Puebla (BUAP)
**Hackathon:** Por Amor a Puebla 2026
**Fecha:** 25 - 26 Abril 2026

---

*Construido en 36 horas para cambiar la vida de 40,000 familias cafetaleras de la Sierra Norte de Puebla.*

**☕ Del cafetal a tu taza. Sin intermediarios.**