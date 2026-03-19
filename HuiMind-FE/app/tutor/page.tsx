"use client";

import { useState } from "react";

import { askQuestion, chatWithBuddy, updateBuddyProfile } from "@/lib/api";
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
  const [composer, setComposer] = useState("请结合我的资料，解释一下 RAG 和普通 LLM 提示的区别。");
  const [lastUserPrompt, setLastUserPrompt] = useState("请结合我昨天上传的文档，解释一下 RAG 和普通 LLM 提示的区别。");
  const [aiReply, setAiReply] = useState(
    "你可以把普通 LLM 理解成只依赖自身记忆的专家，它知道很多通用知识，但看不到你最新上传的资料。RAG 则像先去图书馆检索资料，再基于检索到的片段组织回答，因此能把输出建立在你的文档事实上。",
  );
  const [citations, setCitations] = useState([
    { source_label: "[1] Resume_v2.pdf", source_locator: "chunk-3" },
    { source_label: "[2] Wiki_Intro.html", source_locator: "section-1" },
  ]);
  const [savingPersona, setSavingPersona] = useState(false);
  const [sending, setSending] = useState(false);

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
    if (!prompt) return;
    setSending(true);
    setLastUserPrompt(prompt);
    try {
      const [qa, buddy] = await Promise.all([
        askQuestion({ scene_id: "general", question: prompt }),
        chatWithBuddy({ scene_id: "general", message: prompt }),
      ]);
      setAiReply(`${qa.answer}\n\n${buddy.reply}`);
      setCitations(qa.citations.map((c) => ({ source_label: c.source_label, source_locator: c.source_locator })));
      setComposer("");
    } finally {
      setSending(false);
    }
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
            {/* User message */}
            <div className="flex justify-end">
              <div className="bg-surface-container-high px-5 py-3 rounded-2xl rounded-tr-none max-w-[75%] border border-outline-variant/10">
                <p className="text-sm leading-relaxed text-on-surface">{lastUserPrompt}</p>
              </div>
            </div>

            {/* AI message */}
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center flex-shrink-0 mt-1">
                <span className="material-symbols-outlined text-primary text-base" style={{ fontVariationSettings: "'FILL' 1" }}>psychology</span>
              </div>
              <div className="space-y-3 max-w-[80%]">
                <div className="glass-card p-5 rounded-2xl rounded-tl-none border border-primary/20 shadow-[0_0_30px_rgba(186,158,255,0.05)]">
                  <p className="text-sm leading-relaxed text-on-surface whitespace-pre-line">{aiReply}</p>
                  <div className="flex flex-wrap gap-2 mt-3">
                    {citations.map((c) => (
                      <span key={`${c.source_label}-${c.source_locator}`} className="text-[10px] bg-primary/10 text-primary px-2.5 py-1 rounded-full font-label border border-primary/20">
                        {c.source_label}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Quiz card */}
                <div className="bg-surface-container-high/60 rounded-2xl p-4 border border-outline-variant/10">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-tertiary font-bold">⚡</span>
                    <span className="text-[10px] font-label font-bold uppercase tracking-widest text-tertiary">快速测验</span>
                  </div>
                  <p className="text-sm text-on-surface mb-3">在 RAG 架构中，LLM 生成回答之前会先发生什么？</p>
                  <div className="space-y-2">
                    <button className="w-full text-left px-4 py-2.5 rounded-xl bg-surface-container-highest text-sm text-on-surface-variant hover:bg-surface-container-highest/80 transition-colors">
                      A) 随机编造一个事实
                    </button>
                    <button className="w-full text-left px-4 py-2.5 rounded-xl bg-tertiary/10 border border-tertiary/30 text-sm text-tertiary font-medium flex justify-between items-center">
                      <span>B) 检索相关文档片段</span>
                      <span className="text-tertiary">✓</span>
                    </button>
                    <button className="w-full text-left px-4 py-2.5 rounded-xl bg-surface-container-highest text-sm text-on-surface-variant hover:bg-surface-container-highest/80 transition-colors">
                      C) 重新训练整个模型
                    </button>
                  </div>
                </div>
              </div>
            </div>
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
                className="flex-1 bg-surface-container-lowest rounded-xl px-4 py-3 text-sm text-on-surface placeholder:text-outline outline-none border border-outline-variant/30 focus:border-primary transition-colors"
              />
              <button
                type="submit"
                disabled={sending}
                className="w-10 h-10 rounded-xl bg-primary text-on-primary flex items-center justify-center hover:scale-105 active:scale-95 transition-all disabled:opacity-60"
              >
                <span className="material-symbols-outlined text-base" style={{ fontVariationSettings: "'FILL' 1" }}>send</span>
              </button>
            </div>
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
