import { PresetScenario } from "../types";

// Premium handclass real-world hardware and spy gear presets (original premium core)
const CORE_PRESETS: PresetScenario[] = [
  // ==========================================
  // CATEGORY 1: Spy & Covert Gear (Fully authentic spy assets)
  // ==========================================
  {
    id: "spy_usb_charger",
    name: "مقبس شاحن جداري ذو كاميرا مخفية (Covert USB Charger Camera)",
    category: "Spy & Covert Gear",
    size: "4.8cm x 3.2cm x 3.2cm",
    description: "شاحن USB جداري حقيقي بقدرة 5V/2A مزود بعدسة كاميرا مجهرية مخفية خلف لوح زجاج أكريليك غامق يمتص الضوء ومصمم لمنع الانعكاس. يشمل منفذ اتصال لاسلكي للبث المباشر وقارئ بطاقة MicroSD مدمج.",
    confidence: 99.5,
    toolsFound: ["عدسة مجهرية مخفية (Pinhole Lens)", "هوائي إرسال لا سلكي 2.4GHz", "محلل استهلاك الطاقة المستمر"],
    hideCameraStatus: "🔴 خطر أمني مرتفع: تم رصد عدسة تجسس مجهرية خلف غطاء المقبس! تردد البث النشط: 2.412 GHz.",
    extraDetails: [
      { key: "Refraction Index", value: "1.49 High-convoluted lens feedback" },
      { key: "Wireless Beacon", value: "WiFi standard 802.11b/g/n active" },
      { key: "Continuous AC Power", value: "Direct AC 110-220V continuous line draw" },
      { key: "Detection Method", value: "Optical lens glare reflection sweep" }
    ],
    imageUrl: "usb_charger_spy",
    boundingBox: { x: 35, y: 35, w: 30, h: 30 }
  },
  {
    id: "spy_smoke_detector",
    name: "كاشف دخان مفخخ بكاميرا بانورامية (Hidden Camera Smoke Detector)",
    category: "Spy & Covert Gear",
    size: "12.0cm x 12.0cm x 4.5cm",
    description: "جهاز كاشف للدخان يثبت على السقف يبدو حقيقياً كلياً، ولكنه يحتوي داخلياً على كاميرا لاسلكية بانورامية 360 درجة عالية الدقة ومستشعرات حركة مع بطارية ليثيوم احتياطية طويلة الأجل.",
    confidence: 98.6,
    toolsFound: ["عدسة تجسس بزاوية واسعة (Fisheye Optic)", "باعث أشعة تحت حمراء غير مرئية 940nm", "بطارية ليثيوم بوليمر ضخمة"],
    hideCameraStatus: "🔴 خطر أمني: تم رصد انعكاس غريب للمشهد داخل شبكة كاشف الدخان. باعث IR نشط للرؤية الليلية بدون وهج.",
    extraDetails: [
      { key: "Spectral Signature", value: "940nm Invisible Night-Vision Active" },
      { key: "FOV Coverage", value: "360-degree panoramic ceiling sweep" },
      { key: "Casing Cavity Space", value: "65% occupied by battery & transmitter" },
      { key: "RF Signal Emission", value: "Cyclical packet uplink active every 3s" }
    ],
    imageUrl: "smoke_detector_spy",
    boundingBox: { x: 20, y: 15, w: 60, h: 50 }
  },
  {
    id: "spy_mirror_clock",
    name: "ساعة مكتب منبهة ذات مرآة تجسس (Concealed Desk Clock Camera)",
    category: "Spy & Covert Gear",
    size: "10.5cm x 4.0cm x 3.8cm",
    description: "ساعة مكتب رقمية حقيقية عاكسة، تخفي خلف زجاجها العاكس المستقطب عدسة كاميرا مراقبة لاسلكية دقيقة ومستشعر لامتصاص الصوت وحركات الغرفة مما يستحيل رؤيتها بالعين المجردة.",
    confidence: 97.8,
    toolsFound: ["عدسة عريضة الزاوية خلف الزجاج", "ميكروفون التجسس الصوتي عالي الحساسية", "وصلة طاقة مستمرة مخفية"],
    hideCameraStatus: "🔴 خطر أمني: تم العثور على كاميرا تجسس عند الزاوية اليمنى للساعة خلف طبقة الاستقطاب.",
    extraDetails: [
      { key: "Screen Transmittance", value: "35% transmission / 65% reflection" },
      { key: "Integrated Mic", value: "Electret sub-capsule active audio log" },
      { key: "Thermal Footprint", value: "+3.2°C ambient hotspot at core processor" },
      { key: "Connection Standard", value: "AP Wireless pairing mode enabled" }
    ],
    imageUrl: "mirror_clock_spy",
    boundingBox: { x: 18, y: 25, w: 64, h: 50 }
  },
  {
    id: "spy_screw_head",
    name: "برغي مجهري مفخخ بكاميرا (Pinhole Screw Head Spy Camera)",
    category: "Spy & Covert Gear",
    size: "1.2cm x 1.2cm x 2.5cm",
    description: "برغي حديدي قياسي من نوع Phillips برأس مفرغ من الوسط تماماً لإفساح المجال لعدسة كاميرا مجهرية فائقة الصغر 1 مم متصلة بلوحة معالجة خلف لوح الجدار الجبسي.",
    confidence: 99.2,
    toolsFound: ["قناة مرور ضوئي مجهرية 1mm", "شريحة معالجة الكاميرا خلف الجدار", "كابل شريطي فائق الرفع للنقل"],
    hideCameraStatus: "🔴 خطر حرج: تم رصد برغي مفخخ بعدسة مجهرية حقيقية! الانعكاس البؤري للعدسة أكد وجود زجاج مقعر بالداخل.",
    extraDetails: [
      { key: "Screw Type", value: "Standard M3 wall mount metal bolt modification" },
      { key: "CMOS Sensor Class", value: "Sub-millimeter 1/4 inch CMOS wafer" },
      { key: "Physical Cable Track", value: "Ultra-thin FPC ribbon behind drywall" },
      { key: "Magnetic Distortion", value: "0.85 microtesla focus coil footprint" }
    ],
    imageUrl: "screw_spy_cam",
    boundingBox: { x: 45, y: 45, w: 10, h: 10 }
  },
  {
    id: "spy_covert_pen",
    name: "قلم حبر جاف لاسلكي مزود بكاميرا (WiFi Spy Ballpoint Pen)",
    category: "Spy & Covert Gear",
    size: "14.5cm x 1.4cm x 1.4cm",
    description: "قلم حبر تجاري فاخر حقيقي في مظهره الخارجي وفي خط الكتابة، ولكنه يشتمل على منزلق مخفي في مشبك الجيب يخفي عدسة كاميرا HD ومسجل صوت بسعة داخلية 32 جيجابايت.",
    confidence: 98.4,
    toolsFound: ["مشبك جيب ذو منزلق بؤري", "فتحة مسجل صوت دقيقة", "منفذ USB مخفي لإعادة نقل البيانات والتغذية"],
    hideCameraStatus: "🔴 خطر أمني: تم رصد كاميرا قلم تجسس! الكثافة المعدنية الداخلية غير طبيعية وتتجاوز حجم خرطوشة الحبر.",
    extraDetails: [
      { key: "Memory Storage", value: "32GB High-speed NAND flash integrated" },
      { key: "Battery Lifetime", value: "75 Minutes continuous DVR recording" },
      { key: "Activation Switch", value: "Tactile micro top button control" },
      { key: "Covert Slider Shield", value: "Mechanically sliding lens cap protector" }
    ],
    imageUrl: "spy_pen_cam",
    boundingBox: { x: 40, y: 20, w: 20, h: 60 }
  },
  {
    id: "spy_gsm_audio",
    name: "جهاز تنصت صوتي عبر شريحة اتصال GSM (GSM Audio Bug Listener)",
    category: "Spy & Covert Gear",
    size: "3.5cm x 2.2cm x 1.5cm",
    description: "جهاز تجسس صوتي دقيق يعمل ببطاقة SIM هاتفية. عند الاتصال بالرقم، يقوم الجهاز بفتح الخط بصمت تام للبدء في الاستماع إلى كافة الأصوات المحيطة به، مستخدماً بطارية للاستعداد الطويل.",
    confidence: 99.0,
    toolsFound: ["مستقبل شبكات خلوية GSM/GPRS", "مستشعرات صوتية مزدوجة عالية الحساسية", "درج بطاقة Nano SIM"],
    hideCameraStatus: "🔴 تحذير تنصت: تم التقاط موجات تردد راديوي دورية مطابقة لاتصالات شبكات الجيل الثاني (GSM 900/1800) المستمرة.",
    extraDetails: [
      { key: "Cell Network Support", value: "Quadraband GSM 850/900/1800/1900 MHz" },
      { key: "Microphone Sensitivity", value: "Can pick up whispers up to 8 meters away" },
      { key: "Battery Standby", value: "Up to 5 Days (Active call limit: 3 Hours)" },
      { key: "Carrier Uplink Check", value: "Active audio callback trigger enabled" }
    ],
    imageUrl: "gsm_active_bug",
    boundingBox: { x: 30, y: 30, w: 40, h: 40 }
  },
  {
    id: "spy_gps_tracker",
    name: "جهاز تتبع المواقع المغناطيسي المصغر (Magnetic Mini GPS Tracker)",
    category: "Spy & Covert Gear",
    size: "4.2cm x 2.5cm x 1.6cm",
    description: "جهاز تتبع ورصد الموقع الجغرافي ذو الحجم المصغر ومحاط بجدار مغناطيسي قوي للالتصاق بالمركبات والأسطح المعدنية، يتضمن دعماً بنظام GPS وبطاقة SIM لنقل الإحداثيات.",
    confidence: 97.9,
    toolsFound: ["قاعدة مغناطيسية مغلفة بنبروديميوم", "مودم تحديد المواقع بالأقمار الصناعية GPS", "ميكروفون محيط مدمج"],
    hideCameraStatus: "🔴 تحذير تتبع: موجات تحديد المواقع نشطة. رصد انحراف مغناطيسي غير طبيعي بقيمة 4.2 microtesla على هيكل الحماية.",
    extraDetails: [
      { key: "GPS Precision Limit", value: "Within 5 to 10 meters radial distance" },
      { key: "Magnetic Pulling", value: "Super strong Neodymium base plates (Class N52)" },
      { key: "AGPS Functionality", value: "Assisted network locating enabled for tunnels" },
      { key: "Uplink Burst State", value: "Data transmission packets active every 30s" }
    ],
    imageUrl: "gps_tracker_bug",
    boundingBox: { x: 28, y: 32, w: 44, h: 36 }
  },
  {
    id: "spy_pir_sensor",
    name: "مستشعر حركة ممر مجهز بلقطة تجسس (Hidden Camera PIR Motion Sensor)",
    category: "Spy & Covert Gear",
    size: "8.5cm x 6.0cm x 4.0cm",
    description: "مستشعر حركة بالأشعة تحت الحمراء السلبية (PIR) يثبت على الجدران، ولكنه يضم في زاويته السفلى فتحة صغيرة للغاية بقطر 1.5 مم مجهزة بعدسة تجسس واسعة تبث الفيديو بدقة HDR للجناة.",
    confidence: 96.5,
    toolsFound: ["لوح انتشار العدسة المجهرية", "شريحة PIR السلبية لرصد الحرارة", "محول الجهد المستمر للتشغيل الدائم"],
    hideCameraStatus: "🔴 خطر أمني: تم تأكيد وجود عدسة التقاط سرية داخل غطاء مرشح مستشعر PIR البصري.",
    extraDetails: [
      { key: "PIR Detection Axis", value: "Passive Thermopile array active" },
      { key: "Covert Lens Position", value: "Concealed look-down orientation inside casing" },
      { key: "Transmitter Output", value: "WiFi client connection link active" },
      { key: "RF Signal Signature", value: "Continuous local ping broadcast" }
    ],
    imageUrl: "pir_spy_camera",
    boundingBox: { x: 25, y: 20, w: 50, h: 60 }
  },
  {
    id: "spy_cable_audio",
    name: "كابل شاحن مفخخ بمستمع بيئي (Covert USB Cable Audio Bug)",
    category: "Spy & Covert Gear",
    size: "100.0cm x 1.5cm x 0.8cm",
    description: "كابل شاحن هاتف عادي تماماً من نوع USB-C، لكن رأس المدخل الجانبي العريض يشتمل على شريحة تنصت صوتي مجهرية وبطاقة SIM مصغرة للمراقبة عن بعد بدون علم العميل.",
    confidence: 98.9,
    toolsFound: ["شريحة اتصال خلوي مجهرية داخل الرأس", "ميكروفون صوتي دقيق مطبوع", "خط تغذية طاقة مباشر من الشاحن"],
    hideCameraStatus: "🔴 تحذير تنصت: رصد دائرة إلكترونية متطورة مدمجة داخل رأس كابل الـ USB للشحن بدون مبرر تقني.",
    extraDetails: [
      { key: "Connector Model", value: "USB Type-C containing custom integrated SoC" },
      { key: "Voice Sensitivity", value: "Highly reactive voice activation trigger" },
      { key: "Power Input Source", value: "Takes power from active host port or charger" },
      { key: "Network Protocol", value: "2G GSM sub-band transmitter" }
    ],
    imageUrl: "spy_cable_audio_bug",
    boundingBox: { x: 10, y: 40, w: 80, h: 20 }
  },
  {
    id: "spy_teddy_eye",
    name: "دمية دب بعين مفخخة بكاميرا (Covert Teddy Bear Eye Camera)",
    category: "Spy & Covert Gear",
    size: "28.0cm x 22.0cm x 18.0cm",
    description: "دمية دب قطنية لطيفة تخفي في عينها اليسرى المصنوعة من البلاستيك اللامع معبراً بؤرياً مجهرياً بقطر 1 مم لعدسة كاميرا لاسلكية متطورة تلتقط تفاصيل الغرفة بالكامل وتعمل ببطارية مدمجة.",
    confidence: 99.1,
    toolsFound: ["فتحة بؤرة العين اليسرى المجهرية", "بطارية ليثيوم مخبأة بالقطن الداخلي", "لوحة تبدد حراري رقيقة للغاية"],
    hideCameraStatus: "🔴 خطر أمني حرج: تباين بؤري واضح في لمعان العين اليسرى للدمية. المسح الحراري يظهر بقعة دافئة في النصف الأيسر من الرأس.",
    extraDetails: [
      { key: "Glance Reflection Value", value: "88% mismatch in pupil optical absorption" },
      { key: "Wired Harness Path", value: "Cables routed from plastic eye to chest cavity" },
      { key: "Transmitter Signature", value: "Continuous Wi-Fi AP standard broadcast" },
      { key: "Aperture Check", value: "Verified 1.1mm lens aperture behind glass eye" }
    ],
    imageUrl: "teddy_bear_spy",
    boundingBox: { x: 25, y: 20, w: 50, h: 60 }
  },

  // ==========================================
  // CATEGORY 2: TV & Room Equipment
  // ==========================================
  {
    id: "room_smart_tv",
    name: "شاشة تلفاز ذكية رقيقة الحواف (65-inch Bezel-less OLED TV)",
    category: "TV & Room Equipment",
    size: "144.9cm x 83.2cm x 4.8cm",
    description: "شاشة تلفزيون ذكية رقيقة للغاية تعرض ألواناً غنية مبنية على خلايا الإضاءة الذاتية. تحتوي على لوحة حماية معدنية خلفية وتوصيلات كابلات وتوصيلات لاسلكية متعددة.",
    confidence: 99.8,
    toolsFound: ["لوحة OLED النشطة للإطلاق البصري", "منافذ التوصيل HDMI 2.1", "شريحة الاتصال بالشبكة اللاسلكية الذكية"],
    hideCameraStatus: "🟢 آمن: البنية سليمة وجوانب الحواف خالية بالكامل من أي كاميرات تجسس مجهرية. الانعكاس البصري طبيعي.",
    extraDetails: [
      { key: "Panel Technology", value: "Self-emitting subpixel OLED array system" },
      { key: "Physical Ports Available", value: "4x HDMI 2.1, 1x Optical Audio Out, 3x USB" },
      { key: "Active Power Consumption", value: "185 Watts active operating state" },
      { key: "Display Preset Profile", value: "Native Ultra HD 4K Color Profile Active" }
    ],
    imageUrl: "oled_tv",
    boundingBox: { x: 8, y: 12, w: 84, h: 70 }
  },
  {
    id: "room_router",
    name: "موزع شبكة إنترنت لاسلكي فائق السرعة (Wi-Fi 6 Gigabit Router)",
    category: "TV & Room Equipment",
    size: "26.0cm x 18.0cm x 22.0cm",
    description: "جهاز راوتر لاسلكي ذو لون أسود مطفي مزود بـ 4 هوائيات عالية الكسب وحجرات تبديد حراري ممتازة للبث اللاسلكي المستقر وإجراء عمليات المزامنة والربط السحابي الآمن.",
    confidence: 98.4,
    toolsFound: ["أعمدة الهوائيات الذكية Wi-Fi 6", "قنوات الشبكة السلكية RJ45 Gigabits", "أضواء مؤشر الحالة LED"],
    hideCameraStatus: "🟢 آمن: البث طبيعي ومعتمد لموجات الـ 2.4GHz والـ 5GHz ضمن المعايير الأمنية الآمنة، بدون وجود قنوات خفية.",
    extraDetails: [
      { key: "Transmit Radiating Power", value: "23 dBm active output signal strength" },
      { key: "Hardware Interfaces", value: "4x Gigabit Ethernet, 1x WAN, 1x USB 3.0" },
      { key: "Operating System Type", value: "Firmware encrypted secure Linux-based OS" },
      { key: "Core CPU Temperature", value: "44.5°C normal thermometric limits" }
    ],
    imageUrl: "wifi_router",
    boundingBox: { x: 20, y: 25, w: 60, h: 60 }
  },
  {
    id: "room_air_purifier",
    name: "منقي هواء ذكي متصل بالإنترنت (Smart Air Purifier IoT Device)",
    category: "TV & Room Equipment",
    size: "52.0cm x 24.0cm x 24.0cm",
    description: "منقي هواء ذكي برجي يحتوي على مرشح هواء ذي 3 طبقات وشاشة معلومات مدمجة ومكثفات هواء ذكية، آمن للاستخدام المنزلي وخالٍ من كاميرات التجسس.",
    confidence: 99.1,
    toolsFound: ["مرشح فئة HEPA H13 الصارم", "محسس جودة الهواء بالليزر الدقيق", "جهاز دفع وتدوير الهواء التوربيني"],
    hideCameraStatus: "🟢 آمن: المسح الضوئي يؤكد الشفافية الكاملة البصرية وعدم احتواء الشبكات الجانبية على عدسات كاميرا دقيقة.",
    extraDetails: [
      { key: "Filtration Rank", value: "HEPA H13 True particles catcher up to 99.97%" },
      { key: "Integrated Connections", value: "Built-in low energy WiFi controller card" },
      { key: "Clean Air Delivery Rate", value: "CADR rating 400 cubic meters per hour" },
      { key: "Core Acoustic Output", value: "Low decibel sleep mode down to 24 dB" }
    ],
    imageUrl: "air_purifier_room",
    boundingBox: { x: 28, y: 15, w: 44, h: 70 }
  },
  {
    id: "room_smart_lamp",
    name: "مصباح مكتب ذكي قابل للبرمجة (IoT Smart LED Desktop Lamp)",
    category: "TV & Room Equipment",
    size: "45.0cm x 15.0cm x 15.0cm",
    description: "مصباح مكتبي إلكتروني أنيق وهادئ يتم التحكم به عبر الإيماءات، ذو ذراع قابل للتدوير مجهزة بمصابيح LED مريحة وخافضة للإجهاد البصري ومستشعرات ذكية.",
    confidence: 98.7,
    toolsFound: ["لوحة صمام LED الموزعة المانعة للوهج", "قاعدة التحكم باللمس المستديرة", "منفذ شحن مخرجي للأجهزة ذكي"],
    hideCameraStatus: "🟢 آمن: البنية مأمونة ومثبتة ومستقرة، ولا توجد أي تعديلات إلكترونية مريبة داخل غطاء المصباح البلاستيكي.",
    extraDetails: [
      { key: "Luminous Density", value: "Maximum luminescence index up to 800 Lumens" },
      { key: "Color Temperatures", value: "Dynamic shift range from 2700K to 6500K" },
      { key: "Sensory Integration", value: "Ambient light automatic adaptation slider" },
      { key: "Power Voltage Metric", value: "DC 12V / 1.2A stabilized input pipeline" }
    ],
    imageUrl: "smart_lamp",
    boundingBox: { x: 30, y: 18, w: 40, h: 64 }
  },

  // ==========================================
  // CATEGORY 3: Objects & Tools
  // ==========================================
  {
    id: "tool_power_bank",
    name: "بنك طاقة محمول فائق القدرة وسريع الشحن (Ultra Power Bank 20000mAh)",
    category: "Objects & Tools",
    size: "15.0cm x 7.0cm x 2.5cm",
    description: "بطارية شحن محمولة للأجهزة الذكية مصنوعة من هيكل ألومنيوم مقاوم للصدمات، بسعة حقيقية 20,000 مللي أمبير تدعم تقنية الشحن السريع وحماية دوائر الطاقة الكهربائية.",
    confidence: 99.4,
    toolsFound: ["شاشة عرض مستوى الشحن الرقمي", "لوحة تبديل شحن ذكي (Power Delivery)", "خلايا ليثيوم أيون مكثفة متميزة"],
    hideCameraStatus: "🟢 آمن: تم مسح خلايا البطارية تماماً، واستهلاك الجهد طبيعي، ولا توجد أي تعديلات أو استقطاع لعدسات تجسس بالداخل.",
    extraDetails: [
      { key: "Battery Capacity", value: "20,000 Milliampere hour total charge capacity" },
      { key: "Max Wattage Output", value: "Dynamic Power Delivery output up to 65 Watts" },
      { key: "Chassis Material", value: "Fireproof anodized structural grade aluminum" },
      { key: "Protection Matrix", value: "Safety over-charge & over-heat auto trip" }
    ],
    imageUrl: "power_bank",
    boundingBox: { x: 30, y: 25, w: 40, h: 50 }
  },
  {
    id: "tool_camera_lens",
    name: "عدسة كاميرا احترافية فائقة السطوع (50mm f/1.2 Luxury DSLR Lens)",
    category: "Objects & Tools",
    size: "8.9cm x 8.9cm x 10.8cm",
    description: "عدسة فوتوغرافية بصرية احترافية ذات جودة تصنيع متينة وهيكل خارجي من مادة المغنيسيوم. تحتوي على حلقات ضبط تركيز بؤري وطلاء لحماية الأنماط الزجاجية المقعرة والمحدبة بالداخل.",
    confidence: 99.6,
    toolsFound: ["مجموعة زجاج عاكس متعدد الطبقات", "حلقة التركيز البؤري المطاطية المموجة", "محرك تركيز تلقائي صامت مدمج"],
    hideCameraStatus: "🟢 آمن: البصريات المسلحة بالعدسة سلبية مئة بالمئة للالتقاط العادي، وخالية تماماً من شرائح الإرسال والبطاريات الإضافية.",
    extraDetails: [
      { key: "Optical Arrangement", value: "15 refractive elements layered inside 9 groups" },
      { key: "Aperture Mechanisms", value: "9 circular electromagnetically controlled blades" },
      { key: "Filter Mount Thread", value: "77mm industry standard threading" },
      { key: "Max Light Intake", value: "Ultra-shallow f/1.2 depth field focus capacity" }
    ],
    imageUrl: "camera_lens",
    boundingBox: { x: 25, y: 24, w: 50, h: 52 }
  }
];

// List of words to generate 1000 realistic IoT and room scanning presets procedurally
const SPY_NOUNS = [
  "رأس جداري", "مشرط تشغيلي", "برغي من النحاس", "سماعة فحص مسار", "مفتاح طاقة", 
  "سلك توصيل ذكي", "شاحن مغناطيسي", "مستشعر رطوبة", "لوحة إنذار", "مرشح سقف", 
  "موزع إشارة", "مقوي شبكة", "إطار نظارة طبية", "جهاز تنصت عازل", "سوار رياضي"
];

const BRAND_CODES = ["S-100", "Pro-X", "Optima", "SecureMax", "Helix-IoT", "Aura-Shield", "Elite-V2", "Cypher"];

const CATEGORIES: ("Spy & Covert Gear" | "TV & Room Equipment" | "Objects & Tools" | "Animals & Creatures" | "Humans & Action")[] = [
  "Spy & Covert Gear", "TV & Room Equipment", "Objects & Tools", "Animals & Creatures", "Humans & Action"
];

// Helper to generate a realistic mock preset
function generateMockPreset(index: number): PresetScenario {
  const category = CATEGORIES[index % CATEGORIES.length];
  const code = BRAND_CODES[index % BRAND_CODES.length];
  const noun = SPY_NOUNS[index % SPY_NOUNS.length];
  
  const id = `proc_preset_${index}`;
  const isThreat = category === "Spy & Covert Gear";
  
  const widthVal = (2 + (index % 120)) / 10;
  const heightVal = (2 + (index % 95)) / 10;
  const depthVal = (1 + (index % 40)) / 10;
  const size = `${widthVal.toFixed(1)}cm x ${heightVal.toFixed(1)}cm x ${depthVal.toFixed(1)}cm`;

  const confidence = parseFloat((84.5 + (index % 150) / 10).toFixed(1));

  let name = "";
  let description = "";
  let hideCameraStatus = "";
  let toolsFound: string[] = [];

  if (category === "Spy & Covert Gear") {
    name = `جهاز رصد مجهري ${noun} إصدار ${code}`;
    description = `معزز لمراقبة ورصد الأبعاد البيئية، يحتوي داخلياً على ناقل إشارة لاسلكية ترددي دقيق طراز ${code} يعمل بنطاق بث دوري عريض ونطاق طاقة LiPo خارق.`;
    hideCameraStatus = `🔴 خطر أمني مرتفع: تم العثور على ذراع بث لاسلكي مخفي في البنية ومستقبل عدسة مجهرية بقطر ${(0.8 + (index % 12)/10).toFixed(1)} ملم!`;
    toolsFound = ["محلل أشعة مجهري سري", "باعث تذبذب ترددي لاسلكي", "مكثف طاقة LiPo مستديم"];
  } else if (category === "TV & Room Equipment") {
    name = `تجهيز غرفة ذكي ${noun} طراز ${code}`;
    description = `أداة ذكية متعددة الاستخدامات لتنظيم درجات التهوية والإضاءة المنزلية المتلائمة مع شبكات الاستشعار الذكية السليمة.`;
    hideCameraStatus = "🟢 آمن: تم التحقق من المكونات الكهرومغناطيسية والبصرية والعلبة الخارجية نظيفة وسلبية تماماً.";
    toolsFound = ["حساس الاستنشاق البيئي", "دارة قياس درجة الفولت"];
  } else if (category === "Objects & Tools") {
    name = `أداة فحص وهندسة ${noun} فئة ${code}`;
    description = `مستلزم محكم الاستخدام وعالي المتانة للقياسات الهندسية الدقيقة ويدعم حماية الموصلات وامتصاص الصدمات.`;
    hideCameraStatus = "🟢 آمن: البنية متماسكة والمسح الراداري يؤكد عدم وجود أي إشارات تجسس نشطة.";
    toolsFound = ["شريحة توزيع الإشارة", "خط حماية الفولت المتناوب"];
  } else if (category === "Animals & Creatures") {
    name = `${noun === "مستشعر رطوبة" ? "طائر معبر" : noun} أليف حيواني سليم`;
    description = "كائن حيواني طبيعي ذو إشعاع حراري حيوي معتاد ونظيف، يخلو تماماً من المكونات الاصطناعية أو العدسات المجهرية التلصصية.";
    hideCameraStatus = "🟢 تشخيص حيوي: كائن حي متفاعل سليم درجة حرارته طبيعية ولا يحمل رقاقات تتبع مزروعة خبيثة.";
    toolsFound = ["استجابة بصرية طبيعية", "توزيع حراري طبيعي"];
  } else {
    name = `هدف بشري طبيعي بـ ${noun} فني`;
    description = "كائن بشري ديناميكي مستقر يتابع ممارسة أنشطة المكتبيين اليومية سليم المعايير الحيوية.";
    hideCameraStatus = "🟢 كائن طبيعي: تم مسح حيز التواجد وتوزيع درجات حرارة الأطراف المعبر ينبئ بسلامة تامة.";
    toolsFound = ["توزيع هيكلي سليم", "نبضات قلب طبيعية"];
  }

  return {
    id,
    name,
    category,
    size,
    description,
    confidence,
    toolsFound,
    hideCameraStatus,
    extraDetails: [
      { key: "Protocol Std", value: `IEEE 802.11b/n/ax-${index}` },
      { key: "Thermal Footprint", value: `+${(1.2 + (index % 4)).toFixed(1)}°C delta max` },
      { key: "Operational Peak", value: `${(12 + (index % 120))}mW active draw` },
      { key: "Spectral Code", value: `IR-CLASS-${index % 5}` }
    ],
    imageUrl: isThreat ? "spy_gear_covert" : "standard_fixture_safe",
    boundingBox: {
      x: 15 + (index % 50),
      y: 15 + (index % 45),
      w: 30 + (index % 25),
      h: 30 + (index % 30)
    }
  };
}

// Generate procedurally generated items to achieve exactly 1000 items
const GENERATED_PRESETS: PresetScenario[] = Array.from({ length: 1000 - CORE_PRESETS.length }, (_, k) => {
  return generateMockPreset(k);
});

// Full combined list of exactly 1000 entries
export const PRESET_SCENARIOS: PresetScenario[] = [...CORE_PRESETS, ...GENERATED_PRESETS];
