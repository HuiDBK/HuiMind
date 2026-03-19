"use client";

import { useMemo, useState } from "react";

import { answerInterviewQuestion, createInterviewSession, createJd, getInterviewSession, runResumeDiagnosis } from "@/lib/api";
import { useMvpData } from "@/hooks/use-mvp-data";
import { WorkspaceFrame } from "@/components/workspace-frame";

export default function CareerPage() {
  const { documents } = useMvpData("career");
  const [jdForm, setJdForm] = useState({ title: "后端开发工程师", content: "负责 API 设计、MySQL 建模和 Redis 缓存优化。", source_url: "" });
  const [diagnosisForm, setDiagnosisForm] = useState({ resume_doc_id: 2002, jd_doc_id: 2003 });
  const [interviewForm, setInterviewForm] = useState({ jd_doc_id: 2003, mode: "standard" as "standard" | "pressure" });
  const [interviewAnswer, setInterviewAnswer] = useState("我会先梳理流量入口，再排查接口、数据库和缓存的瓶颈位置。");
  const [diagnosis, setDiagnosis] = useState<Awaited<ReturnType<typeof runResumeDiagnosis>> | null>(null);
  const [session, setSession] = useState<Awaited<ReturnType<typeof createInterviewSession>> | null>(null);
  const [sessionDetail, setSessionDetail] = useState<Awaited<ReturnType<typeof getInterviewSession>> | null>(null);
  const [answerResult, setAnswerResult] = useState<Awaited<ReturnType<typeof answerInterviewQuestion>> | null>(null);

  const resumeName = useMemo(
    () => documents.find((d) => d.doc_type === "resume")?.filename ?? "backend-resume.pdf",
    [documents],
  );

  async function handleCreateJd(event: React.SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    await createJd({ scene_id: "career", title: jdForm.title, content: jdForm.content || undefined, source_url: jdForm.source_url || undefined });
  }

  async function handleDiagnosis(event: React.SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    const result = await runResumeDiagnosis({ scene_id: "career", ...diagnosisForm });
    setDiagnosis(result);
  }

  async function handleCreateSession(event: React.SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    const result = await createInterviewSession({ scene_id: "career", ...interviewForm });
    setSession(result);
    setSessionDetail(await getInterviewSession(result.session_id));
  }

  async function handleSubmitAnswer(event: React.SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session?.questions[0]) return;
    const result = await answerInterviewQuestion({ sessionId: session.session_id, turnId: session.questions[0].turn_id, answer: interviewAnswer });
    setAnswerResult(result);
    setSessionDetail(await getInterviewSession(session.session_id));
  }

  const matchScore = diagnosis ? Math.round(diagnosis.match_score) : 78;
  const circumference = 2 * Math.PI * 58; // r=58
  const dashOffset = circumference * (1 - matchScore / 100);

  return (
    <WorkspaceFrame badge="职业发展" title="职业发展场景" subtitle="把简历诊断、JD 工作台和模拟面试整合进同一个求职中枢。">

      {/* Hero breadcrumb + match gauge */}
      <div className="flex items-end justify-between mb-6">
        <div>
          <div className="flex items-center gap-2 text-[10px] font-label font-bold uppercase tracking-widest text-on-surface-variant">
            <span>求职助手</span>
            <span className="material-symbols-outlined text-sm">chevron_right</span>
            <span className="text-primary">简历诊断</span>
          </div>
          <h3 className="text-3xl font-headline font-bold text-on-surface mt-1">优化你的求职策略</h3>
        </div>
        {/* Gauge */}
        <div className="relative w-28 h-28 flex items-center justify-center flex-shrink-0">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 128 128">
            <circle className="text-surface-container-high" cx="64" cy="64" fill="transparent" r="58" stroke="currentColor" strokeWidth="8" />
            <circle
              className="text-primary transition-all duration-1000"
              cx="64" cy="64" fill="transparent" r="58"
              stroke="currentColor"
              strokeDasharray={circumference}
              strokeDashoffset={dashOffset}
              strokeLinecap="round"
              strokeWidth="8"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-2xl font-headline font-black text-on-surface">{matchScore}%</span>
            <span className="text-[9px] font-label font-bold text-primary uppercase tracking-tighter">岗位匹配度</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">

        {/* Resume preview — col 5 */}
        <section className="col-span-12 lg:col-span-5">
          <div className="glass-card rounded-3xl border border-outline-variant/10 shadow-xl overflow-hidden">
            {/* Window bar */}
            <div className="flex items-center justify-between px-4 py-3 bg-surface-container-high/60 border-b border-outline-variant/10">
              <span className="text-xs text-on-surface-variant font-label">{resumeName}</span>
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-error/60" />
                <div className="w-3 h-3 rounded-full bg-[#ffb36d]/60" />
                <div className="w-3 h-3 rounded-full bg-tertiary/60" />
              </div>
            </div>
            <div className="p-5 space-y-4">
              <div className="text-center pb-3 border-b border-outline-variant/10">
                <p className="font-headline font-black text-on-surface text-lg">ALEX RIVERS</p>
                <p className="text-xs text-outline mt-1">FastAPI / MySQL / Redis / System Design</p>
              </div>
              <div>
                <h4 className="text-[10px] font-label font-bold uppercase tracking-widest text-outline mb-2">经历亮点</h4>
                <ul className="space-y-2">
                  <li className="text-xs text-tertiary leading-relaxed pl-3 border-l-2 border-tertiary/40">
                    主导 API 重构，6 个月内将业务看板留存提升 24%。
                  </li>
                  <li className="text-xs text-[#ffb36d] leading-relaxed pl-3 border-l-2 border-[#ffb36d]/40">
                    负责后端模块开发与系统维护，但产出表达仍可进一步量化。
                  </li>
                  <li className="text-xs text-on-surface-variant leading-relaxed pl-3 border-l-2 border-outline-variant/20">
                    为内部工具搭建共享数据模型，并落地基于 Redis 的缓存流程。
                  </li>
                </ul>
              </div>
              <div>
                <h4 className="text-[10px] font-label font-bold uppercase tracking-widest text-outline mb-2">核心技能</h4>
                <div className="flex flex-wrap gap-2">
                  {["FastAPI", "MySQL", "Redis", "RAG"].map((s) => (
                    <span key={s} className="text-[10px] bg-primary/10 text-primary px-2.5 py-1 rounded-full font-label border border-primary/20">{s}</span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Diagnosis report — col 7 */}
        <section className="col-span-12 lg:col-span-7 space-y-4">
          <div className="glass-card rounded-3xl p-6 border border-outline-variant/10 shadow-xl">
            <div className="flex items-center gap-2 mb-4">
              <span className="material-symbols-outlined text-primary">analytics</span>
              <h3 className="font-headline font-bold text-on-surface">诊断报告</h3>
              <span className="text-[10px] font-label text-outline ml-auto">差距分析</span>
            </div>
            <div className="space-y-4">
              <div className="bg-surface-container-high/40 rounded-2xl p-4">
                <p className="text-[10px] font-label font-bold uppercase tracking-widest text-error mb-2">缺失关键词</p>
                <div className="flex flex-wrap gap-2">
                  {(diagnosis?.missing_keywords ?? ["高并发", "监控告警", "异步任务"]).map((kw) => (
                    <span key={kw} className="text-[10px] bg-error/10 text-error px-2.5 py-1 rounded-full font-label border border-error/20">{kw}</span>
                  ))}
                </div>
              </div>
              <div className="bg-surface-container-high/40 rounded-2xl p-4">
                <p className="text-[10px] font-label font-bold uppercase tracking-widest text-tertiary mb-2">已匹配技能</p>
                <div className="flex flex-wrap gap-2">
                  {(diagnosis?.matched_keywords ?? ["FastAPI", "MySQL", "Redis"]).map((kw) => (
                    <span key={kw} className="text-[10px] bg-tertiary/10 text-tertiary px-2.5 py-1 rounded-full font-label border border-tertiary/20">{kw}</span>
                  ))}
                </div>
              </div>
              <div className="space-y-2">
                <p className="text-[10px] font-label font-bold uppercase tracking-widest text-outline">改写建议</p>
                {(diagnosis?.rewrite_suggestions ?? [{ original: "负责一些后端开发工作", rewritten: "负责 FastAPI 后端接口开发与 MySQL 数据建模，支撑核心业务模块上线。" }]).map((item) => (
                  <div key={item.original} className="bg-surface-container-high/40 rounded-xl p-3 border-l-2 border-primary/40">
                    <p className="text-[10px] text-outline line-through mb-1">{item.original}</p>
                    <p className="text-xs text-on-surface">{item.rewritten}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* JD Studio — col 6 */}
        <section className="col-span-12 lg:col-span-6">
          <div className="glass-card rounded-3xl p-6 border border-outline-variant/10 shadow-xl space-y-4">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-secondary">work</span>
              <h3 className="font-headline font-bold text-on-surface">JD 工作台</h3>
              <span className="text-[10px] font-label text-outline ml-auto">目标岗位</span>
            </div>
            <form className="space-y-3" onSubmit={handleCreateJd}>
              <input
                value={jdForm.title}
                onChange={(e) => setJdForm({ ...jdForm, title: e.target.value })}
                className="w-full bg-surface-container-lowest rounded-xl px-4 py-2.5 text-sm text-on-surface outline-none border-b-2 border-transparent focus:border-primary transition-colors"
                placeholder="岗位名称"
              />
              <textarea
                value={jdForm.content}
                onChange={(e) => setJdForm({ ...jdForm, content: e.target.value })}
                rows={4}
                className="w-full bg-surface-container-lowest rounded-xl px-4 py-2.5 text-sm text-on-surface outline-none border border-outline-variant/30 focus:border-primary transition-colors resize-none"
                placeholder="岗位描述..."
              />
              <button type="submit" className="w-full bg-surface-container-high text-secondary font-bold py-2.5 rounded-xl text-sm hover:text-primary hover:bg-primary/10 transition-all border border-outline-variant/10">
                生成 JD 模拟数据
              </button>
            </form>
            <form className="space-y-3" onSubmit={handleDiagnosis}>
              <div className="grid grid-cols-2 gap-3">
                <input
                  type="number"
                  value={diagnosisForm.resume_doc_id}
                  onChange={(e) => setDiagnosisForm({ ...diagnosisForm, resume_doc_id: Number(e.target.value) })}
                  className="bg-surface-container-lowest rounded-xl px-4 py-2.5 text-sm text-on-surface outline-none border border-outline-variant/30 focus:border-primary transition-colors"
                  placeholder="简历文档 ID"
                />
                <input
                  type="number"
                  value={diagnosisForm.jd_doc_id}
                  onChange={(e) => setDiagnosisForm({ ...diagnosisForm, jd_doc_id: Number(e.target.value) })}
                  className="bg-surface-container-lowest rounded-xl px-4 py-2.5 text-sm text-on-surface outline-none border border-outline-variant/30 focus:border-primary transition-colors"
                  placeholder="JD 文档 ID"
                />
              </div>
              <button type="submit" className="w-full bg-primary text-on-primary font-bold py-2.5 rounded-xl text-sm hover:scale-[1.01] active:scale-95 transition-all">
                开始诊断
              </button>
            </form>
          </div>
        </section>

        {/* Interview Lab — col 6 */}
        <section className="col-span-12 lg:col-span-6">
          <div className="glass-card rounded-3xl p-6 border border-outline-variant/10 shadow-xl space-y-4">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-secondary">record_voice_over</span>
              <h3 className="font-headline font-bold text-on-surface">模拟面试</h3>
              <span className="text-[10px] font-label text-outline ml-auto">面试演练</span>
            </div>
            <form className="space-y-3" onSubmit={handleCreateSession}>
              <div className="grid grid-cols-2 gap-3">
                <input
                  type="number"
                  value={interviewForm.jd_doc_id}
                  onChange={(e) => setInterviewForm({ ...interviewForm, jd_doc_id: Number(e.target.value) })}
                  className="bg-surface-container-lowest rounded-xl px-4 py-2.5 text-sm text-on-surface outline-none border border-outline-variant/30 focus:border-primary transition-colors"
                  placeholder="JD 文档 ID"
                />
                <select
                  value={interviewForm.mode}
                  onChange={(e) => setInterviewForm({ ...interviewForm, mode: e.target.value as "standard" | "pressure" })}
                  className="bg-surface-container-lowest rounded-xl px-4 py-2.5 text-sm text-on-surface outline-none"
                >
                  <option value="standard">标准模式</option>
                  <option value="pressure">压力模式</option>
                </select>
              </div>
              <button type="submit" className="w-full bg-surface-container-high text-secondary font-bold py-2.5 rounded-xl text-sm hover:text-primary hover:bg-primary/10 transition-all border border-outline-variant/10">
                创建模拟面试
              </button>
            </form>

            <div className="bg-surface-container-high/40 rounded-xl p-4">
              <p className="text-[10px] font-label font-bold uppercase tracking-widest text-outline mb-2">当前题目</p>
              <p className="text-sm text-on-surface">{session?.questions[0]?.question ?? "先创建一个面试会话，再查看第一道题。"}</p>
            </div>

            <form className="space-y-3" onSubmit={handleSubmitAnswer}>
              <textarea
                value={interviewAnswer}
                onChange={(e) => setInterviewAnswer(e.target.value)}
                rows={4}
                className="w-full bg-surface-container-lowest rounded-xl px-4 py-2.5 text-sm text-on-surface outline-none border border-outline-variant/30 focus:border-primary transition-colors resize-none"
              />
              <button type="submit" className="w-full bg-primary text-on-primary font-bold py-2.5 rounded-xl text-sm hover:scale-[1.01] active:scale-95 transition-all">
                提交回答
              </button>
            </form>

            {answerResult && (
              <div className="bg-surface-container-high/40 rounded-xl p-4 border-l-4 border-tertiary">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-2xl font-headline font-black text-tertiary">{answerResult.score}</span>
                  <span className="text-[10px] font-label text-outline">/ 100</span>
                </div>
                <p className="text-xs text-on-surface-variant">{answerResult.feedback.comment}</p>
              </div>
            )}
          </div>
        </section>

        {/* Interview timeline */}
        {sessionDetail && (
          <section className="col-span-12">
            <div className="glass-card rounded-3xl p-6 border border-outline-variant/10 shadow-xl">
              <div className="flex items-center gap-2 mb-4">
                <span className="material-symbols-outlined text-secondary">timeline</span>
                <h3 className="font-headline font-bold text-on-surface">面试时间线</h3>
                <span className="text-[10px] font-label text-outline ml-auto">会话记录</span>
              </div>
              <div className="space-y-2">
                {sessionDetail.turns.map((turn) => (
                  <div key={turn.turn_id} className="flex items-center justify-between p-3 rounded-xl bg-surface-container-high/40 hover:bg-surface-container-high/60 transition-colors">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-8 h-8 rounded-lg bg-surface-container-highest flex items-center justify-center flex-shrink-0">
                        <span className="material-symbols-outlined text-xs text-secondary">chat</span>
                      </div>
                      <div className="min-w-0">
                        <p className="text-xs font-bold text-on-surface truncate">{turn.question}</p>
                        <p className="text-[10px] text-outline truncate">{turn.answer ?? "等待作答"}</p>
                      </div>
                    </div>
                    <span className={`text-xs font-bold ml-3 flex-shrink-0 ${turn.score ? "text-tertiary" : "text-outline"}`}>
                      {turn.score ?? "--"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

      </div>
    </WorkspaceFrame>
  );
}
