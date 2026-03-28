"use client";

import { useRef, useState } from "react";

import { startAskQuestionStream, type AskStreamEnvelope, updateBuddyProfile } from "@/lib/api";
import { useMvpData } from "@/hooks/use-mvp-data";
import { WorkspaceFrame } from "@/components/workspace-frame";

const personaOptions = [
  { value: "strict", title: "严格导师", description: "高标准监督推进", icon: "school" },
  { value: "gentle", title: "温柔学伴", description: "耐心支持与鼓励", icon: "favorite" },
  { value: "energetic", title: "冲刺教练", description: "直接高效、快速推进", icon: "bolt" },
];

export default function TutorPage() {
  const { buddyProfile, weakPoints, reviewTasks, documents } = useMvpData("general");
  const [selectedPersona, setSelectedPersona] = useState<"gentle" | "strict" | "energetic" | "calm">(buddyProfile?.persona ?? "strict");
  const [composer, setComposer] = useState("");
  const [lastUserPrompt, setLastUserPrompt] = useState("");
  const [aiReply, setAiReply] = useState("");
  const [citations, setCitations] = useState<Array<{ source_label: string; source_locator: string }>>([]);
  const [savingPersona, setSavingPersona] = useState(false);
  const [sending, setSending] = useState(false);
  const [status, setStatus] = useState("");
  const [toolSteps, setToolSteps] = useState<Array<{ id: string; type: "start" | "end"; name: string; detail?: string }>>([]);
  const abortRef = useRef<null | (() => void)>(null);

  async function handlePersonaChange(persona: "gentle" | "strict" | "energetic" | "calm") {
    setSelectedPersona(persona);
    setSavingPersona(true);
    try {
      await updateBuddyProfile({ name: buddyProfile?.name ?? "小智", persona });
    } finally {
      setSavingPersona(false);
    }
  }

  async function handleSend(event: React.SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    const prompt = composer.trim();
    if (!prompt || sending) return;

    abortRef.current?.();
    setSending(true);
    setLastUserPrompt(prompt);
    setAiReply("");
    setCitations([]);
    setToolSteps([]);
    setStatus("请求已发送，等待模型响应...");

    const onEvent = (ev: AskStreamEnvelope) => {
      const data = (ev as AskStreamEnvelope).data as Record<string, unknown>;
      if (!data || typeof data.type !== "string") return;

      if (data.type === "status") {
        if (typeof data.content === "string") setStatus(data.content);
        return;
      }

      if (data.type === "tool_start") {
        const toolName = String(data.tool_name ?? "unknown");
        setToolSteps((prev) => [
          ...prev,
          { id: `start-${Date.now()}`, type: "start", name: toolName, detail: JSON.stringify(data.input ?? "").slice(0, 100) },
        ]);
        setStatus(`正在调用工具：${toolName}`);
        return;
      }

      if (data.type === "tool_end") {
        const toolName = String(data.tool_name ?? "unknown");
        setToolSteps((prev) => [
          ...prev,
          { id: `end-${Date.now()}`, type: "end", name: toolName, detail: String(data.output ?? "").slice(0, 100) },
        ]);
        return;
      }

      if (data.type === "token") {
        if (typeof data.content === "string" && data.content) {
          setAiReply((prev) => prev + data.content);
        }
        return;
      }

      if (data.type === "final") {
        setAiReply(String(data.answer ?? ""));
        const citationsData = Array.isArray(data.citations) ? data.citations : [];
        setCitations(
          citationsData.map((c: { source_label?: string; source_locator?: string }) => ({
            source_label: String(c?.source_label ?? ""),
            source_locator: String(c?.source_locator ?? ""),
          })),
        );
        setStatus("");
        setSending(false);
        abortRef.current = null;
        return;
      }

      if (data.type === "error") {
        setStatus(ev.message || "问答失败。");
        setSending(false);
        abortRef.current = null;
      }
    };

    abortRef.current = startAskQuestionStream(
      { scene_id: "general", session_id: null, question: prompt },
      onEvent,
      () => {
        setStatus("流式请求失败，请检查后端服务与网络。");
        setSending(false);
        abortRef.current = null;
      },
    );
    setComposer("");
  }

  const currentNode = weakPoints[0]?.concept ?? "AI 架构基础";
  const focusLabel = reviewTasks[0]?.concept ?? "RAG 基础原理";

  return (
    <WorkspaceFrame badge="学习辅导" title="学习辅导" subtitle="" hidePageHeader>
      <div className="flex gap-6 h-[calc(100vh-120px)]">

        {/* Chat area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto space-y-6 pb-4">
            {!lastUserPrompt && !aiReply && (
              <div className="flex items-center justify-center h-full">
                <div className="text-center space-y-3">
                  <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto">
                    <span className="material-symbols-outlined text-primary text-3xl" style={{ fontVariationSettings: "'FILL' 1" }}>psychology</span>
                  </div>
                  <p className="text-sm text-outline">向你的 AI 学伴提问，开始学习之旅</p>
                </div>
              </div>
            )}
            {lastUserPrompt && (
              <div className="flex justify-end">
                <div className="bg-surface-container-high px-5 py-3 rounded-2xl rounded-tr-none max-w-[75%] border border-outline-variant/10">
                  <p className="text-sm leading-relaxed text-on-surface">{lastUserPrompt}</p>
                </div>
              </div>
            )}
            {(aiReply || sending) && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center flex-shrink-0 mt-1">
                  <span className="material-symbols-outlined text-primary text-base" style={{ fontVariationSettings: "'FILL' 1" }}>psychology</span>
                </div>
                <div className="space-y-3 max-w-[80%]">
                  {toolSteps.length > 0 && (
                    <div className="bg-surface-container-high/40 rounded-xl p-3 space-y-1.5 border border-outline-variant/10">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="material-symbols-outlined text-secondary text-sm">account_tree</span>
                        <span className="text-[10px] font-label font-bold uppercase tracking-widest text-outline">思维链</span>
                      </div>
                      {toolSteps.map((step) => (
                        <div key={step.id} className="flex items-start gap-2">
                          <span className={`material-symbols-outlined text-xs mt-0.5 ${step.type === "start" ? "text-secondary" : "text-tertiary"}`}>
                            {step.type === "start" ? "play_arrow" : "check_circle"}
                          </span>
                          <div className="flex-1 min-w-0">
                            <span className="text-[10px] font-bold text-on-surface">{step.name}</span>
                            {step.detail && (
                              <p className="text-[9px] text-outline truncate">{step.detail}</p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  <div className="glass-card p-5 rounded-2xl rounded-tl-none border border-primary/20 shadow-[0_0_30px_rgba(186,158,255,0.05)]">
                    <p className="text-sm leading-relaxed text-on-surface whitespace-pre-line">
                      {aiReply || <span className="text-outline">正在思考中...</span>}
                    </p>
                    {citations.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-3">
                        {citations.map((c) => (
                          <span key={`${c.source_label}-${c.source_locator}`} className="text-[10px] bg-primary/10 text-primary px-2.5 py-1 rounded-full font-label border border-primary/20">
                            {c.source_label}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Composer */}
          <form onSubmit={handleSend} className="glass-card rounded-2xl border border-outline-variant/10 p-4 space-y-3">
            <div className="flex gap-2">
              {["上传资料", "生成测验", "开始专注"].map((tool) => (
                <button key={tool} type="button" className="text-[10px] font-label font-bold uppercase tracking-widest px-3 py-1.5 rounded-full bg-surface-container-high text-secondary hover:text-primary hover:bg-primary/10 transition-colors border border-outline-variant/10">
                  {tool}
                </button>
              ))}
            </div>
            <div className="flex gap-3 items-center">
              <input
                value={composer}
                onChange={(e) => setComposer(e.target.value)}
                placeholder="向你的 AI 学伴提问..."
                disabled={sending}
                className="flex-1 bg-surface-container-lowest rounded-xl px-4 py-3 text-sm text-on-surface placeholder:text-outline outline-none border border-outline-variant/30 focus:border-primary transition-colors disabled:opacity-60"
              />
              <button
                type="submit"
                disabled={sending || !composer.trim()}
                className="w-10 h-10 rounded-xl bg-primary text-on-primary flex items-center justify-center hover:scale-105 active:scale-95 transition-all disabled:opacity-60"
              >
                <span className="material-symbols-outlined text-base" style={{ fontVariationSettings: "'FILL' 1" }}>send</span>
              </button>
              {sending && (
                <button
                  type="button"
                  onClick={() => {
                    abortRef.current?.();
                    abortRef.current = null;
                    setSending(false);
                    setStatus("已停止生成。");
                  }}
                  className="w-10 h-10 rounded-xl bg-surface-container-high text-outline flex items-center justify-center hover:text-primary hover:bg-primary/10 transition-all border border-outline-variant/10"
                >
                  <span className="material-symbols-outlined text-base">stop</span>
                </button>
              )}
            </div>
            {status && <p className="text-[10px] text-outline">{status}</p>}
          </form>
        </div>

        {/* Right aside */}
        <aside className="w-64 flex-shrink-0 space-y-4 overflow-y-auto">
          {/* Focus timer */}
          <div className="glass-card rounded-3xl p-5 border border-outline-variant/10 text-center space-y-3">
            <span className="text-[10px] font-label font-bold uppercase tracking-widest text-outline">专注计时</span>
            <div className="text-4xl font-headline font-black text-tertiary">25:00</div>
            <p className="text-xs text-outline">{focusLabel}</p>
            <div className="flex gap-2">
              <button className="flex-1 bg-primary text-on-primary font-bold py-2 rounded-xl text-xs hover:scale-[1.02] active:scale-95 transition-all">开始</button>
              <button className="flex-1 bg-surface-container-high text-secondary font-bold py-2 rounded-xl text-xs hover:text-primary transition-colors">重置</button>
            </div>
          </div>

          {/* Knowledge map */}
          <div className="glass-card rounded-3xl p-5 border border-outline-variant/10 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-label font-bold uppercase tracking-widest text-outline">知识地图</span>
              <span className="text-secondary text-xs cursor-pointer hover:text-primary">↗</span>
            </div>
            <div className="flex flex-col items-center gap-2 py-2">
              <div className="w-10 h-10 rounded-full bg-tertiary flex items-center justify-center text-on-tertiary font-bold text-sm">✓</div>
              <div className="w-px h-4 bg-outline-variant/30" />
              <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center text-on-primary font-bold text-sm">✦</div>
              <div className="w-px h-4 bg-outline-variant/30" />
              <div className="w-10 h-10 rounded-full border-2 border-outline-variant flex items-center justify-center text-outline opacity-50">•</div>
            </div>
            <p className="text-[11px] text-outline text-center">当前节点：{currentNode}</p>
          </div>

          {/* Tutor persona */}
          <div className="glass-card rounded-3xl p-5 border border-outline-variant/10 space-y-3">
            <span className="text-[10px] font-label font-bold uppercase tracking-widest text-outline">辅导人格</span>
            <div className="space-y-2">
              {personaOptions.map((opt) => {
                const active = selectedPersona === opt.value;
                return (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => handlePersonaChange(opt.value as "gentle" | "strict" | "energetic")}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all text-left ${
                      active ? "bg-primary/10 border border-primary/20" : "bg-surface-container-high/40 border border-transparent hover:border-outline-variant/20"
                    }`}
                  >
                    <span className={`material-symbols-outlined text-base ${active ? "text-primary" : "text-outline"}`} style={active ? { fontVariationSettings: "'FILL' 1" } : {}}>
                      {opt.icon}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className={`text-xs font-bold ${active ? "text-primary" : "text-on-surface"}`}>{opt.title}</p>
                      <p className="text-[10px] text-outline">{opt.description}</p>
                    </div>
                    <span className={`text-sm ${active ? "text-primary" : "text-outline"}`}>{active ? "◉" : "○"}</span>
                  </button>
                );
              })}
            </div>
            <div className="flex gap-2 flex-wrap">
              <span className="text-[9px] bg-surface-container-high px-2 py-0.5 rounded-full text-outline font-label">
                {savingPersona ? "保存中..." : `人格：${selectedPersona}`}
              </span>
              <span className="text-[9px] bg-surface-container-high px-2 py-0.5 rounded-full text-outline font-label">
                资料：{documents.length}
              </span>
            </div>
          </div>
        </aside>
      </div>
    </WorkspaceFrame>
  );
}
