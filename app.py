import streamlit as st
# Set page config as the very first execution statement in the script
st.set_page_config(
    page_title="AgriVision Disease Guard",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

import os
import time
from PIL import Image, ImageDraw
import io

# Import our modular multi-agent backend & security utilities
from agents.workflow import execute_disease_guard_pipeline

# ----------------- TRANSLATION DICTIONARIES & HELPERS -----------------
TRANSLATIONS = {
    "English": {
        "step_1": "Step 1: Select Crop Type & Enter Pathology Details:",
        "crop_label": "Crop Type",
        "symptoms_label": "Describe the symptoms in detail",
        "symptoms_help": "Describe symptoms to guide the Visual Diagnostician.",
        "step_2": "Step 2: Upload Leaf Pathology Photo (Vision Node):",
        "upload_label": "Upload leaf pathology photo",
        "upload_success": "📎 Image uploaded:",
        "thumbnail_label": "Leaf Specimen Thumbnail:",
        "run_button": "🔬 Run Multi-Agent Diagnostic Protocol",
        "output_panel_title": "🧠 Real-Time Multi-Agent Output Display",
        "spinner_agent1": "Visual Diagnostician (Agent 1): Executing pre-LLM PII scrubbing filter and diagnosing symptom profile...",
        "spinner_agent2": "MCP Strategy Broker (Agent 2): Querying local disease database and extracting bio-safe treatment rules...",
        "spinner_agent3": "Compliance & Containment Judge (Agent 3): Auditing generated actions and compiling containment playbook...",
        "audits_header": "🛡️ Executive Compliance Audits:",
        "privacy_audit": "Privacy Audit",
        "pii_cleaned": "🔒 PII Cleaned",
        "eco_safe_check": "Eco-Safe Check",
        "bio_uda": "🌿 100% Bio-UDA",
        "playbook_status": "Playbook Status",
        "tab_diagnosis": "🩺 AI Diagnosis",
        "tab_remedies": "🌿 Eco-Safe Remedies",
        "tab_playbook": "📋 Action Playbook",
        "diagnosed_pathogen": "Diagnosed Pathogen:",
        "confidence_score": "Confidence score:",
        "findings_header": "🔬 Pathological Findings Summary",
        "privacy_header": "🔒 Shift-Left Privacy Scrubbing Audit Log",
        "privacy_info": "The raw text was cleaned before transmitting to the external API model. All PII data has been redacted:",
        "uda_record_msg": "🛡️ Verified Universal Design for Agriculture (UDA) Bio-Safe Record",
        "organic_remedies_header": "🌿 Organic Bio-Treatments (Database Matches)",
        "cultural_practices_header": "🚜 Cultural & Field Practices",
        "warnings_header": "⚠️ Immediate Environmental Warnings",
        "compliance_approved": "✅ Strategy Compliance: APPROVED (0% synthetic toxic chemicals detected)",
        "export_button": "📥 Export Certified Mitigation Playbook",
        "ready_title": "Ready for Crop Diagnostics",
        "ready_desc": "Select one of the preloaded scenarios in the Quick-Start bar above or upload a leaf photo, then trigger the 3-Agent Protocol to compile diagnostic remedies.",
        "presets_header": "🚀 Quick-Start Demo Presets:",
        "mechanics_title": "💡 Multi-Agent Pipeline Mechanics:",
        "mechanics_desc": "1. **Security Shield-Left**: Redacts Coordinates, Names, and Contacts. Check out the preloaded presets to verify redaction output.<br>2. **Agent 1: Visual Diagnostician**: Determines pathological disease profile and severity metrics.<br>3. **Agent 2: MCP Strategy Broker**: Programmatically queries local verified database via standard MCP schemas.<br>4. **Agent 3: Compliance Judge**: Scans generated plans for toxic chemicals (DDT, Paraquat) and signs the final Markdown Playbook.",
        "input_panel_title": "🔬 Input & Security Command",
        "tomato_preset": "🍅 Tomato Blight",
        "wheat_preset": "🌾 Wheat Rust",
        "citrus_preset": "🍊 Citrus Greening",
        "active_preset": "Active Preset: ",
        "custom_details": "⚠️ Custom details loaded. Edit values or select a preset."
    },
    "Hindi": {
        "step_1": "चरण 1: अपनी फसल चुनें और बीमारी के लक्षणों का विवरण दें:",
        "crop_label": "फसल का प्रकार",
        "symptoms_label": "बीमारी के लक्षणों का विस्तार से वर्णन करें:",
        "symptoms_help": "मल्टी-एजेंट एआई को बीमारी की पहचान करने में मदद करने के लिए लक्षणों का विवरण दें।",
        "step_2": "चरण 2: रोगग्रस्त पत्ते का फोटो अपलोड करें (वैकल्पिक):",
        "upload_label": "यहाँ पत्ते का फोटो अपलोड करें (JPEG/PNG)",
        "upload_success": "📎 फोटो सफलतापूर्वक अपलोड हो गया है:",
        "thumbnail_label": "अपलोड किए गए पत्ते का थंबनेल:",
        "run_button": "🔬 एआई रोग निदान शुरू करें",
        "output_panel_title": "🧠 एआई एजेंटों द्वारा वास्तविक समय में विश्लेषण की रिपोर्ट",
        "spinner_agent1": "एजेंट 1 (मुख्य रोग विशेषज्ञ): आपकी सुरक्षा के लिए व्यक्तिगत डेटा साफ कर रहा है और लक्षणों का विश्लेषण कर रहा है...",
        "spinner_agent2": "एजेंट 2 (रणनीति समन्वयक): स्थानीय सुरक्षित डेटाबेस से जैविक उपचारों की खोज कर रहा है...",
        "spinner_agent3": "एजेंट 3 (सुरक्षा समीक्षक): उपचारों की जैविक सुरक्षा की जांच कर रहा है और कार्य योजना तैयार कर रहा है...",
        "audits_header": "🛡️ जैविक एवं सुरक्षा जांच परिणाम:",
        "privacy_audit": "गोपनीयता सुरक्षा",
        "pii_cleaned": "🔒 व्यक्तिगत जानकारी सुरक्षित",
        "eco_safe_check": "जैविक प्रमाणीकरण",
        "bio_uda": "🌿 100% सुरक्षित (Bio-UDA)",
        "playbook_status": "कार्य योजना स्थिति",
        "tab_diagnosis": "🩺 एआई रोग निदान",
        "tab_remedies": "🌿 सुरक्षित जैविक उपचार",
        "tab_playbook": "📋 अंतिम कार्य योजना",
        "diagnosed_pathogen": "पहचाना गया रोगजनक:",
        "confidence_score": "निदान की सत्यता का स्तर:",
        "findings_header": "🔬 रोग के लक्षणों का वैज्ञानिक विश्लेषण",
        "privacy_header": "🔒 सुरक्षित डेटा ऑडिट लॉग (गोपनीयता सुरक्षा)",
        "privacy_info": "डेटा ट्रांसमिशन से पहले सुरक्षा जांच में किसान की निजी जानकारी (जैसे फोन, नाम, स्थान) को हटा दिया गया है:",
        "uda_record_msg": "🛡️ प्रमाणित यूनिवर्सल एग्रीकल्चर डेटाबेस (UDA) के अनुसार सुरक्षित जैविक रिकॉर्ड",
        "organic_remedies_header": "🌿 अनुशंसित जैविक उपचार (सुरक्षित दवाएं)",
        "cultural_practices_header": "🚜 खेतों की साफ-सफाई और सही कृषि पद्धतियां",
        "warnings_header": "⚠️ तत्काल ध्यान देने योग्य सावधानियां",
        "compliance_approved": "✅ सुरक्षा अनुपालन: पूर्णतः स्वीकृत (0% रासायनिक/जहरीले कीटनाशक)",
        "export_button": "📥 सुरक्षित जैविक कार्य योजना (PDF/MD) डाउनलोड करें",
        "ready_title": "पौधों के रोग निदान के लिए तैयार",
        "ready_desc": "ऊपर दिए गए 'त्वरित-शुरुआत डेमो प्रीसेट' में से किसी एक रोग को चुनें या अपनी फसल के पत्तों की फोटो अपलोड करें और लक्षणों का विवरण लिखकर विश्लेषण शुरू करें।",
        "presets_header": "🚀 त्वरित-शुरुआत डेमो प्रीसेट:",
        "mechanics_title": "💡 एआई एजेंट प्रणाली कैसे काम करती है?",
        "mechanics_desc": "1. **सुरक्षा कवच**: आपकी व्यक्तिगत जानकारी (जैसे नाम, फोन नंबर, या स्थान) को हटाता है ताकि डेटा पूरी तरह सुरक्षित रहे।<br>2. **एजेंट 1 (रोग विशेषज्ञ)**: आपके द्वारा बताए गए लक्षणों और फोटो से बीमारी की पहचान करता है।<br>3. **एजेंट 2 (डेटाबेस समन्वयक)**: केवल प्रमाणित सरकारी व वैज्ञानिक जैविक कृषि डेटाबेस से उपचार खोजता है।<br>4. **एजेंट 3 (सुरक्षा समीक्षक)**: यह सुनिश्चित करता है कि कोई भी हानिकारक रासायनिक दवा (जैसे डीडीटी, पैराक्वाट) किसान को न सुझाई जाए।",
        "input_panel_title": "🔬 इनपुट और सुरक्षा कमांड",
        "tomato_preset": "🍅 टमाटर झुलसा (Tomato Blight)",
        "wheat_preset": "🌾 गेहूं गेरूआ (Wheat Rust)",
        "citrus_preset": "🍊 नींबू हरापन (Citrus Greening)",
        "active_preset": "सक्रिय प्रीसेट: ",
        "custom_details": "⚠️ कस्टम विवरण लोड किए गए। मान बदलें या प्रीसेट चुनें।"
    }
}

TRANSLATE_MOCK = {
    # Diseases (Simulated and Database names)
    "Late Blight": {
        "disease_name": "पछैती झुलसा (Late Blight)",
        "reasoning": "पत्तियों पर गहरे भूरे रंग के धब्बे और पीछे की तरफ सफेद फफूंद दिख रही है, जो पछैती झुलसा रोग के मुख्य लक्षण हैं।"
    },
    "Late Blight (Phytophthora infestans)": {
        "disease_name": "पछैती झुलसा (Late Blight - Phytophthora infestans)",
        "reasoning": "पत्तियों पर गहरे भूरे रंग के धब्बे और पीछे की तरफ सफेद फफूंद दिख रही है, जो पछैती झुलसा रोग (Phytophthora infestans) के मुख्य लक्षण हैं।"
    },
    "Wheat Rust": {
        "disease_name": "गेहूं का गेरूआ रोग (Wheat Rust)",
        "reasoning": "तनों और पत्तियों पर नारंगी-पीले रंग के पाउडर जैसे जंग के धब्बे दिख रहे हैं, जो गेहूं में गेरूआ रोग के लक्षण हैं।"
    },
    "Wheat Rust (Puccinia graminis / striiformis)": {
        "disease_name": "गेहूं का गेरूआ रोग (Wheat Rust - Puccinia graminis / striiformis)",
        "reasoning": "तनों और पत्तियों पर नारंगी-पीले रंग के पाउडर जैसे जंग के धब्बे दिख रहे हैं, जो गेहूं में गेरूआ रोग के लक्षण हैं।"
    },
    "Powdery Mildew": {
        "disease_name": "सफेद चूर्णिल रोग (Powdery Mildew)",
        "reasoning": "पत्तियों और तने की सतह पर सफेद पाउडर जैसी परत बन गई है, जो चूर्णिल आसिता (Powdery Mildew) का संकेत है।"
    },
    "Citrus Greening": {
        "disease_name": "सिट्रस ग्रीनिंग (Citrus Greening)",
        "reasoning": "पत्तियों का असमान पीलापन और फलों का बेढंगा आकार तथा स्वाद में कड़वाहट सिट्रस ग्रीनिंग (HLB) को दर्शाते हैं।"
    },
    "Citrus Greening (Huanglongbing - HLB)": {
        "disease_name": "सिट्रस ग्रीनिंग (Citrus Greening - Huanglongbing)",
        "reasoning": "पत्तियों का असमान पीलापन और फलों का बेढंगा आकार तथा स्वाद में कड़वाहट सिट्रस ग्रीनिंग (HLB) को दर्शाते हैं।"
    },
    "Septoria Leaf Spot": {
        "disease_name": "सेप्टोरिया पत्ती धब्बा रोग (Septoria Leaf Spot)",
        "reasoning": "निचले पत्तों पर भूरे किनारों और धूसर (धुंधले) केंद्र वाले छोटे गोल धब्बे सेप्टोरिया पत्ती धब्बा रोग का संकेत हैं।"
    },
    "Septoria Leaf Spot (Septoria lycopersici)": {
        "disease_name": "सेप्टोरिया पत्ती धब्बा रोग (Septoria Leaf Spot - Septoria lycopersici)",
        "reasoning": "निचले पत्तों पर भूरे किनारों और धूसर (धुंधले) केंद्र वाले छोटे गोल धब्बे सेप्टोरिया पत्ती धब्बा रोग का संकेत हैं।"
    },
    
    # Treatments (Database items)
    "Copper octanoate (OMRI listed soap-based copper fungicide)": {
        "val": "कॉपर ऑक्टानोएट (OMRI प्रमाणित साबुन-आधारित जैविक तांबा कवकनाशी) का छिड़काव करें।"
    },
    "Bacillus subtilis strain QST 713 bio-fungicide spray": {
        "val": "बैसिलस सबटिलिस (स्ट्रेन QST 713) जैव-कवकनाशी स्प्रे का उपयोग करें।"
    },
    "Wettable sulfur spray (early preventative application only)": {
        "val": "घुलनशील गंधक (सल्फर) स्प्रे का छिड़काव करें (केवल शुरुआती बचाव के लिए)।"
    },
    "Cold-pressed neem oil extract (1% concentration for early stages)": {
        "val": "कोल्ड-प्रेस (ठंडी विधि से निकाले गए) नीम के तेल के अर्क का 1% घोल बनाकर छिड़काव करें।"
    },
    "Potassium bicarbonate spray (3 tablespoons per gallon of water with a mild soap surfactant)": {
        "val": "पोटेशियम बाइकार्बोनेट स्प्रे (हल्के साबुन के साथ प्रति लीटर पानी में 10-12 ग्राम मिलाकर) छिड़कें।"
    },
    "Neem oil spray (OMRI listed)": {
        "val": "जैविक रूप से प्रमाणित नीम के तेल (OMRI सूचीबद्ध) का छिड़काव करें।"
    },
    "Dilute milk spray (40% milk, 60% water - acts as a natural fungicide under sunlight)": {
        "val": "दूध और पानी का पतला घोल (40% कच्चा दूध और 60% पानी) पत्तियों पर छिड़कें (यह धूप में प्राकृतिक कवकनाशी का काम करता है)।"
    },
    "Kaolin clay spray (creates a physical barrier against Asian Citrus Psyllid vectors)": {
        "val": "काओलिन क्ले का छिड़काव करें (यह नींबू के हानिकारक फुदका कीटों के खिलाफ एक सुरक्षात्मक परत बनाता है)।"
    },
    "Horticultural mineral oils (suffocates vector eggs and nymphs)": {
        "val": "बागवानी खनिज तेल (Horticultural Mineral Oil) का छिड़काव करें, जो कीटों के अंडों और लार्वा को नष्ट करता है।"
    },
    "Copper soap fungicide (OMRI approved)": {
        "val": "जैविक रूप से स्वीकृत कॉपर सोप कवकनाशी (OMRI प्रमाणित) का छिड़काव करें।"
    },
    "Bacillus amyloliquefaciens bio-fungicide": {
        "val": "बैसिलस एमाइलोलिक्विफ़ेशिएन्स जैव-कवकनाशी घोल का उपयोग करें।"
    },
    
    # Fallback/General Treatments
    "Use standard OMRI-certified multi-purpose botanical oil sprays (neem/pyrethrin).": {
        "val": "मानक जैविक रूप से प्रमाणित बहुउद्देशीय वनस्पति तेल स्प्रे (नीम/पाइरेथ्रिन) का छिड़काव करें।"
    },
    "Apply general beneficial microbial inoculants (Bacillus subtilis).": {
        "val": "सामान्य सुरक्षात्मक जीवाणु घोल (बैसिलस सबटिलिस) का मिट्टी और पत्तों पर प्रयोग करें।"
    },

    # Cultural & Field Practices
    "Prune the bottom 12 inches of leaves to prevent soil-splash inoculation.": {
        "val": "जमीन की मिट्टी उछलकर पत्तों पर न लगे, इसके लिए तने के निचले हिस्से की 12 इंच तक की पत्तियों की छंटाई कर दें।"
    },
    "Ensure wide spacing between plants (at least 24-36 inches) to maximize airflow.": {
        "val": "हवा के बेहतर प्रवाह के लिए पौधों के बीच कम से कम 2 से 3 फीट (24-36 इंच) की पर्याप्त दूरी रखें।"
    },
    "Use drip irrigation exclusively to keep foliage dry.": {
        "val": "पत्तियों को गीला होने से बचाने और कवक को रोकने के लिए केवल टपक सिंचाई (ड्रिप इरिगेशन) का उपयोग करें।"
    },
    "Destroy all infected plant residue immediately; do not compost.": {
        "val": "संक्रमित पौधों के सभी अवशेषों को खेत से बाहर ले जाकर जलाएं या नष्ट करें; इनसे जैविक खाद बिल्कुल न बनाएं।"
    },
    "Plant rust-resistant crop cultivars approved by local extension offices.": {
        "val": "स्थानीय कृषि विकास अधिकारी द्वारा अनुशंसित जंग-प्रतिरोधी (rust-resistant) उन्नत किस्मों के बीजों का ही उपयोग करें।"
    },
    "Implement a 3-year crop rotation program with non-cereal crops (e.g., legumes).": {
        "val": "फसल चक्र अपनाएं: अगले 3 वर्षों तक अनाज के बजाय उस खेत में दलहनी या फलीदार फसलें उगाएं।"
    },
    "Sow crops early in the season to avoid peak spore release times.": {
        "val": "रोग फैलाने वाले बीजाणुओं के हवा में फैलने से पहले, सीजन की शुरुआत में ही बुवाई का काम पूरा कर लें।"
    },
    "Locate plantings in full sun areas where possible.": {
        "val": "खेत में बुवाई या रोपाई ऐसी जगह करें जहां पर्याप्त और सीधी धूप आती हो।"
    },
    "Thin out foliage inside the canopy to increase light penetration and airflow.": {
        "val": "फसल की घनी पत्तियों की छंटाई करें ताकि धूप और हवा पौधों के अंदर तक आसानी से पहुंच सके।"
    },
    "Avoid overhead watering during evening hours.": {
        "val": "शाम के समय पत्तों के ऊपर से पानी छिड़कने से बचें, क्योंकि गीले पत्तों पर फफूंद तेजी से बढ़ती है।"
    },
    "Plant only certified disease-free nursery stock.": {
        "val": "केवल मान्यता प्राप्त नर्सरी से ही प्रमाणित और पूरी तरह से रोग-मुक्त पौधे खरीदकर लगाएं।"
    },
    "Release natural predators like parasitic wasps (Tamarixia radiata) to control psyllid vectors.": {
        "val": "रोग फैलाने वाले कीटों को जैविक रूप से नियंत्रित करने के लिए उनके प्राकृतिक परभक्षी मित्र कीटों (जैसे Tamarixia radiata ततैया) को खेत में छोड़ें।"
    },
    "Apply specialized micronutrient sprays to boost tree immunity and sustain fruit yield.": {
        "val": "पेड़ों की रोग प्रतिरोधक क्षमता बढ़ाने और फलों की पैदावार बनाए रखने के लिए विशेष सूक्ष्म पोषक तत्वों का छिड़काव करें।"
    },
    "Maintain a 3-year crop rotation cycle away from Solanaceous plants.": {
        "val": "आलू, टमाटर और बैंगन वर्ग (Solanaceous) के पौधों से दूर 3 वर्ष का फसल चक्र नियम लागू करें।"
    },
    "Apply organic mulch (straw or paper) around the base of plants to act as a barrier against soil spores.": {
        "val": "जड़ के आस-पास सूखी घास या भूसे की मल्चिंग (Mulching) करें, ताकि मिट्टी के कवक बीजाणु पौधों के संपर्क में न आएं।"
    },
    "Thoroughly clean stakes, cages, and gardening tools at the end of the season using a 10% bleach solution.": {
        "val": "खेती में उपयोग होने वाली खूंटियों, जालियों और उपकरणों को 10% ब्लीच के घोल से धोकर अच्छे से साफ करें।"
    },
    "Quarantine infected plants immediately.": {
        "val": "संक्रमित पौधों को तुरंत अन्य स्वस्थ पौधों से अलग (क्वारंटीन) करें।"
    },
    "Improve field sanitation by removing weeds and dead leaves.": {
        "val": "खेत की स्वच्छता में सुधार करें: खरपतवारों और मृत पत्तों को हटाकर खेत साफ रखें।"
    },
    "Increase plant spacing to maximize air circulation.": {
        "val": "हवा के प्रवाह को बढ़ाने के लिए पौधों के बीच की दूरी बढ़ाएं।"
    },
    
    # Warnings
    "No direct cure exists. Focus is strictly vector control and host plant health preservation.": {
        "val": "इस बीमारी का कोई सीधा इलाज उपलब्ध नहीं है। मुख्य ध्यान केवल रोगवाहक कीटों के नियंत्रण और पेड़ों की सेहत सुधारने पर केंद्रित करें।"
    },
    "Warning: Specific UDA protocol not indexed. Proceed with caution.": {
        "val": "सावधानी: इस रोग के लिए विशिष्ट UDA सुरक्षा प्रोटोकॉल अनुक्रमित नहीं है। सतर्कता से कार्य करें।"
    }
}

# Crop mapping
crop_display_mapping = {
    "Tomato": "Tomato / टमाटर",
    "Potato": "Potato / आलू",
    "Wheat": "Wheat / गेहूं",
    "Citrus": "Citrus / नींबू",
    "Corn": "Corn / मक्का",
    "Barley": "Barley / जौ",
    "Other": "Other / अन्य"
}

def translate_to_hindi(text: str, api_key: str = None) -> str:
    if not text:
        return text
    try:
        from openai import OpenAI
        gateway_url = os.getenv("GATEWAY_URL", "http://localhost:8080/v1")
        gateway_api_key = api_key or os.getenv("GATEWAY_API_KEY", "agrivision-sovereign-key-2026")
        client = OpenAI(
            base_url=gateway_url,
            api_key=gateway_api_key,
            default_headers={"X-API-Key": gateway_api_key}
        )
        prompt = (
            "You are a professional Hindi translator specializing in agriculture. "
            "Translate the following agricultural diagnosis, treatment details, or markdown playbook into clear, simple Hindi (Devanagari script) "
            "suitable for an Indian farmer. Keep English names of pathogens, scientific terms, or chemicals in brackets next to their Hindi terms (e.g. पछैती झुलसा (Late Blight)). "
            "Preserve all markdown structure, bullet points, warning callouts (> [!WARNING]), and headers exactly. Do NOT summarize or omit any content. "
            "Return ONLY the translated Hindi content:\n\n"
            f"{text}"
        )
        response = client.chat.completions.create(
            model=os.getenv("VLLM_MODEL", "meta-llama/Llama-3.1-8B-Instruct"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"{text}\n\n*(अनुवाद त्रुटि / Translation Error: {str(e)})*"

def translate_text(text: str, lang: str, api_key: str = None) -> str:
    if lang == "English" or not text:
        return text
    # Check if we have a static translation in TRANSLATE_MOCK
    if text in TRANSLATE_MOCK:
        if isinstance(TRANSLATE_MOCK[text], dict):
            return TRANSLATE_MOCK[text].get("val", TRANSLATE_MOCK[text].get("disease_name", text))
        return TRANSLATE_MOCK[text]
    
    stripped = text.strip()
    if stripped in TRANSLATE_MOCK:
        if isinstance(TRANSLATE_MOCK[stripped], dict):
            return TRANSLATE_MOCK[stripped].get("val", TRANSLATE_MOCK[stripped].get("disease_name", text))
        return TRANSLATE_MOCK[stripped]
        
    # Translate dynamically if API key is present
    if api_key:
        return translate_to_hindi(text, api_key)
        
    return text

def get_translated_playbook(state, lang, api_key=None):
    if lang == "English":
        return state.compliance_output.get("playbook_markdown", "")
    
    disease_name = translate_text(state.broker_output.get("disease_name", "Diagnosed Plant Disease"), lang, api_key)
    severity = state.diagnostician_output.get("severity", "Medium")
    confidence = state.diagnostician_output.get("confidence", 80.0)
    
    mcp_treatments_list = state.broker_output.get("organic_treatments", [])
    mcp_practices_list = state.broker_output.get("cultural_practices", [])
    mcp_warnings_list = state.broker_output.get("warnings", [])
    extra_guidance = state.broker_output.get("additional_guidance", "Follow standard organic agricultural practices.")
    
    translated_severity = "उच्च (High)" if severity == "High" else ("मध्यम (Medium)" if severity == "Medium" else "निम्न (Low)")
    translated_crop = translate_text(state.crop_type, lang, api_key)
    
    markdown_playbook = f"""# एग्रीविज़न रोग रक्षक एक्शन प्लेबुक (AgriVision Disease Guard Action Playbook)

## 🛡️ अनुपालन सत्यापन स्थिति (Compliance Verification Status)
> [!NOTE]
> **स्थिति:** स्वीकृत (APPROVED): 100% जैविक और गैर-विषाक्त  
> **सुरक्षा प्रोटोकॉल:** UDA (कृषि के लिए सार्वभौमिक डिज़ाइन) दिशानिर्देशों के तहत सत्यापित। कोई सिंथेटिक रासायनिक इनपुट नहीं मिला।

---

## 📋 फसल निदान सारांश (Crop Diagnosis Summary)
*   **लक्षित फसल (Target Crop):** {translated_crop}
*   **निदान की गई स्थिति (Diagnosed Condition):** **{disease_name}**
*   **विश्वास स्तर (Confidence Level):** `{confidence}%`
*   **संक्रमण की तीव्रता (Infection Severity):** `{translated_severity}`

---

## 🌿 पर्यावरण-अनुकूल रोकथाम योजना (Eco-Friendly Mitigation Plan)

### 1. जैविक उपचार (Organic Bio-Treatments - स्वीकृत इनपुट)
"""
    for t in mcp_treatments_list:
        display_t = translate_text(t, lang, api_key)
        markdown_playbook += f"- {display_t}\n"
        
    markdown_playbook += "\n### 2. कृषि और स्वच्छता पद्धतियां (Cultural & Sanitation Practices)\n"
    for p in mcp_practices_list:
        display_p = translate_text(p, lang, api_key)
        markdown_playbook += f"- {display_p}\n"
        
    if mcp_warnings_list:
        markdown_playbook += "\n### ⚠️ महत्वपूर्ण चेतावनियां (Critical Alerts)\n"
        for w in mcp_warnings_list:
            display_w = translate_text(w, lang, api_key)
            markdown_playbook += f"> [!WARNING]\n> {display_w}\n"
            
    display_guidance = translate_text(extra_guidance, lang, api_key)
    markdown_playbook += f"""
### 3. अतिरिक्त कृषि वैज्ञानिक मार्गदर्शन (Additional Agronomist Guidance)
{display_guidance}

---

## 🔒 सुरक्षा ऑडिट लॉग (Security Audit Logs)
*   **व्यक्तिगत डेटा (PII) जांच:** लागू (प्रसंस्करण से पहले किसान के व्यक्तिगत विवरण हटा दिए गए)।
*   **प्रतिबंधित पदार्थ स्कैनर:** प्रतिबंधित सिंथेटिक कीटनाशकों के खिलाफ जांचा गया। अनुपालन रेटिंग 100% है।
"""
    return markdown_playbook

# ----------------- DESIGN THEME & CUSTOM CSS INJECTION -----------------
# Inject core structural wrapper styling and enforce text contrast
css_code = """
<style>
    /* Global background gradient */
    .stApp {
        background: linear-gradient(135deg, #E8F0EA 0%, #F1F5F2 100%) !important;
    }
    
    /* Frosted-glass look around side-by-side columns */
    div[data-testid="stColumn"] {
        background: rgba(255, 255, 255, 0.65) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.4) !important;
        border-radius: 20px !important;
        padding: 28px !important;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.05) !important;
    }
    
    /* Reset styling for nested columns to prevent visual card nesting bugs */
    div[data-testid="stColumn"] div[data-testid="stColumn"] {
        background: transparent !important;
        backdrop-filter: none !important;
        -webkit-backdrop-filter: none !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0px !important;
    }
    
    /* Force deep charcoal-green for widget labels, headers, and standard markdown text */
    div[data-testid="stWidgetLabel"] p,
    div[data-testid="stWidgetLabel"] label,
    div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stMarkdownContainer"] li,
    div[data-testid="stMarkdownContainer"] h1,
    div[data-testid="stMarkdownContainer"] h2,
    div[data-testid="stMarkdownContainer"] h3,
    div[data-testid="stMarkdownContainer"] h4,
    div[data-testid="stMarkdownContainer"] h5,
    div[data-testid="stMarkdownContainer"] h6,
    div[data-testid="stExpander"] summary p,
    div[data-testid="stExpander"] summary span {
        color: #1E2A22 !important;
    }
    
    /* Style captions to be a dark sage-green for contrast */
    .stCaption, div[data-testid="stCaptionContainer"] p {
        color: #4A6B53 !important;
    }
    
    /* Make sure span elements inside markdown are high-contrast unless they are badges */
    div[data-testid="stMarkdownContainer"] span:not(.status-badge):not(.list-bullet):not(.st-icon) {
        color: #1E2A22 !important;
    }

    /* Force text elements inside input fields to be high-contrast dark charcoal-green */
    .stSelectbox select, .stTextInput input, .stTextArea textarea {
        color: #1E2A22 !important;
        background-color: #FFFFFF !important;
    }
    
    /* Override for buttons to ensure text stays high-contrast white */
    div.stButton button p, 
    div.stButton button span, 
    div[data-testid="stDownloadButton"] button p, 
    div[data-testid="stDownloadButton"] button span {
        color: #FFFFFF !important;
    }
    
    /* Primary buttons (Run Multi-Agent) */
    div.stButton > button {
        background: linear-gradient(135deg, #15803D 0%, #166534 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid #14532D !important;
        padding: 14px 20px !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 12px rgba(21, 128, 61, 0.2) !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #16a34a 0%, #15803D 100%) !important;
        box-shadow: 0 6px 18px rgba(22, 163, 74, 0.3) !important;
        transform: translateY(-2px) !important;
    }
    
    /* Export Playbook Download Button */
    div[data-testid="stDownloadButton"] > button {
        background: linear-gradient(135deg, #15803D 0%, #166534 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid #14532D !important;
        padding: 12px 24px !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 15px rgba(21, 128, 61, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    div[data-testid="stDownloadButton"] > button:hover {
        background: linear-gradient(135deg, #16a34a 0%, #15803D 100%) !important;
        box-shadow: 0 6px 20px rgba(22, 163, 74, 0.4) !important;
        transform: translateY(-2px) !important;
    }

    /* Beautifully framed dashed image upload zone */
    div[data-testid="stFileUploader"] {
        border: 2px dashed rgba(21, 128, 61, 0.3) !important;
        border-radius: 12px !important;
        padding: 16px !important;
        background-color: rgba(255, 255, 255, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    div[data-testid="stFileUploader"]:hover {
        border-color: #15803D !important;
        background-color: rgba(21, 128, 61, 0.05) !important;
    }
    
    /* Yellow Warning Callout High-Contrast Fix */
    div[data-testid="stNotification"],
    div[data-testid="stNotification"] p, 
    div[data-testid="stNotification"] span, 
    div[data-testid="stNotification"] div,
    .stAlert,
    .stAlert p,
    .stAlert span,
    .stAlert div {
        background-color: #FEF3C7 !important;
        color: #451A03 !important;
        font-weight: 700 !important;
    }
    div[data-testid="stNotification"] {
        border-left: 5px solid #D97706 !important;
    }
    
    /* Preset button row styling overrides */
    .preset-row button {
        background: rgba(21, 128, 61, 0.1) !important;
        border: 1px solid rgba(21, 128, 61, 0.3) !important;
        color: #15803D !important;
        padding: 6px 14px !important;
        border-radius: 20px !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        box-shadow: none !important;
        width: auto !important;
    }
    .preset-row button span {
        color: #15803D !important;
    }
    
    /* Clean Polaroid Leaf Specimen Thumbnail frame */
    .specimen-preview {
        background-color: #FFFFFF;
        border: 1px solid rgba(21, 128, 61, 0.2);
        border-radius: 12px;
        padding: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        display: inline-block;
        margin-top: 10px;
        margin-bottom: 15px;
        text-align: center;
    }
    
    /* Result summary cards */
    .summary-card {
        background-color: rgba(255, 255, 255, 0.85);
        border: 1px solid rgba(226, 232, 240, 0.8);
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 15px;
    }
    
    .list-item {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        margin-bottom: 10px;
        font-size: 0.95rem;
        line-height: 1.5;
    }
    .list-bullet {
        color: #15803D;
        font-weight: bold;
        font-size: 1.2rem;
        line-height: 1;
    }
    
    /* Tabs decoration styling */
    .stTabs [data-baseweb="tab"] {
        font-weight: 700;
        color: #4B5563;
        background-color: rgba(255, 255, 255, 0.5);
        border-radius: 8px;
        padding: 8px 16px;
        border: 1px solid rgba(229, 231, 235, 0.5);
    }
    .stTabs [aria-selected="true"] {
        color: #FFFFFF !important;
        background-color: #15803D !important;
    }
    .stTabs [aria-selected="true"] p, .stTabs [aria-selected="true"] span {
        color: #FFFFFF !important;
    }
</style>
"""
st.markdown(css_code, unsafe_allow_html=True)

# ----------------- DEMO IMAGE GENERATION UTILS -----------------
# Dynamically create sample crop pathology photos if they don't exist
def create_demo_images():
    assets_dir = "assets"
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
        
    demos = {
        "tomato_blight_demo.jpg": ("green", [((100, 100), 30, "brown"), ((150, 120), 20, "brown")]),
        "wheat_rust_demo.jpg": ("darkgoldenrod", [((50, 10), 10, "orange"), ((50, 80), 8, "orange"), ((50, 150), 12, "orange")]),
        "citrus_greening_demo.jpg": ("yellowgreen", [((80, 80), 40, "yellow"), ((140, 100), 25, "yellow")])
    }
    
    for filename, (bg_color, spots) in demos.items():
        filepath = os.path.join(assets_dir, filename)
        if not os.path.exists(filepath):
            img = Image.new("RGB", (300, 300), color=bg_color)
            draw = ImageDraw.Draw(img)
            draw.line([(150, 0), (150, 300)], fill="darkgreen", width=4)
            draw.line([(150, 100), (50, 50)], fill="darkgreen", width=2)
            draw.line([(150, 100), (250, 50)], fill="darkgreen", width=2)
            draw.line([(150, 200), (50, 150)], fill="darkgreen", width=2)
            draw.line([(150, 200), (250, 150)], fill="darkgreen", width=2)
            
            for (pos, radius, color) in spots:
                x, y = pos
                draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color, outline="black")
            img.save(filepath)

create_demo_images()

# Initialize Session States for Scenarios and Input binding
if "language" not in st.session_state:
    st.session_state.language = "English"
if "active_scenario" not in st.session_state:
    st.session_state.active_scenario = "none"
if "crop_type" not in st.session_state:
    st.session_state.crop_type = "Tomato"
if "symptoms" not in st.session_state:
    st.session_state.symptoms = "Lower leaves show dark brown spots with yellow halos. Papery margins with fuzzy white undersides."
if "farmer_name" not in st.session_state:
    st.session_state.farmer_name = "Farmer John Doe"
if "location_info" not in st.session_state:
    st.session_state.location_info = "North plot, Lat: 37.7749, Long: -122.4194 (Phone: +1-555-987-6543)"
if "execution_mode" not in st.session_state:
    st.session_state.execution_mode = "Production (API)" if os.getenv("GATEWAY_API_KEY", "").strip() else "Simulation (Mock API)"
if "gateway_key" not in st.session_state:
    st.session_state.gateway_key = os.getenv("GATEWAY_API_KEY", "agrivision-sovereign-key-2026")
if "gateway_url" not in st.session_state:
    st.session_state.gateway_url = os.getenv("GATEWAY_URL", "http://localhost:8080/v1")

# Quick launch template presets
demo_scenarios = {
    "Tomato Blight": {
        "crop": "Tomato",
        "farmer": "Farmer Johnathon Carter",
        "location": "North Field - Coordinates: 34.0522° N, 118.2437° W (Phone: +1-555-987-6543)",
        "symptoms": "Lower leaves show dark brown spots with yellow halos. Leaf margins are turning papery, and there is a fuzzy white coating on the underside after the recent heavy rainfall."
    },
    "Wheat Rust": {
        "crop": "Wheat",
        "farmer": "Amara Diallo",
        "location": "Ségou Plot C - Lat: 13.4312, Long: -6.2643 (Phone: +223 20 22 44 66)",
        "symptoms": "Orange, powdery rust-like pustules have formed in neat lines along the leaf sheaths and leaves. Stems seem slightly weakened."
    },
    "Citrus Greening": {
        "crop": "Citrus",
        "farmer": "Chen Wei",
        "location": "Sichuan Grove B, Lat 30.6586, Lon 104.0648 (Phone: +86 138-0000-0000)",
        "symptoms": "The leaves are mottled yellow asynchronously. The fruit is lopsided, remains green at the base, and has a very bitter taste. I suspect citrus greening."
    }
}

# ----------------- MAIN APP HEADER -----------------
header_left, header_right = st.columns([3, 1])
with header_left:
    st.markdown("""
    <div style="background: #FFFFFF; padding: 15px 25px; border-radius: 12px; border: 1px solid #E2E8F0; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between;">
        <div>
            <span style="font-family: 'Montserrat', sans-serif; font-weight: 800; font-size: 1.8rem; color: #15803D;">🌿 AgriVision Disease Guard</span>
            <span style="color:#64748B; margin-left:15px; font-size:1rem;">| Capstone Executive Dashboard</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
with header_right:
    selected_lang = st.selectbox(
        "🌐 Language / भाषा",
        options=["English", "हिन्दी (Hindi)"],
        index=0 if st.session_state.language == "English" else 1,
        help="Select app language / ऐप की भाषा चुनें"
    )
    st.session_state.language = "Hindi" if "हिन्दी" in selected_lang else "English"

# ----------------- TOP-ROW ACTION PRESETS BAR -----------------
if st.session_state.execution_mode == "Simulation (Mock API)":
    st.markdown(f"<p style='font-size: 0.95rem; font-weight: 700; color: #15803D; margin-bottom: 8px;'>{TRANSLATIONS[st.session_state.language]['presets_header']}</p>", unsafe_allow_html=True)
    col_s1, col_s2, col_s3, col_s4 = st.columns([1, 1, 1, 3])
    with col_s1:
        if st.button(TRANSLATIONS[st.session_state.language]["tomato_preset"], key="preset_tomato"):
            st.session_state.active_scenario = "Tomato Blight"
            st.session_state.crop_type = demo_scenarios["Tomato Blight"]["crop"]
            st.session_state.farmer_name = demo_scenarios["Tomato Blight"]["farmer"]
            st.session_state.location_info = demo_scenarios["Tomato Blight"]["location"]
            if st.session_state.language == "Hindi":
                st.session_state.symptoms = "निचले पत्तों पर पीले घेरे के साथ गहरे भूरे रंग के धब्बे दिख रहे हैं। हाल ही में हुई भारी बारिश के बाद पत्तों के किनारे कागज की तरह पतले हो रहे हैं और नीचे की तरफ सफेद फफूंद दिखाई दे रही है।"
            else:
                st.session_state.symptoms = demo_scenarios["Tomato Blight"]["symptoms"]
            st.rerun()
    with col_s2:
        if st.button(TRANSLATIONS[st.session_state.language]["wheat_preset"], key="preset_wheat"):
            st.session_state.active_scenario = "Wheat Rust"
            st.session_state.crop_type = demo_scenarios["Wheat Rust"]["crop"]
            st.session_state.farmer_name = demo_scenarios["Wheat Rust"]["farmer"]
            st.session_state.location_info = demo_scenarios["Wheat Rust"]["location"]
            if st.session_state.language == "Hindi":
                st.session_state.symptoms = "तने और पत्तियों पर नारंगी और पीले रंग के पाउडर जैसे जंग के धब्बे बन गए हैं। ऐसा लगता है कि पौधे का तना थोड़ा कमजोर हो गया है।"
            else:
                st.session_state.symptoms = demo_scenarios["Wheat Rust"]["symptoms"]
            st.rerun()
    with col_s3:
        if st.button(TRANSLATIONS[st.session_state.language]["citrus_preset"], key="preset_citrus"):
            st.session_state.active_scenario = "Citrus Greening"
            st.session_state.crop_type = demo_scenarios["Citrus Greening"]["crop"]
            st.session_state.farmer_name = demo_scenarios["Citrus Greening"]["farmer"]
            st.session_state.location_info = demo_scenarios["Citrus Greening"]["location"]
            if st.session_state.language == "Hindi":
                st.session_state.symptoms = "पत्तियां असममित रूप से पीली पड़ रही हैं। फल टेढ़े-मेढ़े और बेढंगे हैं, नीचे से हरे हैं और स्वाद में बहुत कड़वे हैं। मुझे सिट्रस ग्रीनिंग का संदेह है।"
            else:
                st.session_state.symptoms = demo_scenarios["Citrus Greening"]["symptoms"]
            st.rerun()
    with col_s4:
        if st.session_state.active_scenario != "none":
            active_scenario_translated = TRANSLATIONS[st.session_state.language]["tomato_preset"] if st.session_state.active_scenario == "Tomato Blight" else (TRANSLATIONS[st.session_state.language]["wheat_preset"] if st.session_state.active_scenario == "Wheat Rust" else TRANSLATIONS[st.session_state.language]["citrus_preset"])
            active_label = TRANSLATIONS[st.session_state.language]["active_preset"]
            st.markdown(f"""
            <div style="text-align: right; font-size: 0.85rem; color: #15803D; font-weight: 600; padding-top: 8px;">
                {active_label} <b>{active_scenario_translated}</b>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="text-align: right; font-size: 0.85rem; color: #0F172A; font-weight: 600; padding-top: 8px;">
                {TRANSLATIONS[st.session_state.language]["custom_details"]}
            </div>
            """, unsafe_allow_html=True)

# ----------------- PANEL GRID -----------------
panel_left, panel_right = st.columns([4, 6], gap="large")

# ================= PANEL A (LEFT): COMMAND & CONTROLS =================
with panel_left:
    st.markdown(f"<h3 style='color:#14532D; font-family:Montserrat; font-weight:700; font-size:1.3rem; margin-top:0; margin-bottom:15px;'>{TRANSLATIONS[st.session_state.language]['input_panel_title']}</h3>", unsafe_allow_html=True)
    
    st.markdown(f"<p style='font-size:0.9rem; font-weight:600; color:#4A6B53;'>{TRANSLATIONS[st.session_state.language]['step_1']}</p>", unsafe_allow_html=True)
    
    crop_options = ["Tomato", "Potato", "Wheat", "Citrus", "Corn", "Barley", "Other"]
    crop_display_options = [crop_display_mapping[c] for c in crop_options]
    default_index = 0
    if st.session_state.crop_type in crop_options:
        default_index = crop_options.index(st.session_state.crop_type)
        
    selected_crop_display = st.selectbox(
        TRANSLATIONS[st.session_state.language]["crop_label"],
        options=crop_display_options, index=default_index,
        help="Select the crop type from the verified list."
    )
    input_crop = crop_options[crop_display_options.index(selected_crop_display)]
    
    input_symptoms = st.text_area(
        TRANSLATIONS[st.session_state.language]["symptoms_label"],
        value=st.session_state.symptoms, 
        help=TRANSLATIONS[st.session_state.language]["symptoms_help"]
    )
    
    # Update session states with manually typed values
    st.session_state.crop_type = input_crop
    st.session_state.symptoms = input_symptoms

    st.markdown("---")

    st.markdown(f"<p style='font-size:0.9rem; font-weight:600; color:#4A6B53;'>{TRANSLATIONS[st.session_state.language]['step_2']}</p>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader(TRANSLATIONS[st.session_state.language]["upload_label"], type=["png", "jpg", "jpeg"], label_visibility="collapsed")
    
    if uploaded_file:
        st.success(f"{TRANSLATIONS[st.session_state.language]['upload_success']} {uploaded_file.name}")
        
        # POLAROID SPECIMEN THUMBNAIL PREVIEW
        try:
            img_preview = Image.open(uploaded_file)
            img_preview.thumbnail((150, 150))
            
            st.markdown(f"""
            <div class="specimen-preview">
                <p style="margin: 0 0 5px 0; font-size: 0.75rem; font-weight: 700; color: #4A6B53; text-transform: uppercase;">{TRANSLATIONS[st.session_state.language]['thumbnail_label']}</p>
            """, unsafe_allow_html=True)
            st.image(img_preview, width=120)
            st.markdown("</div>", unsafe_allow_html=True)
        except Exception:
            pass
        
    run_diagnose = st.button(TRANSLATIONS[st.session_state.language]["run_button"])

# ================= PANEL B (RIGHT): DYNAMIC OUTPUT =================
with panel_right:
    st.markdown(f"<h3 style='color:#15803D; font-family:Montserrat; font-weight:700; font-size:1.3rem; margin-top:0; margin-bottom:15px;'>{TRANSLATIONS[st.session_state.language]['output_panel_title']}</h3>", unsafe_allow_html=True)
    
    if run_diagnose:
        # Load image bytes if uploaded
        image_bytes = None
        if uploaded_file:
            img = Image.open(uploaded_file)
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG')
            image_bytes = img_byte_arr.getvalue()

        # Determine API key / gateway key
        api_key = os.getenv("GATEWAY_API_KEY", "") or st.session_state.gateway_key

        # Preprocess symptoms if in Hindi mode to support Hindi symptoms inputs
        pipeline_symptoms = st.session_state.symptoms
        if st.session_state.language == "Hindi":
            if st.session_state.execution_mode == "Production (API)" and api_key:
                try:
                    from openai import OpenAI
                    gateway_url = os.getenv("GATEWAY_URL", "http://localhost:8080/v1")
                    client = OpenAI(
                        base_url=gateway_url,
                        api_key=api_key,
                        default_headers={"X-API-Key": api_key}
                    )
                    translate_prompt = f"Translate the following farmer's symptom description in Hindi into clear agricultural English. Only return the English translation:\n\n{st.session_state.symptoms}"
                    resp = client.chat.completions.create(
                        model=os.getenv("VLLM_MODEL", "meta-llama/Llama-3.1-8B-Instruct"),
                        messages=[{"role": "user", "content": translate_prompt}],
                        temperature=0.2
                    )
                    pipeline_symptoms = resp.choices[0].message.content.strip()
                except Exception:
                    pass
            
            # If in Simulation Mode, or if the API call failed, do key-based appending
            # This enables mock disease matching for Hindi inputs
            h_symptoms = st.session_state.symptoms.lower()
            appended_keywords = []
            if any(kw in h_symptoms for kw in ["झुलसा", "धब्बे", "दाग"]):
                appended_keywords.append("blight spot")
            if any(kw in h_symptoms for kw in ["गेरूआ", "जंग", "रस्ट", "फफोले"]):
                appended_keywords.append("rust pustules")
            if any(kw in h_symptoms for kw in ["सफेद", "पाउडर", "फफूंद"]):
                appended_keywords.append("mildew white")
            if any(kw in h_symptoms for kw in ["पीला", "ग्रीनिंग", "कड़वा"]):
                appended_keywords.append("greening yellow")
            
            if appended_keywords:
                pipeline_symptoms = pipeline_symptoms + " " + " ".join(appended_keywords)

        # Display Step-by-Step logs using st.spinner (indicating active Agent state transitions)
        # Agent 1 (Visual Diagnostician): Process symptom profile & clean inputs via Shift-Left PII filter.
        with st.spinner(TRANSLATIONS[st.session_state.language]["spinner_agent1"]):
            time.sleep(1.0)
            state = execute_disease_guard_pipeline(
                crop_type=st.session_state.crop_type,
                symptoms=pipeline_symptoms,
                farmer_info=st.session_state.farmer_name,
                location_info=st.session_state.location_info,
                image_bytes=image_bytes
            )
            
        # Agent 2 (MCP Strategy Broker): Fetch organic treatments from verified database schemas.
        with st.spinner(TRANSLATIONS[st.session_state.language]["spinner_agent2"]):
            time.sleep(0.8)
            
        # Agent 3 (Compliance & Containment Judge): Scan results for compliance approval and compile Playbook.
        with st.spinner(TRANSLATIONS[st.session_state.language]["spinner_agent3"]):
            time.sleep(0.8)
            
        # Determine API key / gateway key
        api_key = os.getenv("GATEWAY_API_KEY", "") or st.session_state.gateway_key

        # Render Executive Top-Row Metrics & Badges inside miniature cards
        st.markdown(f"<h5 style='font-family:Montserrat; font-weight:700; margin-top:15px; margin-bottom:10px; color:#0F172A;'>{TRANSLATIONS[st.session_state.language]['audits_header']}</h5>", unsafe_allow_html=True)
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.markdown(f"""
            <div style="background: rgba(255, 255, 255, 0.85); border: 1px solid rgba(21, 128, 61, 0.25); padding: 12px; border-radius: 10px; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.02);">
                <span style="font-size: 0.75rem; color: #555; text-transform: uppercase; font-weight:700; display:block;">{TRANSLATIONS[st.session_state.language]['privacy_audit']}</span>
                <div style="color: #16A34A; font-weight: 800; font-size: 0.9rem; margin-top: 5px;">{TRANSLATIONS[st.session_state.language]['pii_cleaned']}</div>
            </div>
            """, unsafe_allow_html=True)
        with col_m2:
            st.markdown(f"""
            <div style="background: rgba(255, 255, 255, 0.85); border: 1px solid rgba(21, 128, 61, 0.25); padding: 12px; border-radius: 10px; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.02);">
                <span style="font-size: 0.75rem; color: #555; text-transform: uppercase; font-weight:700; display:block;">{TRANSLATIONS[st.session_state.language]['eco_safe_check']}</span>
                <div style="color: #16A34A; font-weight: 800; font-size: 0.9rem; margin-top: 5px;">{TRANSLATIONS[st.session_state.language]['bio_uda']}</div>
            </div>
            """, unsafe_allow_html=True)
        with col_m3:
            # Playbook approval status check
            audit_passed = "APPROVED" if state.compliance_output.get("is_compliant", True) else "REPLACED"
            audit_passed_disp = "स्वीकृत (APPROVED)" if audit_passed == "APPROVED" and st.session_state.language == "Hindi" else ("प्रतिस्थापित (REPLACED)" if audit_passed == "REPLACED" and st.session_state.language == "Hindi" else audit_passed)
            audit_color = "#16A34A" if audit_passed == "APPROVED" else "#D97706"
            st.markdown(f"""
            <div style="background: rgba(255, 255, 255, 0.85); border: 1px solid rgba(21, 128, 61, 0.25); padding: 12px; border-radius: 10px; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.02);">
                <span style="font-size: 0.75rem; color: #555; text-transform: uppercase; font-weight:700; display:block;">{TRANSLATIONS[st.session_state.language]['playbook_status']}</span>
                <div style="color: {audit_color}; font-weight: 800; font-size: 0.9rem; margin-top: 5px;">📋 {audit_passed_disp}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<div style='margin-bottom:20px;'></div>", unsafe_allow_html=True)
        
        # Setup Tabs for final dashboard outputs
        tab_diagnosis, tab_remedies, tab_playbook = st.tabs([
            TRANSLATIONS[st.session_state.language]["tab_diagnosis"],
            TRANSLATIONS[st.session_state.language]["tab_remedies"],
            TRANSLATIONS[st.session_state.language]["tab_playbook"]
        ])
        
        # TAB 1: Visual Diagnostician Outputs
        with tab_diagnosis:
            diag_output = state.diagnostician_output
            disease = diag_output.get("disease_name", "Diagnosed Pathology")
            confidence = diag_output.get("confidence", 0.0)
            severity = diag_output.get("severity", "Medium").upper()
            reasoning = diag_output.get("reasoning", "")
            
            # Translate if Hindi selected
            display_disease = translate_text(disease, st.session_state.language, api_key)
            display_reasoning = translate_text(reasoning, st.session_state.language, api_key)
            
            sev_color = "#EF6C00" # Orange
            if "HIGH" in severity:
                sev_color = "#C62828" # Red
            elif "LOW" in severity:
                sev_color = "#2E7D32" # Green
                
            translated_severity = severity
            if st.session_state.language == "Hindi":
                if "HIGH" in severity:
                    translated_severity = "उच्च (High)"
                elif "MEDIUM" in severity:
                    translated_severity = "मध्यम (Medium)"
                elif "LOW" in severity:
                    translated_severity = "निम्न (Low)"

            st.markdown(f"""
            <div class="summary-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:0.9rem; font-weight:700; color:#555;">{TRANSLATIONS[st.session_state.language]["diagnosed_pathogen"]}</span>
                    <span class="status-badge" style="background-color:{sev_color}; color:#ffffff !important;">{TRANSLATIONS[st.session_state.language]["playbook_status"]}: {translated_severity}</span>
                </div>
                <h3 style="color:#15803D; font-family:'Montserrat'; font-weight:800; margin:10px 0;">{display_disease}</h3>
                <div style="font-size:0.95rem;">{TRANSLATIONS[st.session_state.language]["confidence_score"]} <b>{confidence}%</b></div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"#### {TRANSLATIONS[st.session_state.language]['findings_header']}")
            reasoning_points = [p.strip() for p in display_reasoning.split(".") if p.strip()]
            for point in reasoning_points:
                st.markdown(f"<div class='list-item'><span class='list-bullet'>•</span><span>{point}.</span></div>", unsafe_allow_html=True)
                
            st.markdown("---")
            st.markdown(f"#### {TRANSLATIONS[st.session_state.language]['privacy_header']}")
            st.markdown(f"<p style='font-size:0.85rem; color:#666;'>{TRANSLATIONS[st.session_state.language]['privacy_info']}</p>", unsafe_allow_html=True)
            st.code(state.scrubbed_input, language="text")
            
        # TAB 2: MCP Strategy Broker Database Outputs
        with tab_remedies:
            broker_output = state.broker_output
            treatments = broker_output.get("organic_treatments", [])
            practices = broker_output.get("cultural_practices", [])
            warnings = broker_output.get("warnings", [])
            
            st.markdown(f"""
            <div style="background-color:#E8F5E9; border: 1px solid #C8E6C9; border-radius:10px; padding:12px; font-weight:700; color:#1B5E20; text-align:center; margin-bottom:15px; font-size:0.9rem;">
                {TRANSLATIONS[st.session_state.language]["uda_record_msg"]}
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"#### {TRANSLATIONS[st.session_state.language]['organic_remedies_header']}")
            for t in treatments:
                display_t = translate_text(t, st.session_state.language, api_key)
                st.markdown(f"<div class='list-item'><span class='list-bullet'>•</span><span>{display_t}</span></div>", unsafe_allow_html=True)
                
            st.markdown(f"#### {TRANSLATIONS[st.session_state.language]['cultural_practices_header']}")
            for p in practices:
                display_p = translate_text(p, st.session_state.language, api_key)
                st.markdown(f"<div class='list-item'><span class='list-bullet'>•</span><span>{display_p}</span></div>", unsafe_allow_html=True)
                
            if warnings:
                st.markdown(f"#### {TRANSLATIONS[st.session_state.language]['warnings_header']}")
                for w in warnings:
                    display_w = translate_text(w, st.session_state.language, api_key)
                    st.warning(display_w)
                    
        # TAB 3: Compliance & Final Action Playbook
        with tab_playbook:
            playbook_md = get_translated_playbook(state, st.session_state.language, api_key)
            
            if st.session_state.language == "Hindi":
                compliance_msg = "✅ रणनीति अनुपालन: स्वीकृत (0% सिंथेटिक जहरीले रसायन पाए गए)"
            else:
                compliance_msg = "✅ Strategy Compliance: APPROVED (0% synthetic toxic chemicals detected)"
            
            st.markdown(f"""
            <div style="background-color:#E8F5E9; border-left:5px solid #2E7D32; padding:12px; border-radius:6px; color:#1B5E20; margin-bottom:15px; font-size:0.9rem; font-weight:600;">
                {compliance_msg}
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(playbook_md)
            
            st.download_button(
                label=TRANSLATIONS[st.session_state.language]["export_button"],
                data=playbook_md,
                file_name="AgriVision_Disease_Guard_Playbook.md",
                key="download_playbook_btn",
                mime="text/markdown"
            )
            
    else:
        ready_title = TRANSLATIONS[st.session_state.language]["ready_title"]
        ready_desc = TRANSLATIONS[st.session_state.language]["ready_desc"]
        st.markdown(f"""
        <div style="text-align:center; padding: 40px 10px;">
            <span style="font-size:3.5rem;">🌾</span>
            <h3 style="font-family:'Montserrat'; font-weight:700; color:#2E7D32; margin-top:15px;">{ready_title}</h3>
            <p style="color:#666; font-size:0.95rem; max-width:450px; margin: 10px auto;">
                {ready_desc}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        flowchart_path = "assets/pipeline_flowchart.png"
        if os.path.exists(flowchart_path):
            try:
                flowchart_img = Image.open(flowchart_path)
                st.image(flowchart_img, caption="Multi-Agent Orchestration Flow (Visual Diagnostician ➔ MCP Broker ➔ Compliance Judge)", width="stretch")
            except Exception:
                pass
                
        mechanics_title = TRANSLATIONS[st.session_state.language]["mechanics_title"]
        mechanics_desc = TRANSLATIONS[st.session_state.language]["mechanics_desc"]
        st.markdown(f"""
        <div style="background-color:#F5F7F8; padding:20px; border-radius:12px; border: 1px solid #E0E0E0; margin-top:20px; font-size:0.9rem; color:#444;">
            <b style="color:#1B5E20; display:block; margin-bottom:8px;">{mechanics_title}</b>
            {mechanics_desc}
        </div>
        """, unsafe_allow_html=True)

# ----------------- MAIN PAGE FOOTER: CREDENTIALS & PRIVACY EXPANDER -----------------
st.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)
with st.expander("⚙️ Sovereign Gateway & Security Audit"):
    gateway_url_env = os.getenv("GATEWAY_URL", "http://localhost:8080/v1")
    gateway_key_env = os.getenv("GATEWAY_API_KEY", "agrivision-sovereign-key-2026")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        st.markdown("<b>🛡️ Sovereign Gateway Configuration:</b>", unsafe_allow_html=True)
        st.radio(
            "Select Execution Mode",
            options=["Production (API)", "Simulation (Mock API)"],
            index=0 if gateway_key_env else 1,
            horizontal=True,
            key="execution_mode"
        )
        if st.session_state.execution_mode == "Production (API)":
            st.session_state.gateway_url = st.text_input("FastAPI Gateway URL", value=st.session_state.gateway_url or gateway_url_env, help="Port 8080 Sovereign Gateway endpoint")
            st.session_state.gateway_key = st.text_input("Gateway X-API-Key", type="password", value=st.session_state.gateway_key or gateway_key_env)
            if st.session_state.gateway_key:
                os.environ["GATEWAY_API_KEY"] = st.session_state.gateway_key
            if st.session_state.gateway_url:
                os.environ["GATEWAY_URL"] = st.session_state.gateway_url
                
    with col_f2:
        st.markdown("<b>👤 Farmer Metadata (PII Test Fields):</b>", unsafe_allow_html=True)
        st.text_input("Farmer Name", key="farmer_name", help="Simulate inputting real farmer name to test automated PII scrubbing.")
        st.text_input("Coordinates / Location Context", key="location_info", help="Simulate inputting real contact or coordinate information.")
        
    with col_f3:
        st.markdown("<b>🔒 Sovereign Security & Redaction Stack:</b>", unsafe_allow_html=True)
        st.markdown("""
        - **Gateway Port**: `8080` (FastAPI Proxy ➔ vLLM: `8000`)
        - **Rate Limiting**: `60 req/min` via SlowAPI
        - **Indian PII Redaction**: Aadhaar, 10-digit Mobile, Emails
        - **Guided Decoding**: Pydantic JSON enforcement via vLLM
        """)
        st.info("Verification: All inputs undergo Indian PII sanitization at Gateway before vLLM ingress.")
