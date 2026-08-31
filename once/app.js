const TARGETS = [
  { id: "en", tts: "en-US", label: "English", short: "EN" },
  { id: "es", tts: "es-ES", label: "Español", short: "ES" },
  { id: "fr", tts: "fr-FR", label: "Français", short: "FR" },
  { id: "pt", tts: "pt-BR", label: "Português", short: "PT" },
  { id: "de", tts: "de-DE", label: "Deutsch", short: "DE" },
  { id: "ar", tts: "ar-SA", label: "العربية", short: "AR" },
  { id: "ja", tts: "ja-JP", label: "日本語", short: "JA" },
  { id: "zh-CN", tts: "zh-CN", label: "中文", short: "ZH" },
  { id: "hi", tts: "hi-IN", label: "हिन्दी", short: "HI" },
  { id: "ko", tts: "ko-KR", label: "한국어", short: "KO" },
];

const I18N = {
  fr: {
    eyebrow: "Le doublage pour tout le monde",
    h1a: "Tu parles une fois.",
    h1b: "Ta vidéo parle toutes les langues.",
    lead: "Tu filmes en français. ONCE réécoute, traduit, et rejoue ta vidéo avec une nouvelle voix + des sous-titres. Pas un compte. Pas une carte. Ça tourne dans ton navigateur.",
    record: "Parler maintenant",
    upload: "Déposer une vidéo",
    type: "Écrire une phrase",
    hint: "V1 : nouvelle voix + sous-titres. La bouche ne suit pas encore (ça, c’est la V2).",
    original: "Original",
    play: "Écouter la nouvelle voix",
    dl: "Télécharger .srt",
    again: "Recommencer",
    foot: "Tu parles une fois. Le monde t’écoute.",
    listening: "J’écoute… parle clairement.",
    stop: "Stop · traduire",
    transcribing: "J’écoute la vidéo…",
    translating: "Je traduis…",
    ready: "Prêt. Lance la nouvelle voix.",
    needmic: "Autorise le micro — c’est tout.",
    nomic: "Ce navigateur ne capte pas la voix. Utilise Chrome, ou dépose une vidéo.",
    nofile: "Je n’ai pas pu lire la voix dans ce fichier. Écris ce qui est dit.",
    empty: "Je n’ai rien entendu. Écris la phrase, ou réessaie.",
    typeTitle: "Écris ce que tu as dit",
    typeGo: "Traduire",
    cancel: "Annuler",
    iframeMic: "Le micro est bloqué dans cet aperçu. Écris une phrase, ou dépose une vidéo. Sur le vrai site (en grand / téléphone), le micro marchera.",
  },
  en: {
    eyebrow: "Dubbing for everyone",
    h1a: "Speak once.",
    h1b: "Your video speaks every language.",
    lead: "Film in your language. ONCE listens, translates, and plays it back with a new voice + subtitles. No account. No card. It runs in your browser.",
    record: "Speak now",
    upload: "Drop a video",
    type: "Type a sentence",
    hint: "V1: new voice + subtitles. Lips don’t match yet — that’s V2.",
    original: "Original",
    play: "Play new voice",
    dl: "Download .srt",
    again: "Start over",
    foot: "Speak once. Be heard everywhere.",
    listening: "Listening… speak clearly.",
    stop: "Stop · translate",
    transcribing: "Listening to the video…",
    translating: "Translating…",
    ready: "Ready. Play the new voice.",
    needmic: "Allow the microphone — that’s it.",
    nomic: "This browser can’t hear you. Use Chrome, or drop a video.",
    nofile: "Couldn’t hear speech in that file. Type what was said.",
    empty: "Heard nothing. Type the sentence, or try again.",
    typeTitle: "Type what you said",
    typeGo: "Translate",
    cancel: "Cancel",
    iframeMic: "The mic is blocked in this preview. Type a sentence, or drop a video. On the real site, the mic will work.",
  },
};

const $ = (id) => document.getElementById(id);
const state = {
  ui: "fr",
  target: TARGETS[0],
  recording: false,
  media: null,
  recorder: null,
  chunks: [],
  recognition: null,
  liveText: "",
  sourceText: "",
  sourceLang: "fr",
  segments: [],
  objectUrl: null,
};

function t(key) {
  return I18N[state.ui][key] || key;
}

function applyUi() {
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = t(el.dataset.i18n);
  });
  $("langUi").textContent = state.ui.toUpperCase();
}

function renderTargets() {
  const box = $("targetPicker");
  box.innerHTML = "";
  TARGETS.forEach((lang) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "chip" + (lang.id === state.target.id ? " on" : "");
    b.textContent = lang.label;
    b.onclick = () => {
      state.target = lang;
      renderTargets();
      $("dstTitle").textContent = lang.label;
    };
    box.appendChild(b);
  });
}

function showStudio() {
  $("hero").classList.add("hidden");
  $("studio").classList.remove("hidden");
}

function setStatus(msg) {
  $("status").textContent = msg || "";
  $("stepLabel").textContent = msg || "—";
}

function setScripts(src, dst) {
  $("srcText").textContent = src || "";
  $("dstText").textContent = dst || "";
}

$("langUi").onclick = () => {
  state.ui = state.ui === "fr" ? "en" : "fr";
  applyUi();
};

$("btnReset").onclick = () => location.reload();

function SpeechRec() {
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}

$("btnRecord").onclick = async () => {
  if (state.recording) {
    stopRecording();
    return;
  }
  showErr("");
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    showErr(t("iframeMic"));
    openType();
    return;
  }
  try {
    try {
      state.media = await navigator.mediaDevices.getUserMedia({ audio: true, video: true });
    } catch {
      state.media = await navigator.mediaDevices.getUserMedia({ audio: true });
    }
  } catch {
    showErr(t("iframeMic"));
    openType();
    return;
  }
  showStudio();
  const player = $("player");
  player.muted = true;
  player.srcObject = state.media;
  const hasVideo = state.media.getVideoTracks().length > 0;
  if (hasVideo) $("emptyStage").classList.add("off");
  else $("emptyStage").classList.remove("off");
  player.play().catch(() => {});
  $("recBadge").classList.remove("hidden");
  $("btnStop").classList.remove("hidden");
  $("btnRecord").classList.add("live");

  state.chunks = [];
  const mime = pickMime(hasVideo);
  const rec = mime ? new MediaRecorder(state.media, { mimeType: mime }) : new MediaRecorder(state.media);
  state.recorder = rec;
  rec.ondataavailable = (e) => {
    if (e.data.size) state.chunks.push(e.data);
  };
  rec.start(200);

  const Rec = SpeechRec();
  state.liveText = "";
  if (Rec) {
    const recognition = new Rec();
    recognition.lang = state.ui === "fr" ? "fr-FR" : "en-US";
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.onresult = (ev) => {
      let final = "";
      let interim = "";
      for (let i = 0; i < ev.results.length; i++) {
        const piece = ev.results[i][0].transcript;
        if (ev.results[i].isFinal) final += piece + " ";
        else interim += piece;
      }
      state.liveText = (final + interim).trim();
      setScripts(state.liveText, "");
      $("subs").textContent = state.liveText;
    };
    recognition.onerror = () => {};
    try {
      recognition.start();
    } catch {
      /* already started */
    }
    state.recognition = recognition;
  }
  state.recording = true;
  setStatus(t("listening"));
};

$("btnStop").onclick = () => {
  if (state.recording) stopRecording();
};

function pickMime() {
  const types = ["video/webm;codecs=vp8,opus", "video/webm", "video/mp4"];
  for (const tpe of types) {
    if (MediaRecorder.isTypeSupported(tpe)) return tpe;
  }
  return "";
}

async function stopRecording() {
  state.recording = false;
  $("btnRecord").classList.remove("live");
  $("recBadge").classList.add("hidden");
  $("btnStop").classList.add("hidden");
  try {
    state.recognition && state.recognition.stop();
  } catch {
    /* ignore */
  }
  await new Promise((res) => {
    if (!state.recorder || state.recorder.state === "inactive") return res();
    state.recorder.onstop = res;
    state.recorder.stop();
  });
  state.media && state.media.getTracks().forEach((tr) => tr.stop());
  const blob = new Blob(state.chunks, { type: state.recorder?.mimeType || "video/webm" });
  if (blob.size > 0) attachMedia(blob);
  const text = state.liveText.trim();
  if (!text) {
    setStatus(t("empty"));
    openType("");
    return;
  }
  await finishWithText(text, state.ui === "fr" ? "fr" : "en");
}

$("btnType").onclick = () => openType();
$("btnTypeCancel").onclick = () => closeType();
$("btnTypeGo").onclick = async () => {
  const text = $("typeBox").value.trim();
  if (!text) return;
  closeType();
  showStudio();
  if (!$("player").src && !$("player").srcObject) {
    $("emptyStage").classList.remove("off");
  }
  setStatus(t("translating"));
  await finishWithText(text, state.ui === "fr" ? "fr" : "en");
};

$("file").onchange = async (ev) => {
  const file = ev.target.files && ev.target.files[0];
  if (!file) return;
  showErr("");
  showStudio();
  attachMedia(file);
  setStatus(t("transcribing"));
  try {
    const { text, lang } = await transcribeFile(file);
    if (!text) {
      setStatus(t("empty"));
      openType("");
      return;
    }
    await finishWithText(text, lang || "en");
  } catch (err) {
    console.error(err);
    setStatus(t("nofile"));
    openType("");
  }
};

function attachMedia(fileOrBlob) {
  if (state.objectUrl) URL.revokeObjectURL(state.objectUrl);
  state.objectUrl = URL.createObjectURL(fileOrBlob);
  const player = $("player");
  player.srcObject = null;
  player.src = state.objectUrl;
  player.muted = false;
  player.controls = true;
  $("emptyStage").classList.add("off");
}

async function finishWithText(text, sourceLang) {
  state.sourceText = text;
  state.sourceLang = sourceLang;
  setScripts(text, "");
  setStatus(t("translating"));
  const translated = await translateText(text, sourceLang, state.target.id);
  const segs = splitSentences(translated);
  const srcSegs = splitSentences(text);
  state.segments = segs.map((s, i) => ({
    src: srcSegs[i] || "",
    dst: s,
  }));
  setScripts(text, translated);
  $("dstTitle").textContent = state.target.label;
  $("subs").textContent = translated;
  $("btnPlayDub").disabled = false;
  $("btnDl").disabled = false;
  setStatus(t("ready"));
}

$("btnPlayDub").onclick = () => {
  const player = $("player");
  window.speechSynthesis.cancel();
  player.muted = true;
  player.currentTime = 0;
  player.play().catch(() => {});
  const full = $("dstText").textContent.trim();
  if (!full) return;
  const u = new SpeechSynthesisUtterance(full);
  u.lang = state.target.tts;
  const voice = pickVoice(state.target.tts);
  if (voice) u.voice = voice;
  u.rate = 1;
  u.onboundary = () => {
    $("subs").textContent = full;
  };
  const parts = splitSentences(full);
  speakQueue(parts, state.target.tts);
};

function speakQueue(parts, lang) {
  window.speechSynthesis.cancel();
  let i = 0;
  const next = () => {
    if (i >= parts.length) return;
    const u = new SpeechSynthesisUtterance(parts[i]);
    u.lang = lang;
    const voice = pickVoice(lang);
    if (voice) u.voice = voice;
    $("subs").textContent = parts[i];
    i += 1;
    u.onend = next;
    window.speechSynthesis.speak(u);
  };
  next();
}

function pickVoice(lang) {
  const voices = window.speechSynthesis.getVoices();
  const prefix = lang.slice(0, 2).toLowerCase();
  return (
    voices.find((v) => v.lang.replace("_", "-").toLowerCase() === lang.toLowerCase()) ||
    voices.find((v) => v.lang.toLowerCase().startsWith(prefix)) ||
    null
  );
}

$("btnDl").onclick = () => {
  const dst = $("dstText").textContent.trim();
  const src = $("srcText").textContent.trim();
  if (!dst) return;
  const srt = toSrt(dst);
  const blob = new Blob([srt], { type: "text/plain;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `once-${state.target.id}.srt`;
  a.click();
  const txt = `${src}\n\n--- ${state.target.label} ---\n\n${dst}\n`;
  const b2 = new Blob([txt], { type: "text/plain;charset=utf-8" });
  const a2 = document.createElement("a");
  a2.href = URL.createObjectURL(b2);
  a2.download = `once-${state.target.id}.txt`;
  a2.click();
};

function toSrt(text) {
  const parts = splitSentences(text);
  return parts
    .map((p, i) => {
      const start = i * 4;
      const end = start + 4;
      return `${i + 1}\n${fmt(start)} --> ${fmt(end)}\n${p}\n`;
    })
    .join("\n");
}

function fmt(sec) {
  const h = String(Math.floor(sec / 3600)).padStart(2, "0");
  const m = String(Math.floor((sec % 3600) / 60)).padStart(2, "0");
  const s = String(Math.floor(sec % 60)).padStart(2, "0");
  return `${h}:${m}:${s},000`;
}

function splitSentences(text) {
  const bits = text
    .replace(/\s+/g, " ")
    .split(/(?<=[.!?。？！])\s+/)
    .map((s) => s.trim())
    .filter(Boolean);
  return bits.length ? bits : [text];
}

async function translateText(text, sl, tl) {
  if (!text) return "";
  if (sl.slice(0, 2) === tl.slice(0, 2)) return text;
  const chunks = chunk(text, 420);
  const out = [];
  for (const c of chunks) {
    out.push(await translateChunk(c, sl, tl));
  }
  return out.join(" ");
}

async function translateChunk(text, sl, tl) {
  const pair = `${normLang(sl)}|${normLang(tl)}`;
  try {
    const url = `https://api.mymemory.translated.net/get?q=${encodeURIComponent(text)}&langpair=${pair}`;
    const r = await fetch(url);
    if (r.ok) {
      const j = await r.json();
      const tr = j?.responseData?.translatedText;
      if (tr && !/^MYMEMORY WARNING/i.test(tr)) return tr;
    }
  } catch {
    /* try next */
  }
  try {
    const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=${encodeURIComponent(
      normLang(sl)
    )}&tl=${encodeURIComponent(normLang(tl))}&dt=t&q=${encodeURIComponent(text)}`;
    const r = await fetch(url);
    if (r.ok) {
      const j = await r.json();
      return (j[0] || []).map((row) => row[0]).join("");
    }
  } catch {
    /* ignore */
  }
  return text;
}

function normLang(code) {
  const c = (code || "en").toLowerCase();
  if (c.startsWith("zh")) return "zh-CN";
  return c.slice(0, 2);
}

function chunk(text, n) {
  const words = text.split(" ");
  const out = [];
  let cur = "";
  for (const w of words) {
    if ((cur + " " + w).length > n) {
      out.push(cur.trim());
      cur = w;
    } else cur += " " + w;
  }
  if (cur.trim()) out.push(cur.trim());
  return out;
}

let whisperPipe = null;
async function transcribeFile(file) {
  // Fast path: audio decode + whisper in the browser (no server).
  try {
    const { pipeline, env } = await import("https://cdn.jsdelivr.net/npm/@xenova/transformers@2.17.2");
    env.allowLocalModels = false;
    setStatus(state.ui === "fr" ? "Premier lancement : je télécharge l’oreille (1×)…" : "First run: downloading the ear (once)…");
    if (!whisperPipe) {
      whisperPipe = await pipeline("automatic-speech-recognition", "Xenova/whisper-tiny", {
        progress_callback: (p) => {
          if (p?.status === "progress" && p.file) {
            const pct = p.total ? Math.round((p.loaded / p.total) * 100) : 0;
            setStatus(`${p.file.split("/").pop()} ${pct}%`);
          }
        },
      });
    }
    setStatus(t("transcribing"));
    const url = URL.createObjectURL(file);
    const result = await whisperPipe(url, { chunk_length_s: 20, stride_length_s: 4 });
    URL.revokeObjectURL(url);
    const text = (result?.text || "").trim();
    const lang = result?.language || "en";
    return { text, lang };
  } catch (e) {
    console.warn("whisper failed", e);
    // Last resort: ask the OS transcriber via a short recorded playback — not possible.
    throw e;
  }
}

if (window.speechSynthesis) {
  window.speechSynthesis.getVoices();
  window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
}

renderTargets();
applyUi();
$("dstTitle").textContent = state.target.label;
