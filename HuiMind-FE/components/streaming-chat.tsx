"use client";

import { useRef, useState } from "react";

import { startAskQuestionStream, type AskStreamEnvelope } from "@/lib/api";
import type { SceneId } from "@/lib/types";

interface StreamingChatProps {
  sceneId: SceneId;
  onSceneChange?: (sceneId: SceneId) => void;
  showSceneSwitcher?: boolean;
  placeholder?: string;
  className?: string;
}

const sceneOptions: { id: SceneId; label: string; icon: string; description: string }[] = [
  { id: "general", label: "通用学习", icon: "school", description: "通用知识问答" },
  { id: "career", label: "求职助手", icon: "work", description: "简历诊断、模拟面试" },
  { id: "kaoyan", label: "考研备考", icon: "auto_stories", description: "专业课、政治、英语" },
  { id: "gongkao", label: "考公备考", icon: "account_balance", description: "行测、申论" },
];

export function StreamingChat({
  sceneId,
  onSceneChange,
  showSceneSwitcher = true,
  placeholder = "向你的 AI 学伴提问...",
  className = "",
}: StreamingChatProps) {
  const [selectedScene, setSelectedScene] = useState<SceneId>(sceneId);
  const [composer, setComposer] = useState("");
  const [lastUserPrompt, setLastUserPrompt] = useState("");
  const [aiReply, setAiReply] = useState("");
  const [citations, setCitations] = useState<Array<{ source_label: string; source_locator: string }>>([]);
  const [sending, setSending] = useState(false);
  const [status, setStatus] = useState("");
  const [toolSteps, setToolSteps] = useState<Array<{ id: string; type: "start" | "end"; name: string; detail?: string }>>([]);
  const abortRef = useRef<null | (() => void)>(null);

  async function handleSend(event: React.FormEvent<HTMLFormElement>) {
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
      { scene_id: selectedScene, session_id: null, question: prompt },
      onEvent,
      () => {
        setStatus("流式请求失败，请检查后端服务与网络。");
        setSending(false);
        abortRef.current = null;
      },
    );
    setComposer("");
  }

  function handleSceneChange(scene: SceneId) {
    if (!sending) {
      setSelectedScene(scene);
      setLastUserPrompt("");
      setAiReply("");
      setCitations([]);
      setToolSteps([]);
      onSceneChange?.(scene);
    }
  }

  return (
    <div className={`flex flex-col h-full ${className}`}>
      {showSceneSwitcher && (
        <div className="flex items-center gap-2 mb-4 px-1">
          {sceneOptions.map((scene) => {
            const isActive = selectedScene === scene.id;
            return (
              <button
                key={scene.id}
                type="button"
                onClick={() => handleSceneChange(scene.id)}
                disabled={sending}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold transition-all ${
                  isActive
                    ? "bg-primary text-on-primary shadow-lg shadow-primary/20"
                    : "bg-surface-container-high/60 text-secondary hover:text-primary hover:bg-primary/10 border border-outline-variant/10"
                } disabled:opacity-60 disabled:cursor-not-allowed`}
              >
                <span className="material-symbols-outlined text-base" style={isActive ? { fontVariationSettings: "'FILL' 1" } : {}}>
                  {scene.icon}
                </span>
                <span>{scene.label}</span>
              </button>
            );
          })}
        </div>
      )}

      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex-1 overflow-y-auto space-y-6 pb-4">
          {!lastUserPrompt && !aiReply && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center space-y-3">
                <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto">
                  <span className="material-symbols-outlined text-primary text-3xl" style={{ fontVariationSettings: "'FILL' 1" }}>psychology</span>
                </div>
                <p className="text-sm text-outline">{placeholder}</p>
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

        <form onSubmit={handleSend} className="glass-card rounded-2xl border border-outline-variant/10 p-4 space-y-3">
          <div className="flex gap-3 items-center">
            <input
              value={composer}
              onChange={(e) => setComposer(e.target.value)}
              placeholder={placeholder}
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
    </div>
  );
}

export { sceneOptions };
