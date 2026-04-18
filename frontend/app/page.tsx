"use client";

/**
 * Rewind — Command Center (Next.js 14 + App Router + Tailwind)
 * Owner: Jeeyan
 *
 * Run:
 *   cd frontend
 *   npm install
 *   cp .env.local.example .env.local   # set NEXT_PUBLIC_REWIND_API to the Pi's IP
 *   npm run dev                        # http://localhost:3000
 *
 * Audio:
 *   - STT via SpeechRecognition (laptop mic, Chrome-only, free)
 *   - TTS via speechSynthesis (laptop speaker, all browsers, free)
 *   - Typed input is always the primary fallback.
 */

import { useEffect, useRef, useState } from "react";
import { Eye, EyeOff, Mic, MicOff, Send, AlertCircle, Clock, Volume2 } from "lucide-react";

const API = process.env.NEXT_PUBLIC_REWIND_API ?? "http://localhost:8000";
const WS  = API.replace("http", "ws") + "/ws/events";

type EventRow = {
  id: number;
  ts: number;
  event_type: string;
  object: string;
  track_id?: number | null;
  thumb_path?: string | null;
};

type Answer = {
  answer: string;
  confidence: "high" | "medium" | "low";
  event_ids: number[];
  _model?: string;
};

type Alert = {
  severity: "info" | "warn" | "urgent";
  title: string;
  body: string;
  suggested_action?: {
    type: string;
    to_name?: string;
    draft?: string;
  } | null;
};

// ---------- Utilities ----------

function fmtTime(ts: number): string {
  return new Date(ts * 1000).toLocaleTimeString([], {
    hour: "2-digit", minute: "2-digit", second: "2-digit",
  });
}

function speak(text: string) {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
  // Cancel any in-flight utterance so we don't queue
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.rate = 1.0;
  u.pitch = 1.0;
  // Prefer a natural-sounding voice if available
  const voices = window.speechSynthesis.getVoices();
  const preferred = voices.find(v => /Samantha|Jenny|Google US English|Microsoft Aria/i.test(v.name));
  if (preferred) u.voice = preferred;
  window.speechSynthesis.speak(u);
}

// Minimal typings for SpeechRecognition (not in lib.dom yet)
type SRClass = new () => {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: (e: any) => void;
  onend: () => void;
  onerror: (e: any) => void;
  start: () => void;
  stop: () => void;
};

function getSR(): SRClass | null {
  if (typeof window === "undefined") return null;
  return (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition || null;
}

// ---------- Component ----------

export default function Page() {
  const [events, setEvents] = useState<EventRow[]>([]);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const [shutterClosed, setShutterClosed] = useState(false);
  const recognitionRef = useRef<any>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // Initial load + WebSocket
  useEffect(() => {
    fetch(`${API}/events?limit=80`).then(r => r.json()).then(setEvents).catch(() => {});
    const ws = new WebSocket(WS);
    wsRef.current = ws;
    ws.onmessage = msg => {
      const ev: EventRow = JSON.parse(msg.data);
      setEvents(prev => [ev, ...prev].slice(0, 100));
    };
    const ping = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send("ping");
    }, 15_000);
    return () => { clearInterval(ping); ws.close(); };
  }, []);

  // Pre-load voice list (Chrome loads voices asynchronously)
  useEffect(() => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.getVoices();
      window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
    }
  }, []);

  async function ask(q?: string) {
    const question_to_ask = q ?? question;
    if (!question_to_ask.trim()) return;
    setLoading(true);
    setAnswer(null);
    try {
      const r = await fetch(`${API}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: question_to_ask }),
      });
      const data: Answer = await r.json();
      setAnswer(data);
      speak(data.answer);
    } catch (e) {
      setAnswer({
        answer: "Couldn't reach the Rewind device. Check the Pi is on your network.",
        confidence: "low",
        event_ids: [],
      });
    } finally {
      setLoading(false);
    }
  }

  function toggleListen() {
    const SR = getSR();
    if (!SR) {
      alert("Speech recognition not supported in this browser. Use Chrome.");
      return;
    }
    if (listening && recognitionRef.current) {
      recognitionRef.current.stop();
      return;
    }
    const recog = new SR();
    recog.continuous = false;
    recog.interimResults = false;
    recog.lang = "en-US";
    recog.onresult = (e: any) => {
      const transcript = e.results[0][0].transcript;
      setQuestion(transcript);
      setTimeout(() => ask(transcript), 100);
    };
    recog.onend = () => setListening(false);
    recog.onerror = () => setListening(false);
    recognitionRef.current = recog;
    setListening(true);
    recog.start();
  }

  async function checkAgent() {
    const r = await fetch(`${API}/agent/check`, { method: "POST" });
    setAlerts(await r.json());
  }

  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-100 p-6 font-sans">
      {/* Header */}
      <header className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <div className="size-3 rounded-full bg-emerald-500 animate-pulse" />
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Rewind</h1>
            <p className="text-xs text-zinc-500 font-mono">ambient memory · on-device</p>
          </div>
        </div>
        <button
          onClick={() => setShutterClosed(s => !s)}
          className="flex items-center gap-2 text-sm text-zinc-400 hover:text-zinc-100 border border-zinc-800 rounded-lg px-3 py-2"
        >
          {shutterClosed ? <EyeOff size={16} /> : <Eye size={16} />}
          {shutterClosed ? "Shutter closed" : "Watching"}
        </button>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Event timeline */}
        <section className="lg:col-span-1 border border-zinc-800 rounded-xl p-4 bg-zinc-900/40">
          <div className="flex items-center gap-2 mb-3 text-zinc-400 text-xs font-mono uppercase tracking-wider">
            <Clock size={12} />
            Event stream
          </div>
          <ul className="space-y-1.5 max-h-[70vh] overflow-y-auto">
            {events.map(e => (
              <li key={e.id} className="text-sm font-mono flex gap-3 py-1.5 border-b border-zinc-900">
                <span className="text-zinc-600 shrink-0">{fmtTime(e.ts)}</span>
                <span className="text-zinc-400 shrink-0 w-28 truncate">{e.event_type}</span>
                <span className="text-zinc-100 truncate">{e.object}</span>
              </li>
            ))}
            {events.length === 0 && (
              <li className="text-zinc-600 text-sm italic">No events yet. Place something in view.</li>
            )}
          </ul>
        </section>

        {/* Center/Right: Query + Agent */}
        <section className="lg:col-span-2 space-y-6">
          <div className="border border-zinc-800 rounded-xl p-6 bg-zinc-900/40">
            <div className="flex gap-2 mb-4">
              <input
                value={question}
                onChange={e => setQuestion(e.target.value)}
                onKeyDown={e => e.key === "Enter" && ask()}
                placeholder="Ask Rewind… e.g. 'where did I leave my keys?'"
                className="flex-1 bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-3 text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:border-emerald-600"
              />
              <button
                onClick={() => ask()}
                disabled={loading}
                className="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white px-4 py-3 rounded-lg flex items-center gap-2"
              >
                {loading ? "…" : <><Send size={16} /> Ask</>}
              </button>
              <button
                onClick={toggleListen}
                title="Press and speak (laptop mic via Web Speech API)"
                className={
                  "px-4 py-3 rounded-lg flex items-center gap-2 " +
                  (listening
                    ? "bg-red-600 hover:bg-red-500 text-white animate-pulse"
                    : "bg-zinc-800 hover:bg-zinc-700 text-zinc-300")
                }
              >
                {listening ? <MicOff size={16} /> : <Mic size={16} />}
              </button>
            </div>

            <div className="flex flex-wrap gap-2">
              {[
                "Where did I leave my keys?",
                "Did I take my medication today?",
                "When did someone last come in?",
              ].map(q => (
                <button
                  key={q}
                  onClick={() => { setQuestion(q); setTimeout(() => ask(q), 50); }}
                  className="text-xs text-zinc-400 hover:text-zinc-100 border border-zinc-800 rounded-full px-3 py-1.5"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>

          {answer && (
            <div className="border border-emerald-900/60 rounded-xl p-6 bg-emerald-950/20">
              <div className="flex items-center justify-between mb-2">
                <div className="text-xs font-mono uppercase tracking-wider text-emerald-500">
                  Answer · {answer.confidence} confidence · {answer._model ?? "model"}
                </div>
                <button
                  onClick={() => speak(answer.answer)}
                  title="Replay audio"
                  className="text-zinc-500 hover:text-zinc-300"
                >
                  <Volume2 size={14} />
                </button>
              </div>
              <p className="text-lg text-zinc-50 leading-relaxed">{answer.answer}</p>
              {answer.event_ids?.length > 0 && (
                <p className="mt-3 text-xs text-zinc-500 font-mono">
                  Referenced events: {answer.event_ids.join(", ")}
                </p>
              )}
            </div>
          )}

          <div className="border border-zinc-800 rounded-xl p-6 bg-zinc-900/40">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 text-zinc-400 text-xs font-mono uppercase tracking-wider">
                <AlertCircle size={12} />
                Proactive agent
              </div>
              <button
                onClick={checkAgent}
                className="text-xs text-zinc-400 hover:text-zinc-100 border border-zinc-800 rounded-lg px-3 py-1.5"
              >
                Run check
              </button>
            </div>
            <div className="space-y-3">
              {alerts.map((a, i) => (
                <div key={i} className={
                  "rounded-lg border p-4 " +
                  (a.severity === "urgent"
                    ? "border-red-900/60 bg-red-950/20"
                    : "border-amber-900/60 bg-amber-950/20")
                }>
                  <div className="font-semibold text-zinc-100">{a.title}</div>
                  <div className="text-sm text-zinc-400 mt-1">{a.body}</div>
                  {a.suggested_action?.draft && (
                    <div className="mt-3 text-sm">
                      <div className="text-xs text-zinc-500 mb-1">
                        Suggested text to {a.suggested_action.to_name}:
                      </div>
                      <div className="italic text-zinc-300 border-l-2 border-zinc-700 pl-3">
                        "{a.suggested_action.draft}"
                      </div>
                    </div>
                  )}
                </div>
              ))}
              {alerts.length === 0 && (
                <p className="text-zinc-600 text-sm italic">No alerts. All scheduled items on track.</p>
              )}
            </div>
          </div>
        </section>
      </div>

      <footer className="mt-12 text-center text-xs text-zinc-600 font-mono">
        Rewind · HackPrinceton 2026 · no video ever leaves this device
      </footer>
    </main>
  );
}
