import fs from 'fs';

let content = fs.readFileSync('server.ts', 'utf8');

let lines = content.split('\n');

let startIdx = lines.findIndex(l => l.includes('function generateSimulatedAssistantResponse(question: string'));
let endIdx = lines.findIndex((l, i) => i > startIdx && l.startsWith('}'));

if (startIdx !== -1 && endIdx !== -1) {
    let replacedFunc = `function generateSimulatedAssistantResponse(question: string, scanContext: any, isDemandBackoff: boolean = false) {
  const qLower = question.toLowerCase();
  
  let responseText = "";
  let preface = "";
  if (isDemandBackoff) {
    preface = \`⚠️ [ملاحظة: خوادم الذكاء الاصطناعي من قوقل تواجه ضغطاً مؤقتاً عالياً حالياً. لقد قمنا بتفعيل نظام كاشف جيمني الذكي المستقل محلياً لخدمتك فوراً دون انقطاع!] \\n\\n\`;
  } else {
    preface = \`⚡ [نظام المساعد الذكي المستقل النشط لـ AI Vision Lite] \\n\\n\`;
  }

  let body = "";
  
  if (qLower.includes("camera") || qLower.includes("spy") || qLower.includes("كاميرا") || qLower.includes("تجسس") || qLower.includes("مخفي")) {
    body = \`[مستشار الفحص الطيفي للكشف عن الكاميرات الخفية]
1. **الكاميرات المدمجة بالأجهزة والشواحن**:
   - غالبية كاميرات التجسس تأتي مدمجة في أفياش الشواحن USB وساعات المحاذاة وأجهزة كشف الدخان وأجهزة التكييف المعدلة.
   - تعتمد على عدسة زجاجية دقيقة للغاية وحرجة بقطر يقل عن 1ملم.
2. **طريقة الكشف اليدوية والتكنولوجية**:
   - استخدم ميزة **"الرؤية الليلية بالأشعة تحت الحمراء المتكاملة"** بالتطبيق. عند إطفاء أضواء الغرفة، ستكشف الكاميرا انعكاس وهج العدسة (عدسة الكاميرا تعكس الأحمر/البنفسجي).
   - ابحث عن إشارات واي فاي غريبة قريبة مثل "Cam-xxxx" أو "IP-xxxxx" أو "covert".
   - الفحص الميكانيكي: افحص أي فتحات غير مبررة في البلاستيك الخارجي للشواحن.\`;
  } else if (qLower.includes("translate") || qLower.includes("ترجم") || qLower.includes("عربي") || qLower.includes("نجليزي")) {
    body = \`[مساعد الترجمة الفوري الاحترافي]
يمكنني مساعدة ترجمة كافة التقارير الفنية للكشاف واللوحات فوراً.
على سبيل المثال، ترجمة العبقرية التقنية لسلامة الأجهزة:
- "Threat scan verified. No electromagnetic anomalies or rogue signals detected in device core chips."
- **الترجمة العربية المعتمدة**: "تم التحقق من فحص التهديدات بالكامل. لم يتم الكشف عن أي شذوذ كهرومغناطيسي أو إشارات مارقة في رقائق الأجهزة الأساسية للوريد."\`;
  } else {
    body = \`مرحبًا بك! لقد قمت بمعالجة استفسارك الذكي بنجاح.
- يتيح لك نظام الكشف والتحليل تفقد محتويات الغرف، الأجهزة والمكيفات والشاشات، ومقتنيات الأنيمي، وفهم خصائصها بالعربية فوراً.
- يمكنك الكشف عن الثغرات وكاميرات التجسس المخفية يدوياً وآلياً بواسطة أنظمة الذكاء الاصطناعي وبث الترددات.
ما هي التفاصيل التقنية الأخرى التي ترغب في استعراضها؟\`;
  }

  return preface + body;
}`;

    lines.splice(startIdx, endIdx - startIdx + 1, replacedFunc);
    fs.writeFileSync('server.ts', lines.join('\n'), 'utf8');
    console.log('Fixed function');
} else {
    console.log('Function not found!');
}
