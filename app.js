/* =====================================================
   PhysioMind AI — app.js
   Single-file SPA logic: state, translations, rendering
   ===================================================== */

'use strict';

/* ══════════════════════════════════════════════════
   TRANSLATIONS (English & Hindi)
══════════════════════════════════════════════════ */
const T = {
  en: {
    appName: 'PhysioMind AI',
    langToggle: '🇮🇳 Hindi',
    authBtn: 'Login / Sign Up',
    authLogout: 'Logout',
    navHome: 'Home', navAssist: 'AI Assistant', navEx: 'Exercises', navPlan: 'My Plan', navAnalytics: 'Analytics',
    heroBadge: '🇮🇳 English + हिंदी · Real-time Pose AI',
    heroTitle: 'Recover faster with AI-guided physiotherapy',
    heroSub: 'Multilingual symptom analysis, personalized rehab plans, and real-time posture correction using your camera — in English & Hindi.',
    heroCta: 'Start Assessment →',
    heroSec: 'Explore Exercises',
    stat1: 'Pose keypoints tracked', stat2: 'Guided exercises', stat3: 'Languages supported',
    liveBadge: 'AI Pose Tracking Live',
    featTag: 'Full Pipeline',
    featTitle: 'A Complete AI Physiotherapy Pipeline',
    featDesc: 'From input to recovery — NLP, computer vision & healthcare knowledge combined.',
    features: [
      { icon: '🗣️', title: 'Multilingual Intake',   desc: 'Describe symptoms by text or voice in English & Hindi.' },
      { icon: '📄', title: 'Medical Report OCR',     desc: 'Upload MRI/X-ray reports; AI extracts findings automatically.' },
      { icon: '🧠', title: 'AI Diagnosis',            desc: 'Infers likely condition and confidence score from your inputs.' },
      { icon: '🏋️', title: 'Personalized Plans',     desc: 'Tailored exercise, diet & daily routine for your recovery.' },
      { icon: '🎥', title: 'Live Pose Coaching',      desc: 'Camera-based posture tracking with instant corrections.' },
      { icon: '📊', title: 'Recovery Analytics',      desc: 'Track reps, range of motion & quality scores over time.' },
    ],
    demoTitle: 'Guided Video + AI Posture Monitoring',
    demoDesc: 'Each prescribed exercise includes a demo video. Your front camera captures movement, AI compares live pose, counts reps, and gives instant voice/text corrections — pausing for unsafe movements.',
    demoBullets: ['Detects incorrect posture in real-time', 'Automatic repetition counting', 'Pauses on unsafe movement', 'Stores exercise quality scores'],
    demoCta: 'Try Live Pose Demo →',
    stepsTitle: 'How It Works',
    steps: [
      { title: 'Describe Symptoms',  desc: 'Type, speak, or upload a report' },
      { title: 'Get AI Diagnosis',   desc: 'Condition & advice instantly' },
      { title: 'Generate Plan',      desc: 'Exercise + Diet + Routine' },
      { title: 'Live Practice',      desc: 'Camera corrects your posture' },
      { title: 'Track Progress',     desc: 'See recovery on your dashboard' },
    ],
    ctaTitle: 'Start Your Recovery Today',
    ctaDesc:  'Sign up free and get your first AI assessment in minutes.',
    ctaBtn:   'Start Assessment →',
    assistTitle: 'AI Physio Assistant',
    assistSub:   'Describe symptoms via text, voice, or upload a medical report',
    chatEmptyMsg: 'Type or speak your symptoms below to get instant AI analysis.',
    chatPlaceholder: 'Type your symptoms…',
    sendBtn: 'Send',
    diagLabel: 'AI Diagnosis',
    diagPlaceholder: 'Your diagnosis will appear here after describing your symptoms.',
    likelyCondition: 'Likely condition',
    confidence: 'Confidence',
    symptoms: 'Detected symptoms',
    genPlanBtn: 'Generate Personalized Plan',
    disclaimer: 'AI suggestions do not replace professional medical advice. Consult a licensed physiotherapist.',
    chips: ['I have lower back pain', 'My knee is swollen', 'Stiffness in my shoulder', 'Neck pain and headache'],
    exTitle: 'Guided Exercise Library',
    exSub:   'Practice each exercise with live AI posture monitoring',
    startSession: 'Start Session ▶',
    cats: [
      { key: 'all',      label: '🌐 All' },
      { key: 'back',     label: '🔙 Back' },
      { key: 'knee',     label: '🦵 Knee' },
      { key: 'hip',      label: '🦴 Hip' },
      { key: 'shoulder', label: '💪 Shoulder' },
      { key: 'neck',     label: '🧍 Neck' },
      { key: 'posture',  label: '🧘 Posture' },
    ],
    planTitle: 'My Recovery Plan',
    planNone:  'No plan yet. Run an assessment with the AI Assistant first.',
    planNoneBtn: 'Start Assessment',
    planCondition: 'Condition',
    planGenNote: 'AI-generated recovery roadmap tailored to your diagnosis.',
    planTabEx: '🏋️ Exercise',
    planTabDiet: '🥗 Diet',
    planTabRoutine: '🗓️ Routine',
    startBtn: 'Start ▶',
    analyticsTitle: 'Recovery Analytics',
    analyticsSub:   'Your digital biomarkers over time',
    aiSummaryLabel: 'AI Progress Summary',
    qualityTrend: 'Form Quality Trend',
    romTrend:     'Range of Motion (°)',
    errorsTitle:  'Common Posture Errors',
    historyTitle: 'Session History',
    noData: 'No sessions recorded yet. Complete an exercise session to start tracking.',
    sessionReps: 'Reps', sessionQual: 'Form Quality', sessionTime: 'Time',
    hudInstruct: 'Position yourself in front of the camera. Follow along and maintain proper form throughout.',
    footerDisclaimer: 'AI advice is for informational guidance only. Always consult a professional.',
  },
  hi: {
    appName: 'फिजियोमाइंड AI',
    langToggle: '🇬🇧 English',
    authBtn: 'लॉगिन / साइन अप',
    authLogout: 'लॉगआउट',
    navHome: 'मुख्य पृष्ठ', navAssist: 'AI सहायक', navEx: 'व्यायाम', navPlan: 'मेरी योजना', navAnalytics: 'विश्लेषण',
    heroBadge: '🇮🇳 English + हिंदी · Real-time Pose AI',
    heroTitle: 'AI-निर्देशित फिजियोथेरेपी के साथ तेज़ी से ठीक हों',
    heroSub: 'बहुभाषी लक्षण विश्लेषण, व्यक्तिगत पुनर्वास योजनाएँ, और आपके कैमरे से रीयल-टाइम मुद्रा सुधार — अंग्रेज़ी और हिंदी में।',
    heroCta: 'मूल्यांकन शुरू करें →',
    heroSec: 'व्यायाम देखें',
    stat1: 'पोज़ पॉइंट्स ट्रैकिंग', stat2: 'निर्देशित व्यायाम', stat3: 'भाषाओं में समर्थन',
    liveBadge: 'AI पोज़ ट्रैकिंग लाइव',
    featTag: 'पूर्ण पाइपलाइन',
    featTitle: 'पूर्ण AI फिजियोथेरेपी पाइपलाइन',
    featDesc: 'इनपुट से लेकर रिकवरी तक — NLP, कंप्यूटर विज़न और हेल्थकेयर ज्ञान एक साथ।',
    features: [
      { icon: '🗣️', title: 'बहुभाषी इनपुट',    desc: 'अंग्रेज़ी और हिंदी में टेक्स्ट या आवाज़ से लक्षण बताएं।' },
      { icon: '📄', title: 'रिपोर्ट OCR',        desc: 'MRI/X-ray रिपोर्ट अपलोड करें; AI निष्कर्ष निकालता है।' },
      { icon: '🧠', title: 'AI निदान',            desc: 'आपके इनपुट से संभावित स्थिति और विश्वास का अनुमान।' },
      { icon: '🏋️', title: 'व्यक्तिगत योजनाएं', desc: 'आपकी रिकवरी के लिए व्यायाम, आहार और दिनचर्या।' },
      { icon: '🎥', title: 'लाइव पोज़ कोचिंग',   desc: 'कैमरा-आधारित मुद्रा ट्रैकिंग और तुरंत सुधार।' },
      { icon: '📊', title: 'रिकवरी विश्लेषण',    desc: 'समय के साथ दोहराव, गति और गुणवत्ता स्कोर ट्रैक करें।' },
    ],
    demoTitle: 'गाइडेड वीडियो + AI मुद्रा निगरानी',
    demoDesc: 'प्रत्येक निर्धारित व्यायाम में एक डेमो वीडियो शामिल है। फ्रंट कैमरा गति कैप्चर करता है, AI लाइव मुद्रा की तुलना करता है, दोहराव गिनता है।',
    demoBullets: ['रीयल-टाइम में गलत मुद्रा पहचानता है', 'दोहराव की स्वचालित गिनती', 'असुरक्षित गति पर रुकता है', 'गुणवत्ता स्कोर सहेजता है'],
    demoCta: 'लाइव पोज़ डेमो आज़माएं →',
    stepsTitle: 'यह कैसे काम करता है',
    steps: [
      { title: 'लक्षण बताएं',    desc: 'टेक्स्ट, आवाज़ या रिपोर्ट अपलोड करें' },
      { title: 'AI निदान पाएं',  desc: 'स्थिति और सुझाव तुरंत' },
      { title: 'योजना बनाएं',    desc: 'व्यायाम + आहार + दिनचर्या' },
      { title: 'लाइव अभ्यास',    desc: 'कैमरा मुद्रा सुधारता है' },
      { title: 'प्रगति देखें',    desc: 'डैशबोर्ड पर सुधार' },
    ],
    ctaTitle: 'आज ही अपनी रिकवरी शुरू करें',
    ctaDesc:  'मुफ़्त में साइन अप करें और मिनटों में पहला AI मूल्यांकन पाएं।',
    ctaBtn:   'मूल्यांकन शुरू करें →',
    assistTitle: 'AI फिजियो सहायक',
    assistSub:   'टेक्स्ट, आवाज़ या रिपोर्ट से अपने लक्षण बताएं',
    chatEmptyMsg: 'नीचे लिखकर या बोलकर अपने लक्षण बताएं।',
    chatPlaceholder: 'अपने लक्षण लिखें…',
    sendBtn: 'भेजें',
    diagLabel: 'AI निदान',
    diagPlaceholder: 'लक्षण बताने के बाद आपका निदान यहां दिखाई देगा।',
    likelyCondition: 'संभावित स्थिति',
    confidence: 'विश्वास',
    symptoms: 'पहचाने गए लक्षण',
    genPlanBtn: 'व्यक्तिगत योजना बनाएं',
    disclaimer: 'AI सुझाव पेशेवर चिकित्सा सलाह का विकल्प नहीं हैं। लाइसेंस प्राप्त फिजियोथेरेपिस्ट से परामर्श करें।',
    chips: ['मुझे कमर में दर्द है', 'घुटने में सूजन है', 'कंधे में अकड़न है', 'गर्दन में दर्द'],
    exTitle: 'गाइडेड व्यायाम लाइब्रेरी',
    exSub:   'AI मुद्रा निगरानी के साथ प्रत्येक व्यायाम का अभ्यास करें',
    startSession: 'सत्र शुरू करें ▶',
    cats: [
      { key: 'all',      label: '🌐 सभी' },
      { key: 'back',     label: '🔙 कमर' },
      { key: 'knee',     label: '🦵 घुटना' },
      { key: 'hip',      label: '🦴 कूल्हा' },
      { key: 'shoulder', label: '💪 कंधा' },
      { key: 'neck',     label: '🧍 गर्दन' },
      { key: 'posture',  label: '🧘 मुद्रा' },
    ],
    planTitle: 'मेरी रिकवरी योजना',
    planNone:  'अभी कोई योजना नहीं। AI सहायक के साथ मूल्यांकन करें।',
    planNoneBtn: 'मूल्यांकन शुरू करें',
    planCondition: 'स्थिति',
    planGenNote: 'AI द्वारा आपके निदान के आधार पर तैयार किया गया।',
    planTabEx: '🏋️ व्यायाम',
    planTabDiet: '🥗 आहार',
    planTabRoutine: '🗓️ दिनचर्या',
    startBtn: 'शुरू ▶',
    analyticsTitle: 'रिकवरी विश्लेषण',
    analyticsSub:   'समय के साथ आपके डिजिटल बायोमार्कर',
    aiSummaryLabel: 'AI प्रगति सारांश',
    qualityTrend: 'फॉर्म गुणवत्ता प्रवृत्ति',
    romTrend:     'गति सीमा (°)',
    errorsTitle:  'सामान्य मुद्रा त्रुटियाँ',
    historyTitle: 'सत्र इतिहास',
    noData: 'अभी कोई डेटा नहीं। व्यायाम सत्र पूरा करें।',
    sessionReps: 'दोहराव', sessionQual: 'फॉर्म गुणवत्ता', sessionTime: 'समय',
    hudInstruct: 'कैमरे के सामने खड़े हों और सही मुद्रा में व्यायाम करें।',
    footerDisclaimer: 'AI सलाह केवल जानकारी के लिए है। हमेशा विशेषज्ञ से परामर्श लें।',
  }
};

/* ══════════════════════════════════════════════════
   EXERCISE DATA
   Loaded from the backend catalogue. Kept in a module-level cache so views
   can render synchronously after the first fetch.
══════════════════════════════════════════════════ */
let EXERCISES = [];

async function loadExercises() {
  try {
    const data = await API.exercises();
    EXERCISES = data.items;
    // Keep the landing-page count honest as the catalogue grows.
    const counter = $('statExCount');
    if (counter) counter.textContent = EXERCISES.length;
  } catch (err) {
    EXERCISES = [];
    console.error('Could not load exercises:', err.message);
  }
  return EXERCISES;
}

/* ══════════════════════════════════════════════════
   STATE
══════════════════════════════════════════════════ */
let lang = localStorage.getItem('pm_lang') || 'en';
let user = null;                 // resolved from the server via the stored token
let currentView = 'landing';
let currentCat  = 'all';
let currentDiag = null;
let activePlan  = null;
let authMode    = 'login';
let analytics   = null;          // last /api/analytics payload

// Live pose session handle (from pose.js) plus the exercise it belongs to.
let liveSession = null;
let liveExercise = null;

/* ══════════════════════════════════════════════════
   HELPERS
══════════════════════════════════════════════════ */
const t  = () => T[lang];
const $  = id => document.getElementById(id);
const set = (id, txt) => { const el=$(id); if(el) el.textContent = txt; };
const html = (id, h) => { const el=$(id); if(el) el.innerHTML = h; };

/** Escape anything that came from a user or the network before it touches innerHTML. */
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => (
  { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
));

/** Pick the field for the active language, falling back to English. */
const tr = (obj, field) => (lang === 'hi' && obj[field + '_hi']) || obj[field] || '';

function toast(message, tone = 'error') {
  const el = $('toast');
  if (!el) return;
  el.textContent = message;
  el.className = 'toast ' + tone + ' show';
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => { el.className = 'toast ' + tone; }, 4200);
}

/* ══════════════════════════════════════════════════
   INIT
══════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', async () => {
  bindEvents();
  renderAll();

  // Restore the signed-in user from the stored token, then load the catalogue.
  // Both are independent, so let them run together.
  const [me] = await Promise.all([
    API.isLoggedIn() ? API.me().catch(() => null) : Promise.resolve(null),
    loadExercises(),
  ]);
  user = me;
  if (!user) API.logout();          // token was rejected or expired

  renderAll();
  if (user) refreshPlan();
});

/** Pull the active plan so the My Plan tab is populated on load. */
async function refreshPlan() {
  try {
    const plan = await API.activePlan();
    activePlan = plan.content;
    activePlan.id = plan.id;
  } catch {
    activePlan = null;             // 404 simply means no plan generated yet
  }
  if (currentView === 'plan') renderPlan();
}

function bindEvents() {
  // Nav links
  document.querySelectorAll('.nav-link').forEach(btn => {
    btn.addEventListener('click', () => showView(btn.dataset.view));
  });
  // Language toggle
  $('langBtn').addEventListener('click', () => {
    lang = lang === 'en' ? 'hi' : 'en';
    localStorage.setItem('pm_lang', lang);
    renderAll();
  });
  // Auth
  $('authBtn').addEventListener('click', () => {
    if (user) { logout(); } else { openAuth(); }
  });
  // Chat send
  $('sendBtn').addEventListener('click', sendMessage);
  $('chatInput').addEventListener('keydown', e => { if(e.key==='Enter') sendMessage(); });
  // File attach
  $('attachBtn').addEventListener('click', () => $('fileInput').click());
  $('fileInput').addEventListener('change', handleFile);
  // Mic
  $('micBtn').addEventListener('click', handleMic);
}

/* ══════════════════════════════════════════════════
   VIEW SWITCHING
══════════════════════════════════════════════════ */
function showView(name) {
  currentView = name;
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  const el = $('view-' + name);
  if (el) el.classList.add('active');

  document.querySelectorAll('.nav-link').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.view === name);
  });

  window.scrollTo({ top: 0, behavior: 'smooth' });

  if (name === 'exercises') renderExercises();
  if (name === 'plan')      renderPlan();
  if (name === 'analytics') renderAnalytics();
}

/* ══════════════════════════════════════════════════
   RENDER ALL (called on init + lang switch)
══════════════════════════════════════════════════ */
function renderAll() {
  const d = t();
  // Nav
  set('appName',    d.appName);
  set('langBtn',    d.langToggle);
  set('authBtn',    user ? `${d.authLogout} (${user.name.split(' ')[0]})` : d.authBtn);
  $('authBtn').className = user ? 'btn btn-sm btn-outline' : 'btn btn-sm btn-primary';
  document.querySelectorAll('.nav-link').forEach(btn => {
    const map = { landing: d.navHome, assistant: d.navAssist, exercises: d.navEx, plan: d.navPlan, analytics: d.navAnalytics };
    btn.textContent = map[btn.dataset.view] || btn.textContent;
  });
  // Hero
  set('heroBadge',  d.heroBadge);
  set('heroTitle',  d.heroTitle);
  set('heroSub',    d.heroSub);
  set('heroCta',    d.heroCta);
  set('heroSec',    d.heroSec);
  set('stat1',      d.stat1);
  set('stat2',      d.stat2);
  set('stat3',      d.stat3);
  set('liveBadge',  d.liveBadge);
  // Features section
  set('featTag',    d.featTag);
  set('featTitle',  d.featTitle);
  set('featDesc',   d.featDesc);
  html('featuresGrid', d.features.map(f => `
    <div class="feat-card">
      <div class="feat-icon">${f.icon}</div>
      <div class="feat-title">${f.title}</div>
      <div class="feat-desc">${f.desc}</div>
    </div>`).join(''));
  // Demo
  set('demoTitle',  d.demoTitle);
  set('demoDesc',   d.demoDesc);
  set('demoCta',    d.demoCta);
  html('demoBullets', d.demoBullets.map(b => `
    <li class="demo-bullet"><span class="check-icon">✓</span>${b}</li>`).join(''));
  // Steps
  set('stepsTitle', d.stepsTitle);
  html('stepsGrid', d.steps.map((s,i) => `
    <div class="step-card">
      <div class="step-num">${i+1}</div>
      <div class="step-title">${s.title}</div>
      <div class="step-desc">${s.desc}</div>
    </div>`).join(''));
  // CTA
  set('ctaTitle', d.ctaTitle);
  set('ctaDesc',  d.ctaDesc);
  set('ctaBtn',   d.ctaBtn);
  // Assistant
  set('assistTitle',    d.assistTitle);
  set('assistSub',      d.assistSub);
  set('chatEmptyMsg',   d.chatEmptyMsg);
  $('chatInput').placeholder = d.chatPlaceholder;
  set('sendBtn',        d.sendBtn);
  set('diagLabel',      d.diagLabel);
  set('diagPlaceholder',d.diagPlaceholder);
  set('genPlanBtn',     d.genPlanBtn);
  set('disclaimerText', d.disclaimer);
  // Chips
  // Bind the handler rather than interpolating the text into an onclick
  // attribute - the Hindi chips contain characters that break inline quoting.
  const chipsRow = $('chipsRow');
  chipsRow.innerHTML = '';
  d.chips.forEach(text => {
    const chip = document.createElement('button');
    chip.className = 'chip';
    chip.textContent = text;
    chip.addEventListener('click', () => quickSend(text));
    chipsRow.appendChild(chip);
  });
  // Exercises
  set('exTitle', d.exTitle);
  set('exSub',   d.exSub);
  // Category bar
  html('catBar', d.cats.map(c => `
    <button class="cat-btn${c.key===currentCat?' active':''}" onclick="setCat('${c.key}')">${c.label}</button>`).join(''));
  // Plan + Analytics + session modal strings
  set('planTitle',      d.planTitle);
  set('analyticsTitle', d.analyticsTitle);
  set('analyticsSub',   d.analyticsSub);
  set('hudRepLabel',    d.sessionReps);
  set('hudQualLabel',   d.sessionQual);
  set('hudTimeLabel',   d.sessionTime);
  set('sessionInstructions', d.hudInstruct);
  set('footerDisclaimer', d.footerDisclaimer);
  // Re-render diag card if exists
  if (currentDiag) renderDiagCard();
  // Re-render current view
  if (currentView === 'exercises') renderExercises();
  if (currentView === 'plan')      renderPlan();
  if (currentView === 'analytics') renderAnalytics();
}

/* ══════════════════════════════════════════════════
   AI ASSISTANT CHAT
══════════════════════════════════════════════════ */
async function sendMessage() {
  const input = $('chatInput');
  const text = input.value.trim();
  if (!text) return;
  input.value = '';

  const empty = $('chatEmpty');
  if (empty) empty.style.display = 'none';

  const box = $('chatMessages');
  box.appendChild(makeUserBubble(text));
  box.scrollTop = box.scrollHeight;

  const typing = makeBotBubble(
    '<div class="typing-dots"><span></span><span></span><span></span></div>'
  );
  typing.id = 'typingBubble';
  box.appendChild(typing);
  box.scrollTop = box.scrollHeight;

  let result;
  try {
    result = await API.assess(text, lang);
  } catch (err) {
    $('typingBubble')?.remove();
    box.appendChild(makeBotBubble(esc(err.message)));
    box.scrollTop = box.scrollHeight;
    toast(err.message);
    return;
  }

  $('typingBubble')?.remove();
  currentDiag = result;

  // Red flags come first and are visually distinct - they mean "see a
  // clinician", not "here is your exercise plan".
  if (result.red_flags && result.red_flags.length) {
    box.appendChild(makeBotBubble(
      `<strong>${lang === 'hi' ? 'चेतावनी' : 'Warning'}</strong><ul class="flag-list">` +
      result.red_flags.map(f => `<li>${esc(f)}</li>`).join('') + '</ul>'
    ));
  }

  box.appendChild(makeBotBubble(esc(result.reply)));
  box.scrollTop = box.scrollHeight;

  renderDiagCard();
  speak(result.reply);
}

function speak(text) {
  if (!('speechSynthesis' in window)) return;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = lang === 'hi' ? 'hi-IN' : 'en-US';
  speechSynthesis.speak(utterance);
}

/** User text is never trusted as markup - it goes in as text, not HTML. */
function makeUserBubble(text) {
  const div = document.createElement('div');
  div.className = 'bubble user';
  div.textContent = text;
  return div;
}

/** Callers must escape any interpolated value before passing it here. */
function makeBotBubble(safeHtml) {
  const div = document.createElement('div');
  div.className = 'bubble bot';
  div.innerHTML = safeHtml;
  return div;
}

function quickSend(text) {
  $('chatInput').value = text;
  sendMessage();
}

function renderDiagCard() {
  if (!currentDiag) return;
  const d = t();
  const name = tr(currentDiag, 'condition');
  const syms = (lang === 'hi' ? currentDiag.symptoms_hi : currentDiag.symptoms) || [];
  const rec  = tr(currentDiag, 'advice');
  const pct  = Math.round(currentDiag.confidence * 100);

  // A low-confidence result must look low-confidence, not authoritative.
  const barColor = currentDiag.is_confident ? '' : 'background:#f59e0b';

  const alternatives = (currentDiag.alternatives || []).length ? `
    <div class="alt-block">
      <div class="alt-label">${lang === 'hi' ? 'अन्य संभावनाएँ' : 'Also considered'}</div>
      ${currentDiag.alternatives.map(a =>
        `<span class="s-tag">${esc(lang === 'hi' ? a.condition_hi : a.condition)}</span>`
      ).join('')}
    </div>` : '';

  html('diagContent', `
    <div class="diag-gradient-card">
      <div class="diag-condition-lbl">${esc(d.likelyCondition)}</div>
      <div class="diag-condition-name">${esc(name)}</div>
      <div class="progress-wrap">
        <div class="progress-row">
          <span>${esc(d.confidence)}</span><span>${pct}%</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill" style="width:${pct}%;${barColor}"></div>
        </div>
      </div>
    </div>
    <div style="margin-top:.9rem">
      <div style="font-size:.72rem;font-weight:700;color:var(--slate-500);margin-bottom:.35rem">${esc(d.symptoms)}</div>
      <div class="symptom-tags">${syms.map(s => `<span class="s-tag">${esc(s)}</span>`).join('')}</div>
    </div>
    <p class="diag-rec">${esc(rec)}</p>
    ${alternatives}
  `);

  set('genPlanBtn', d.genPlanBtn);
  // Nothing to plan from until the diagnosis is solid enough to act on.
  $('genPlanBtn').style.display = currentDiag.is_confident ? 'block' : 'none';
}

function handleMic() {
  const btn = $('micBtn');
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    toast(lang === 'hi'
      ? 'यह ब्राउज़र आवाज़ पहचान का समर्थन नहीं करता। कृपया टाइप करें।'
      : 'This browser does not support speech recognition. Please type instead.');
    return;
  }
  const rec = new SR();
  rec.lang = lang === 'hi' ? 'hi-IN' : 'en-US';
  btn.classList.add('recording');
  rec.onresult = e => { $('chatInput').value = e.results[0][0].transcript; };
  rec.onerror  = e => {
    toast(e.error === 'not-allowed'
      ? (lang === 'hi' ? 'माइक्रोफ़ोन की अनुमति नहीं मिली।'
                       : 'Microphone permission was denied.')
      : (lang === 'hi' ? 'आवाज़ पहचान विफल रही।' : 'Speech recognition failed.'));
  };
  rec.onend = () => btn.classList.remove('recording');
  rec.start();
}

async function handleFile(e) {
  const file = e.target.files[0];
  if (!file) return;
  e.target.value = '';                      // allow re-picking the same file

  const status = $('ocrStatus');
  status.style.display = 'block';
  status.className = 'ocr-status';
  status.textContent = `📄 ${file.name} — ${lang === 'hi' ? 'अपलोड हो रहा है…' : 'uploading…'}`;

  try {
    const result = await API.uploadReport(file);
    if (!result.ok) {
      // Say what actually went wrong instead of inventing findings.
      status.className = 'ocr-status warn';
      status.textContent = `⚠ ${file.name} — ${result.message}`;
      return;
    }
    status.className = 'ocr-status ok';
    status.innerHTML = `✅ <b>${esc(file.name)}</b> — ${esc(result.summary)}`;
    if (result.suggested_text) {
      $('chatInput').value = result.suggested_text;
      $('chatInput').focus();
    }
  } catch (err) {
    status.className = 'ocr-status warn';
    status.textContent = `⚠ ${err.message}`;
  }
}

/* ══════════════════════════════════════════════════
   EXERCISES
══════════════════════════════════════════════════ */
function setCat(cat) {
  currentCat = cat;
  const d = t();
  html('catBar', d.cats.map(c => `
    <button class="cat-btn${c.key === cat ? ' active' : ''}" onclick="setCat('${c.key}')">${esc(c.label)}</button>`).join(''));
  renderExercises();
}

function renderExercises() {
  const d = t();
  if (!EXERCISES.length) {
    html('exGrid', `<div class="empty-state">
      <div class="empty-state-icon">⚠</div>
      <p class="empty-state-text">${lang === 'hi'
        ? 'व्यायाम लोड नहीं हो सके। जाँचें कि बैकएंड चल रहा है।'
        : 'Could not load exercises. Check that the backend is running.'}</p>
    </div>`);
    return;
  }

  const filtered = currentCat === 'all'
    ? EXERCISES
    : EXERCISES.filter(e => e.category === currentCat);

  html('exGrid', filtered.map(ex => `
    <div class="ex-card">
      <div class="ex-banner">
        <svg class="pv-figure ex-thumb" data-slug="${esc(ex.slug)}" viewBox="0 0 100 100" aria-hidden="true"></svg>
        <span class="view-tag">${ex.camera_view === 'side'
          ? (lang === 'hi' ? '↔ बगल से' : '↔ Side view')
          : (lang === 'hi' ? '⊙ सामने से' : '⊙ Front view')}</span>
        <span class="diff-tag ${esc(ex.difficulty)}">${esc(ex.difficulty)}</span>
      </div>
      <div class="ex-body">
        <div class="ex-name">${esc(tr(ex, 'name'))}</div>
        <div class="ex-part">${esc(ex.body_part)} · ${esc(ex.category.toUpperCase())}</div>
        <div class="ex-desc">${esc(tr(ex, 'description'))}</div>
        <div class="ex-stats">
          <span>🎯 ${ex.target_reps} ${ex.pose_mode === 'hold'
            ? (lang === 'hi' ? 'होल्ड' : 'holds') : 'reps'}</span>
          <span>⏱ ${ex.duration_seconds}s</span>
        </div>
        <div class="ex-actions">
          <button class="btn btn-outline btn-sm" onclick="openPreview('${esc(ex.slug)}')">
            ${lang === 'hi' ? '👁 कैसे करें' : '👁 How to'}
          </button>
          <button class="btn btn-primary btn-sm" onclick="startSession('${esc(ex.slug)}')">
            ${esc(d.startSession)}
          </button>
        </div>
      </div>
    </div>`).join(''));

  // Draw the still thumbnail on each card from the same keyframes the
  // preview animates, so the card and the demo always match.
  document.querySelectorAll('#exGrid .ex-thumb').forEach(svg => {
    const ex = EXERCISES.find(e => e.slug === svg.dataset.slug);
    if (ex && ex.preview) Preview.still(svg, ex, 'end');
  });
}

function catIcon(cat) {
  return { back: '🔙', knee: '🦵', hip: '🦴', shoulder: '💪',
           neck: '🧍', posture: '🧘' }[cat] || '🏋️';
}

/* ══════════════════════════════════════════════════
   EXERCISE PREVIEW  (shown before the camera opens)
══════════════════════════════════════════════════ */
let stopPreviewAnimation = null;

function openPreview(slug) {
  const ex = EXERCISES.find(e => e.slug === slug);
  if (!ex) return;

  set('previewTitle', tr(ex, 'name'));
  set('previewSub', tr(ex, 'description'));
  set('previewFigureLabel',
      `${tr(ex, 'name')} — ${lang === 'hi' ? 'गति का प्रदर्शन' : 'movement demonstration'}`);
  set('previewMotionLabel', lang === 'hi' ? 'गति का प्रदर्शन' : 'Movement demonstration');
  set('previewStepsLabel', lang === 'hi' ? 'कैसे करें' : 'How to do it');
  set('previewMistakesLabel', lang === 'hi' ? 'इनसे बचें' : 'Avoid these');
  set('previewBackBtn', lang === 'hi' ? 'वापस' : 'Back');
  set('previewStartBtn', lang === 'hi' ? 'कैमरे के साथ शुरू करें ▶' : 'Start with Camera ▶');

  const isHold = ex.pose_mode === 'hold';
  html('previewMeta', `
    <span class="meta-pill">${catIcon(ex.category)} ${esc(ex.body_part)}</span>
    <span class="meta-pill">🎯 ${ex.target_reps} ${isHold
      ? (lang === 'hi' ? 'होल्ड' : 'holds') : (lang === 'hi' ? 'दोहराव' : 'reps')}</span>
    <span class="meta-pill">⏱ ${ex.duration_seconds}s</span>
    <span class="meta-pill diff-${esc(ex.difficulty)}">${esc(ex.difficulty)}</span>
  `);

  const steps = (lang === 'hi' ? ex.steps_hi : ex.steps) || [];
  html('previewSteps', steps.map(s => `<li>${esc(s)}</li>`).join(''));

  const mistakes = (lang === 'hi' ? ex.mistakes_hi : ex.mistakes) || [];
  html('previewMistakes', mistakes.map(m => `<li>${esc(m)}</li>`).join(''));

  // Camera placement is not a detail: a sagittal movement measured from the
  // front is nearly flat, which is what makes an exercise "not detect".
  html('previewCameraHint', ex.camera_view === 'side'
    ? `<strong>${lang === 'hi' ? '📷 कैमरा बगल में रखें' : '📷 Place the camera to your side'}</strong>
       ${lang === 'hi'
         ? 'यह गति बगल से दिखती है। कैमरे के सामने न खड़े हों — बगल में मुड़कर पूरा शरीर फ़्रेम में रखें।'
         : 'This movement is visible from the side. Turn side-on to the camera and keep your whole body in frame.'}`
    : `<strong>${lang === 'hi' ? '📷 कैमरे के सामने खड़े हों' : '📷 Face the camera'}</strong>
       ${lang === 'hi'
         ? 'यह गति सामने से दिखती है। कैमरे की ओर मुँह करके पूरा शरीर फ़्रेम में रखें।'
         : 'This movement is visible from the front. Face the camera with your whole body in frame.'}`);

  $('previewStartBtn').onclick = () => { closePreview(); startSession(slug); };

  if (stopPreviewAnimation) stopPreviewAnimation();
  stopPreviewAnimation = Preview.animate($('previewFigure'), ex);

  $('previewModal').classList.add('open');
}

function closePreview() {
  // Stop the rAF loop, otherwise a hidden modal keeps repainting forever.
  if (stopPreviewAnimation) { stopPreviewAnimation(); stopPreviewAnimation = null; }
  $('previewModal').classList.remove('open');
}

/* ══════════════════════════════════════════════════
   LIVE SESSION (camera + pose tracking)
══════════════════════════════════════════════════ */
async function startSession(slug) {
  if (!API.isLoggedIn()) {
    toast(lang === 'hi'
      ? 'सत्र सहेजने के लिए कृपया लॉगिन करें।'
      : 'Please log in so your session can be saved.', 'warn');
    openAuth();
    return;
  }

  const ex = EXERCISES.find(e => e.slug === slug);
  if (!ex) return;
  liveExercise = ex;

  set('sessionTitle', tr(ex, 'name'));
  set('hudReps', `0 / ${ex.target_reps}`);
  set('hudQuality', '—');
  set('hudTime', '0s');
  set('sessionFeedback', lang === 'hi' ? 'तैयार हो रहे हैं…' : 'Getting ready…');
  $('sessionFeedback').style.background = 'rgba(14,165,164,.92)';
  $('sessionError').style.display = 'none';
  $('sessionLoading').style.display = 'flex';
  $('sessionModal').classList.add('open');

  try {
    const config = await API.poseConfig(slug);

    if (!window.PhysioPose) {
      throw new Error(lang === 'hi'
        ? 'पोज़ मॉडल लोड नहीं हुआ। इंटरनेट कनेक्शन जाँचें।'
        : 'Pose model failed to load. Check your internet connection.');
    }

    liveSession = window.PhysioPose.createSession({
      video: $('sessionVideo'),
      canvas: $('sessionCanvas'),
      config,
      lang,
      onUpdate: updateHud,
      onComplete: finishSession,
    });

    await liveSession.start();
    $('sessionLoading').style.display = 'none';
    set('sessionInstructions', lang === 'hi' ? config.cue_hi : config.cue_en);
  } catch (err) {
    showSessionError(err);
  }
}

function showSessionError(err) {
  $('sessionLoading').style.display = 'none';
  $('sessionError').style.display = 'flex';

  // getUserMedia failures are the common case and deserve a real explanation.
  let message;
  if (err && (err.name === 'NotAllowedError' || err.name === 'SecurityError')) {
    message = lang === 'hi'
      ? 'कैमरे की अनुमति नहीं मिली। ब्राउज़र सेटिंग्स में कैमरा चालू करें और फिर से कोशिश करें।'
      : 'Camera permission was denied. Allow camera access in your browser settings and try again.';
  } else if (err && err.name === 'NotFoundError') {
    message = lang === 'hi'
      ? 'कोई कैमरा नहीं मिला। कृपया वेबकैम कनेक्ट करें।'
      : 'No camera found. Please connect a webcam.';
  } else if (err && err.name === 'NotReadableError') {
    message = lang === 'hi'
      ? 'कैमरा किसी अन्य ऐप द्वारा उपयोग में है। उसे बंद करके फिर से कोशिश करें।'
      : 'The camera is in use by another app. Close it and try again.';
  } else {
    message = (err && err.message) || 'Could not start the session.';
  }
  set('sessionErrorText', message);
}

function updateHud({ reps, target, seconds, quality, feedback, tone }) {
  set('hudReps', `${reps} / ${target}`);
  set('hudTime', seconds + 's');
  set('hudQuality', quality + '%');
  $('hudQuality').style.color = quality >= 80 ? '#5eead4' : '#fbbf24';

  const icon = tone === 'warn' ? '⚠️' : '🟢';
  set('sessionFeedback', `${icon} ${feedback}`);
  $('sessionFeedback').style.background =
    tone === 'warn' ? 'rgba(234,179,8,.92)' : 'rgba(14,165,164,.92)';
}

/** Target reps reached: send the keypoint timeline for authoritative scoring. */
async function finishSession(frames) {
  set('sessionFeedback', lang === 'hi'
    ? '🎉 सत्र पूर्ण! विश्लेषण हो रहा है…'
    : '🎉 Session complete! Analysing…');
  $('sessionFeedback').style.background = 'rgba(99,102,241,.92)';

  await saveSession(frames, true);
  closeSession();
  showView('analytics');
}

async function saveSession(frames, completed) {
  if (!frames.length) return null;
  try {
    const saved = await API.submitSession({
      exercise_slug: liveExercise.slug,
      frames,
      completed,
      lang,
    });
    const summary = lang === 'hi'
      ? `सहेजा गया: ${saved.reps} दोहराव, गुणवत्ता ${saved.quality}%`
      : `Saved: ${saved.reps} reps, ${saved.quality}% form quality`;
    toast(summary, 'success');
    return saved;
  } catch (err) {
    toast(lang === 'hi'
      ? `सत्र सहेजा नहीं जा सका: ${err.message}`
      : `Could not save session: ${err.message}`);
    return null;
  }
}

/** Stopping early still records the work done, flagged as incomplete. */
async function closeSession() {
  const session = liveSession;
  liveSession = null;

  if (session) {
    session.stop();                       // releases the camera immediately
    const frames = session.getFrames();
    // Only worth saving if there is enough signal to analyse (~2s at 30fps).
    if (frames.length > 60 && session.getReps() > 0) {
      await saveSession(frames, false);
    }
  }
  $('sessionModal').classList.remove('open');
}

/* ══════════════════════════════════════════════════
   PLAN
══════════════════════════════════════════════════ */
async function generatePlan() {
  if (!currentDiag) return;
  if (!API.isLoggedIn()) {
    toast(lang === 'hi'
      ? 'योजना सहेजने के लिए कृपया लॉगिन करें।'
      : 'Please log in to save your plan.', 'warn');
    openAuth();
    return;
  }

  const btn = $('genPlanBtn');
  const label = btn.textContent;
  btn.disabled = true;
  btn.textContent = lang === 'hi' ? 'बना रहे हैं…' : 'Generating…';

  try {
    const plan = await API.createPlan(lang);
    activePlan = plan.content;
    activePlan.id = plan.id;
    showView('plan');
  } catch (err) {
    toast(err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = label;
  }
}

function renderPlan() {
  const d = t();
  if (!activePlan) {
    html('planContainer', `
      <div class="empty-state">
        <div class="empty-state-icon">📋</div>
        <p class="empty-state-text">${esc(d.planNone)}</p>
        <button class="btn btn-primary" style="margin-top:1.25rem" onclick="showView('assistant')">${esc(d.planNoneBtn)}</button>
      </div>`);
    return;
  }

  html('planContainer', `
    <div class="plan-banner">
      <div class="plan-banner-condition">${esc(d.planCondition)}: ${esc(tr(activePlan, 'condition'))}</div>
      <div class="plan-banner-title">${esc(tr(activePlan, 'title'))}</div>
      <div class="plan-banner-sub">${esc(d.planGenNote)}</div>
    </div>
    <div class="tab-row">
      <button class="tab-btn active" id="tabEx"      onclick="planTab('ex',this)">${esc(d.planTabEx)}</button>
      <button class="tab-btn"        id="tabDiet"    onclick="planTab('diet',this)">${esc(d.planTabDiet)}</button>
      <button class="tab-btn"        id="tabRoutine" onclick="planTab('routine',this)">${esc(d.planTabRoutine)}</button>
    </div>
    <div id="planTabBody">${renderPlanEx()}</div>
  `);
}

function planTab(tab, btn) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const body = { ex: renderPlanEx, diet: renderPlanDiet, routine: renderPlanRoutine };
  html('planTabBody', body[tab]());
}

function renderPlanEx() {
  const d = t();
  // Weeks progress in difficulty, so show them as separate blocks.
  return (activePlan.weeks || []).map(week => `
    <div class="plan-week">
      <div class="plan-week-head">
        <span class="plan-week-num">${lang === 'hi' ? 'सप्ताह' : 'Week'} ${week.week}</span>
        <span class="plan-week-focus">${esc(tr(week, 'focus'))}</span>
      </div>
      ${week.exercises.map(ex => `
        <div class="plan-ex-item">
          <div>
            <div class="plan-ex-name">${esc(tr(ex, 'name'))}</div>
            <div class="plan-ex-meta">${esc(tr(ex, 'time_of_day'))} · ${ex.sets} sets × ${ex.reps} reps</div>
          </div>
          <button class="btn btn-primary btn-sm" onclick="startSession('${esc(ex.slug)}')">${esc(d.startBtn)}</button>
        </div>`).join('')}
    </div>`).join('');
}

function renderPlanDiet() {
  return `<div class="diet-grid">${(activePlan.diet || []).map(item => `
    <div class="diet-card">
      <div class="diet-meal">${esc(tr(item, 'meal'))}</div>
      <div class="diet-items">${esc(tr(item, 'items'))}</div>
      <div class="diet-note">💡 ${esc(tr(item, 'note'))}</div>
    </div>`).join('')}</div>`;
}

function renderPlanRoutine() {
  return `<div class="timeline">${(activePlan.routine || []).map(r => `
    <div class="timeline-step">
      <div class="timeline-time">${esc(r.time)}</div>
      <div class="timeline-act">${esc(tr(r, 'act'))}</div>
    </div>`).join('')}</div>`;
}

/* ══════════════════════════════════════════════════
   ANALYTICS
══════════════════════════════════════════════════ */
async function renderAnalytics() {
  const d = t();

  if (!API.isLoggedIn()) {
    html('analyticsContainer', `
      <div class="empty-state">
        <div class="empty-state-icon">🔒</div>
        <p class="empty-state-text">${lang === 'hi'
          ? 'अपनी प्रगति देखने के लिए लॉगिन करें।'
          : 'Log in to see your recovery progress.'}</p>
        <button class="btn btn-primary" style="margin-top:1.25rem" onclick="openAuth()">${esc(t().authBtn)}</button>
      </div>`);
    return;
  }

  html('analyticsContainer', `<div class="empty-state"><div class="spinner"></div></div>`);

  let data, sessions;
  try {
    [data, sessions] = await Promise.all([API.analytics(), API.sessions()]);
  } catch (err) {
    html('analyticsContainer', `<div class="empty-state">
      <div class="empty-state-icon">⚠</div>
      <p class="empty-state-text">${esc(err.message)}</p></div>`);
    return;
  }
  analytics = data;

  if (!data.total_sessions) {
    html('analyticsContainer', `<div class="empty-state">
      <div class="empty-state-icon">📊</div>
      <p class="empty-state-text">${esc(d.noData)}</p>
      <button class="btn btn-primary" style="margin-top:1.25rem" onclick="showView('exercises')">${esc(d.startSession)}</button>
    </div>`);
    return;
  }

  const qualities = data.quality_trend.map(p => p.value);
  const roms = data.rom_trend.map(p => p.value);
  const summary = lang === 'hi' ? data.summary_hi : data.summary;

  html('analyticsContainer', `
    <div class="analytics-summary">
      <div class="analytics-summary-label">${esc(d.aiSummaryLabel)}</div>
      <div class="analytics-summary-text">${esc(summary)}</div>
    </div>

    <div class="stat-strip">
      <div class="stat-chip"><div class="stat-chip-n">${data.total_sessions}</div>
        <div class="stat-chip-l">${lang === 'hi' ? 'कुल सत्र' : 'Sessions'}</div></div>
      <div class="stat-chip"><div class="stat-chip-n">${data.total_reps}</div>
        <div class="stat-chip-l">${lang === 'hi' ? 'कुल दोहराव' : 'Total reps'}</div></div>
      <div class="stat-chip"><div class="stat-chip-n">${data.average_quality}%</div>
        <div class="stat-chip-l">${lang === 'hi' ? 'औसत गुणवत्ता' : 'Avg quality'}</div></div>
      <div class="stat-chip"><div class="stat-chip-n">${data.streak_days}</div>
        <div class="stat-chip-l">${lang === 'hi' ? 'दिन की लय' : 'Day streak'}</div></div>
    </div>

    <div class="analytics-grid" style="margin-top:1.5rem">
      <div class="analytics-card">
        <div class="analytics-card-header">
          <div class="analytics-card-title">${esc(d.qualityTrend)}</div>
          <div class="analytics-big-val" style="color:var(--teal)">${data.latest_quality}%</div>
        </div>
        ${qualities.length ? svgLine(qualities, 100, '#0ea5a4') : emptyChart()}
        <div class="chart-foot">${qualities.length} ${lang === 'hi' ? 'ट्रैक किए गए सत्र' : 'tracked sessions'}</div>
      </div>
      <div class="analytics-card">
        <div class="analytics-card-header">
          <div class="analytics-card-title">${esc(d.romTrend)}</div>
          <div class="analytics-big-val" style="color:var(--indigo)">${Math.round(data.latest_rom)}°</div>
        </div>
        ${roms.length ? svgLine(roms, Math.max(140, ...roms), '#6366f1') : emptyChart()}
        <div class="chart-foot">${roms.length} ${lang === 'hi' ? 'ट्रैक किए गए सत्र' : 'tracked sessions'}</div>
      </div>
    </div>

    <div class="analytics-grid" style="margin-top:1.5rem">
      <div class="analytics-card">
        <div class="analytics-card-title" style="margin-bottom:1rem">${esc(d.errorsTitle)}</div>
        <div class="error-bar-wrap">
          ${data.common_errors.length ? data.common_errors.map(err => `
            <div class="error-row">
              <div class="error-label-row">
                <span>${esc(lang === 'hi' ? err.message_hi : err.message)}</span>
                <span class="error-count">${err.count}×</span>
              </div>
              <div class="progress-track">
                <div class="progress-fill" style="width:${Math.min(err.percent, 100)}%;background:#ef4444"></div>
              </div>
            </div>`).join('')
            : `<p style="font-size:.88rem;color:var(--slate-400)">${lang === 'hi'
                ? 'कोई मुद्रा त्रुटि दर्ज नहीं! 🎉' : 'No posture errors logged! 🎉'}</p>`}
        </div>
      </div>
      <div class="analytics-card">
        <div class="analytics-card-title" style="margin-bottom:1rem">${esc(d.historyTitle)}</div>
        <div class="history-list">
          ${sessions.map(s => `
            <div class="history-item">
              <div>
                <div class="history-name">${esc(s.exercise_name)}</div>
                <div class="history-date">${new Date(s.created_at).toLocaleDateString(
                  lang === 'hi' ? 'hi-IN' : 'en-IN', { day: 'numeric', month: 'short' })}</div>
              </div>
              <div>
                <div class="history-score">${s.tracked_ratio >= 0.6
                  ? `${s.quality}% ${lang === 'hi' ? 'फॉर्म' : 'Form'}`
                  : `<span class="untracked">${lang === 'hi' ? 'बिना ट्रैकिंग' : 'Untracked'}</span>`}</div>
                <div class="history-reps">${s.reps}/${s.target_reps} reps</div>
              </div>
            </div>`).join('')}
        </div>
      </div>
    </div>
  `);
}

function emptyChart() {
  return `<div class="chart-empty">${lang === 'hi'
    ? 'ट्रैक किया गया कोई सत्र नहीं'
    : 'No tracked sessions yet'}</div>`;
}

function svgLine(data, max, color) {
  if (!data.length) return '';
  const W = 340, H = 130, P = 14;
  const coords = data.map((v, i) => ({
    x: data.length > 1 ? P + (i / (data.length - 1)) * (W - P * 2) : W / 2,
    y: H - P - Math.min(v / max, 1) * (H - P * 2),
  }));
  const pts  = coords.map(c => `${c.x},${c.y}`).join(' ');
  const fill = `M${coords[0].x},${H - P} ` +
    coords.map(c => `L${c.x},${c.y}`).join(' ') +
    ` L${coords[coords.length - 1].x},${H - P} Z`;
  const dots = coords.map(c =>
    `<circle cx="${c.x}" cy="${c.y}" r="4" fill="${color}" stroke="#fff" stroke-width="2"/>`
  ).join('');
  const gid = 'g' + color.replace('#', '');
  return `<svg viewBox="0 0 ${W} ${H}" style="width:100%;height:auto">
    <defs>
      <linearGradient id="${gid}" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="${color}" stop-opacity=".18"/>
        <stop offset="100%" stop-color="${color}" stop-opacity="0"/>
      </linearGradient>
    </defs>
    <line x1="${P}" y1="${H * .33}" x2="${W - P}" y2="${H * .33}" stroke="#f1f5f9" stroke-width="1"/>
    <line x1="${P}" y1="${H * .66}" x2="${W - P}" y2="${H * .66}" stroke="#f1f5f9" stroke-width="1"/>
    <path d="${fill}" fill="url(#${gid})"/>
    <polyline points="${pts}" fill="none" stroke="${color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
    ${dots}
  </svg>`;
}

/* ══════════════════════════════════════════════════
   AUTH
══════════════════════════════════════════════════ */
function openAuth() {
  $('authError').style.display = 'none';
  $('authModal').classList.add('open');
  $('authEmail').focus();
}

function closeAuth() { $('authModal').classList.remove('open'); }

function switchAuthTab(mode) {
  authMode = mode;
  $('tabLogin').classList.toggle('active',  mode === 'login');
  $('tabSignup').classList.toggle('active', mode === 'signup');
  $('nameField').style.display = mode === 'signup' ? 'block' : 'none';
  $('authPwHint').style.display = mode === 'signup' ? 'block' : 'none';
  $('authError').style.display = 'none';
  $('authSubmit').textContent = mode === 'login' ? 'Login' : 'Sign Up';
  $('authPassword').autocomplete =
    mode === 'login' ? 'current-password' : 'new-password';
}

async function handleAuth(e) {
  e.preventDefault();
  const submit = $('authSubmit');
  const errorBox = $('authError');
  errorBox.style.display = 'none';

  const email = $('authEmail').value.trim();
  const password = $('authPassword').value;
  const name = $('authName').value.trim();

  if (authMode === 'signup' && !name) {
    errorBox.textContent = 'Please enter your name';
    errorBox.style.display = 'block';
    return;
  }

  submit.disabled = true;
  const label = submit.textContent;
  submit.textContent = authMode === 'login' ? 'Logging in…' : 'Creating account…';

  try {
    user = authMode === 'signup'
      ? await API.signup(name, email, password, lang)
      : await API.login(email, password);

    $('authPassword').value = '';       // do not leave it sitting in the DOM
    closeAuth();
    renderAll();
    await refreshPlan();
    toast(lang === 'hi' ? `स्वागत है, ${user.name}!` : `Welcome, ${user.name}!`,
          'success');
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.style.display = 'block';
  } finally {
    submit.disabled = false;
    submit.textContent = label;
  }
}

function logout() {
  API.logout();
  user = null;
  activePlan = null;
  currentDiag = null;
  analytics = null;
  renderAll();
  showView('landing');
}

// Close modals on backdrop click
['authModal','sessionModal','previewModal'].forEach(id => {
  $(id).addEventListener('click', e => {
    if (e.target !== $(id)) return;
    if (id === 'sessionModal')      closeSession();
    else if (id === 'previewModal') closePreview();
    else                            closeAuth();
  });
});
