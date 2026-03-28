"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { startAskQuestionStream, type AskStreamEnvelope } from "@/lib/api";
import { useMvpData } from "@/hooks/use-mvp-data";
import { WorkspaceFrame } from "@/components/workspace-frame";

export default function DashboardPage() {
  const { loading, error, dashboard, scenes, documents, weakPoints, reviewTasks, buddyProfile, reload } = useMvpData("general");
  const [question, setQuestion] = useState("请根据当前资料总结 Redis 的三个关键考点。");
  const [qaAnswer, setQaAnswer] = useState("");
  const [qaCitations, setQaCitations] = useState<Array<{ source_label: string; source_locator: string }>>([]);
  const [status, setStatus] = useState("");
  const [qaStreaming, setQaStreaming] = useState(false);
  const [qaSteps, setQaSteps] = useState<Array<{ id: string; title: string; detail?: string }>>([]);
  const abortRef = useRef<null | (() => void)>(null);

  useEffect(() => {
    return () => {
      abortRef.current?.();
    };
  }, []);

  const stats = useMemo(
    () => [
      { label: "知识资产", value: String(documents.length).padStart(2, "0"), icon: "description", color: "text-primary" },
      { label: "薄弱点", value: String(weakPoints.length).padStart(2, "0"), icon: "warning", color: "text-error" },
      { label: "待复习", value: String(reviewTasks.length).padStart(2, "0"), icon: "event_note", color: "text-tertiary" },
    ],
    [documents.length, reviewTasks.length, weakPoints.length],
  );

  async function handleAsk(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    abortRef.current?.();
    setQaAnswer("");
    setQaCitations([]);
    setQaSteps([]);
    setStatus("请求已发送，等待模型响应...");
    setQaStreaming(true);

    const onEvent = (ev: AskStreamEnvelope) => {
      const data = (ev as AskStreamEnvelope).data as any;
      if (!data || typeof data.type !== "string") return;

      if (data.type === "status") {
        if (typeof data.content === "string") setStatus(data.content);
        return;
      }

      if (data.type === "tool_start") {
        setQaSteps((prev) => {
          const next = prev.concat([{ id: `tool_start_${data.step ?? prev.length}`, title: `开始工具：${data.tool_name ?? "unknown"}`, detail: JSON.stringify(data.input ?? "") }]);
          return next.slice(-60);
        });
        return;
      }

      if (data.type === "tool_end") {
        setQaSteps((prev) => {
          const next = prev.concat([{ id: `tool_end_${data.step ?? prev.length}`, title: `结束工具：${data.tool_name ?? "unknown"}`, detail: String(data.output ?? "") }]);
          return next.slice(-60);
        });
        return;
      }

      if (data.type === "token") {
        if (typeof data.content === "string" && data.content) {
          setQaAnswer((prev) => prev + data.content);
        }
        return;
      }

      if (data.type === "final") {
        setQaAnswer(String(data.answer ?? ""));
        const citations = Array.isArray(data.citations) ? data.citations : [];
        setQaCitations(citations.map((c: any) => ({ source_label: String(c?.source_label ?? ""), source_locator: String(c?.source_locator ?? "") })));
        setStatus("问答完成。");
        setQaStreaming(false);
        abortRef.current = null;
        return;
      }

      if (data.type === "error") {
        setStatus(ev.message || "问答失败。");
        setQaStreaming(false);
        abortRef.current = null;
      }
    };

    abortRef.current = startAskQuestionStream(
      { scene_id: "general", session_id: null, question },
      onEvent,
      () => {
        setStatus("流式请求失败，请检查后端服务与网络。");
        setQaStreaming(false);
        abortRef.current = null;
      },
    );
  }

  return (
    <WorkspaceFrame badge="学习中枢" title="学习中枢" subtitle="AI 学伴、技能图谱与学习进度一览，开启高效学习之旅。">
      <div className="grid grid-cols-12 gap-6">
        <section className="col-span-12 lg:col-span-4 space-y-5">
          <div className="bg-gradient-to-br from-primary/20 to-secondary/20 rounded-3xl p-5 border border-primary/20 relative overflow-hidden">
            <div className="absolute -right-4 -bottom-4 w-24 h-24 bg-primary/20 blur-3xl" />
            <div className="relative z-10">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 rounded-xl bg-surface-bright flex items-center justify-center">
                  <span className="material-symbols-outlined text-primary text-base" style={{ fontVariationSettings: "'FILL' 1" }}>psychology</span>
                </div>
                <h4 className="font-headline font-bold text-primary text-sm">{buddyProfile?.name ?? "小智"}</h4>
              </div>
              <p className="text-sm text-on-surface leading-relaxed">
                {buddyProfile?.memory_summary ?? "欢迎回来，今天继续把知识点吃透。"}
              </p>
            </div>
          </div>

          <div className="glass-card rounded-3xl p-5 border border-outline-variant/10 shadow-xl space-y-4">
            <div>
              <div className="flex justify-between items-end mb-1">
                <span className="text-[10px] font-label uppercase tracking-widest text-outline font-bold">当前等级</span>
                <span className="text-[10px] font-label font-bold text-primary">850/1000 经验</span>
              </div>
              <h3 className="text-lg font-headline font-black text-on-surface">Lv.42 学习架构师</h3>
              <div className="h-2.5 w-full bg-surface-container-lowest rounded-full mt-2 p-[2px]">
                <div className="h-full bg-gradient-to-r from-primary to-tertiary rounded-full w-[85%] relative">
                  <div className="absolute right-0 top-0 h-full w-3 bg-white/20 blur-sm" />
                </div>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-3">
              {stats.map((stat) => (
                <div key={stat.label} className="bg-surface-container-high/40 p-3 rounded-2xl border border-outline-variant/10 text-center">
                  <span className={`material-symbols-outlined text-base block mb-1 ${stat.color}`} style={{ fontVariationSettings: "'FILL' 1" }}>{stat.icon}</span>
                  <p className="text-lg font-headline font-black text-on-surface leading-none">{stat.value}</p>
                  <p className="text-[9px] font-label uppercase text-outline mt-1 leading-tight">{stat.label}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="glass-card rounded-3xl p-5 border border-outline-variant/10 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-headline font-bold text-on-surface">今日艾宾浩斯复习</h3>
              <span className="bg-error/20 text-error text-[10px] px-2 py-0.5 rounded-full font-bold">优先处理</span>
            </div>
            <div className="space-y-2">
              {(weakPoints.length > 0 ? weakPoints : [
                { id: 1, concept: "SQL Joins", source_type: "note", correct_rate: 40 },
                { id: 2, concept: "RAG Architectures", source_type: "material", correct_rate: 55 },
              ]).slice(0, 4).map((item) => (
                <div key={item.id} className="flex items-center justify-between p-3 rounded-xl bg-surface-container-high/40 hover:bg-surface-container-high/60 transition-colors cursor-pointer group">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-surface-container-highest flex items-center justify-center">
                      <span className="material-symbols-outlined text-xs text-secondary">psychology</span>
                    </div>
                    <div>
                      <p className="text-xs font-bold text-on-surface">{item.concept}</p>
                      <p className="text-[9px] text-outline">{item.correct_rate}% 正确率</p>
                    </div>
                  </div>
                  <span className="material-symbols-outlined text-outline group-hover:text-primary transition-colors text-sm">chevron_right</span>
                </div>
              ))}
              <button className="w-full text-center py-2 text-[10px] font-label font-bold text-outline hover:text-primary transition-colors">
                查看全部 {weakPoints.length} 项
              </button>
            </div>
          </div>
        </section>

        <section className="col-span-12 lg:col-span-8 space-y-5">
          <div className="glass-card rounded-3xl p-6 border border-outline-variant/10 shadow-xl min-h-[360px] relative overflow-hidden">
            <div className="absolute inset-0 opacity-5 pointer-events-none" style={{ backgroundImage: "radial-gradient(circle at 50% 50%, #ba9eff 1px, transparent 1px)", backgroundSize: "30px 30px" }} />
            <div className="flex items-center justify-between mb-6 relative z-10">
              <div>
                <h2 className="text-xl font-headline font-bold text-on-surface">技能图谱</h2>
                <p className="text-xs text-outline font-label">交互式掌握路径图</p>
              </div>
              <div className="flex gap-2">
                <span className="px-2.5 py-1 bg-tertiary/10 text-tertiary text-[10px] font-bold rounded-full border border-tertiary/20">已掌握</span>
                <span className="px-2.5 py-1 bg-secondary/10 text-secondary text-[10px] font-bold rounded-full border border-secondary/20">学习中</span>
                <span className="px-2.5 py-1 bg-outline/10 text-outline text-[10px] font-bold rounded-full border border-outline/20">未解锁</span>
              </div>
            </div>
            <div className="relative flex items-center justify-center h-64">
              <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-20">
                <line stroke="#dee5ff" strokeWidth="2" x1="50%" x2="30%" y1="15%" y2="45%" />
                <line stroke="#dee5ff" strokeWidth="2" x1="50%" x2="70%" y1="15%" y2="45%" />
                <line stroke="#dee5ff" strokeWidth="2" x1="30%" x2="25%" y1="45%" y2="75%" />
                <line stroke="#dee5ff" strokeWidth="2" x1="70%" x2="60%" y1="45%" y2="75%" />
                <line stroke="#dee5ff" strokeWidth="2" x1="70%" x2="80%" y1="45%" y2="75%" />
              </svg>
              <div className="absolute top-[5%] left-1/2 -translate-x-1/2 group cursor-pointer">
                <div className="w-16 h-16 rounded-full bg-tertiary shadow-[0_0_20px_rgba(155,255,206,0.3)] flex flex-col items-center justify-center text-on-tertiary transition-transform group-hover:scale-110">
                  <span className="material-symbols-outlined text-2xl" style={{ fontVariationSettings: "'FILL' 1" }}>star</span>
                  <span className="text-[8px] font-bold uppercase mt-0.5">核心</span>
                </div>
                <div className="absolute -bottom-5 left-1/2 -translate-x-1/2 whitespace-nowrap text-xs font-bold text-on-surface">核心能力</div>
              </div>
              <div className="absolute top-[38%] left-[22%] group cursor-pointer">
                <div className="w-12 h-12 rounded-full bg-secondary shadow-[0_0_16px_rgba(119,153,255,0.3)] flex flex-col items-center justify-center text-on-secondary transition-transform group-hover:scale-110">
                  <span className="material-symbols-outlined text-xl">work</span>
                  <span className="text-[7px] font-bold uppercase mt-0.5">求职</span>
                </div>
                <div className="absolute -bottom-5 left-1/2 -translate-x-1/2 whitespace-nowrap text-xs font-bold text-on-surface">职业能力</div>
              </div>
              <div className="absolute top-[38%] left-[62%] group cursor-pointer">
                <div className="w-12 h-12 rounded-full bg-outline shadow-lg flex flex-col items-center justify-center text-surface transition-transform group-hover:scale-110">
                  <span className="material-symbols-outlined text-xl">history_edu</span>
                  <span className="text-[7px] font-bold uppercase mt-0.5">应试</span>
                </div>
                <div className="absolute -bottom-5 left-1/2 -translate-x-1/2 whitespace-nowrap text-xs font-bold text-on-surface">考试能力</div>
              </div>
              {[{ left: "20%" }, { left: "52%" }, { left: "74%" }].map((pos, i) => (
                <div key={i} className="absolute top-[72%]" style={{ left: pos.left }}>
                  <div className="w-10 h-10 rounded-full border-2 border-outline-variant flex items-center justify-center text-outline-variant opacity-50 cursor-not-allowed">
                    <span className="material-symbols-outlined text-sm">lock</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="glass-card rounded-3xl p-6 border border-outline-variant/10 shadow-xl">
            <div className="flex items-center gap-2 mb-4">
              <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>psychology</span>
              <h3 className="font-headline font-bold text-on-surface">向知识库提问</h3>
            </div>
            <form className="space-y-3" onSubmit={handleAsk}>
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                rows={4}
                disabled={qaStreaming}
                className="w-full bg-surface-container-lowest rounded-xl px-4 py-3 text-sm text-on-surface placeholder:text-outline outline-none border-b-2 border-transparent focus:border-primary transition-colors resize-none"
                placeholder="输入你的问题..."
              />
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="submit"
                  disabled={qaStreaming}
                  className="w-full bg-primary text-on-primary font-bold py-2.5 rounded-xl text-sm hover:scale-[1.01] active:scale-95 transition-all disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  {qaStreaming ? "生成中..." : "发送问题"}
                </button>
                <button
                  type="button"
                  disabled={!qaStreaming}
                  onClick={() => {
                    abortRef.current?.();
                    abortRef.current = null;
                    setQaStreaming(false);
                    setStatus("已停止生成。");
                  }}
                  className="w-full bg-surface-container-high text-outline font-bold py-2.5 rounded-xl text-sm hover:text-primary hover:bg-primary/10 transition-all border border-outline-variant/10 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  停止
                </button>
              </div>
            </form>
            {qaAnswer && (
              <div className="mt-4 bg-surface-container-high/40 rounded-xl p-4 space-y-2">
                <p className="text-sm text-on-surface whitespace-pre-line leading-relaxed">{qaAnswer}</p>
                {qaCitations.length > 0 && (
                  <div className="flex flex-wrap gap-2 pt-2 border-t border-outline-variant/20">
                    {qaCitations.map((c, i) => (
                      <span key={i} className="text-[10px] bg-primary/10 text-primary px-2.5 py-1 rounded-full font-label border border-primary/20">
                        {c.source_label}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
            {qaSteps.length > 0 && (
              <div className="mt-3 bg-surface-container-high/20 rounded-xl p-3 max-h-32 overflow-y-auto">
                {qaSteps.map((step) => (
                  <div key={step.id} className="text-[10px] text-outline mb-1">
                    <span className="text-secondary">{step.title}</span>
                    {step.detail && <span className="ml-2 opacity-60">{step.detail.slice(0, 80)}...</span>}
                  </div>
                ))}
              </div>
            )}
            {status && <p className="mt-2 text-[10px] text-outline">{status}</p>}
          </div>
        </section>

        <section className="col-span-12">
          <div className="glass-card rounded-3xl p-6 border border-outline-variant/10 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-secondary">description</span>
                <h3 className="font-headline font-bold text-on-surface">最近资料</h3>
              </div>
              <span className="text-[10px] font-label text-outline">共 {documents.length} 份</span>
            </div>
            {documents.length === 0 ? (
              <div className="text-center py-8">
                <span className="material-symbols-outlined text-outline text-3xl mb-2 block">folder_off</span>
                <p className="text-sm text-outline">暂无资料，请前往知识库上传</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {documents.slice(0, 6).map((item) => (
                  <div key={item.id} className="flex items-center gap-3 p-3 rounded-xl bg-surface-container-high/40 hover:bg-surface-container-high/60 transition-colors cursor-pointer group">
                    <div className="w-10 h-10 rounded-lg bg-surface-container-highest flex items-center justify-center flex-shrink-0">
                      <span className="material-symbols-outlined text-secondary text-lg">description</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-bold text-on-surface truncate">{item.filename}</p>
                      <p className="text-[9px] text-outline truncate">{item.summary || "暂无摘要"}</p>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0 ml-2">
                      <span className="text-[9px] bg-surface-container-highest px-2 py-0.5 rounded-full text-outline">{item.doc_type}</span>
                      <span className="text-[9px] bg-tertiary/10 text-tertiary px-2 py-0.5 rounded-full">{item.status}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>
      </div>
    </WorkspaceFrame>
  );
}
