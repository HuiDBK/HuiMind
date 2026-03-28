"use client";

import { useState } from "react";

import { useMvpData } from "@/hooks/use-mvp-data";
import { WorkspaceFrame } from "@/components/workspace-frame";

const subjectOptions = [
  { value: "math", label: "数学", icon: "calculate", progress: 65 },
  { value: "english", label: "英语", icon: "translate", progress: 72 },
  { value: "politics", label: "政治", icon: "gavel", progress: 45 },
  { value: "major", label: "专业课", icon: "auto_stories", progress: 58 },
];

const reviewPhases = [
  { phase: "基础阶段", period: "3-6月", status: "completed", color: "tertiary" },
  { phase: "强化阶段", period: "7-9月", status: "in_progress", color: "secondary" },
  { phase: "冲刺阶段", period: "10-12月", status: "pending", color: "outline" },
];

export default function KaoyanPage() {
  const { documents, weakPoints, reviewTasks } = useMvpData("kaoyan");
  const [selectedSubject, setSelectedSubject] = useState("math");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");

  const totalProgress = Math.round(subjectOptions.reduce((acc, s) => acc + s.progress, 0) / subjectOptions.length);

  return (
    <WorkspaceFrame badge="考研备考" title="考研备考场景" subtitle="专业课复习、公共课强化、真题模拟，一站式考研学习助手。">
      <div className="grid grid-cols-12 gap-6">
        <section className="col-span-12 lg:col-span-4 space-y-5">
          <div className="glass-card rounded-3xl p-5 border border-outline-variant/10 shadow-xl">
            <div className="flex items-center gap-2 mb-4">
              <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>school</span>
              <h3 className="font-headline font-bold text-on-surface">复习进度</h3>
            </div>
            <div className="text-center mb-4">
              <div className="relative w-28 h-28 mx-auto">
                <svg className="w-full h-full -rotate-90" viewBox="0 0 128 128">
                  <circle className="text-surface-container-high" cx="64" cy="64" fill="transparent" r="58" stroke="currentColor" strokeWidth="8" />
                  <circle
                    className="text-primary transition-all duration-1000"
                    cx="64" cy="64" fill="transparent" r="58"
                    stroke="currentColor"
                    strokeDasharray={2 * Math.PI * 58}
                    strokeDashoffset={2 * Math.PI * 58 * (1 - totalProgress / 100)}
                    strokeLinecap="round"
                    strokeWidth="8"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-2xl font-headline font-black text-on-surface">{totalProgress}%</span>
                  <span className="text-[9px] font-label text-outline">总体进度</span>
                </div>
              </div>
            </div>
            <div className="space-y-2">
              {subjectOptions.map((subject) => (
                <button
                  key={subject.value}
                  type="button"
                  onClick={() => setSelectedSubject(subject.value)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                    selectedSubject === subject.value
                      ? "bg-primary/10 border border-primary/20"
                      : "bg-surface-container-high/40 border border-transparent hover:border-outline-variant/20"
                  }`}
                >
                  <span className="material-symbols-outlined text-secondary">{subject.icon}</span>
                  <span className="flex-1 text-left text-sm font-bold text-on-surface">{subject.label}</span>
                  <div className="w-16 h-1.5 bg-surface-container-lowest rounded-full overflow-hidden">
                    <div className="h-full bg-primary rounded-full" style={{ width: `${subject.progress}%` }} />
                  </div>
                  <span className="text-xs text-outline">{subject.progress}%</span>
                </button>
              ))}
            </div>
          </div>

          <div className="glass-card rounded-3xl p-5 border border-outline-variant/10 shadow-xl">
            <div className="flex items-center gap-2 mb-4">
              <span className="material-symbols-outlined text-secondary">timeline</span>
              <h3 className="font-headline font-bold text-on-surface">复习阶段</h3>
            </div>
            <div className="space-y-3">
              {reviewPhases.map((phase, i) => (
                <div key={phase.phase} className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${phase.status === "completed" ? "bg-tertiary" : phase.status === "in_progress" ? "bg-secondary animate-pulse" : "bg-outline-variant"}`} />
                  <div className="flex-1">
                    <p className="text-sm font-bold text-on-surface">{phase.phase}</p>
                    <p className="text-[10px] text-outline">{phase.period}</p>
                  </div>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full ${
                    phase.status === "completed" ? "bg-tertiary/10 text-tertiary" :
                    phase.status === "in_progress" ? "bg-secondary/10 text-secondary" :
                    "bg-outline/10 text-outline"
                  }`}>
                    {phase.status === "completed" ? "已完成" : phase.status === "in_progress" ? "进行中" : "待开始"}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="glass-card rounded-3xl p-5 border border-outline-variant/10 shadow-xl">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-headline font-bold text-on-surface text-sm">薄弱知识点</h3>
              <span className="text-[10px] text-error font-bold">{weakPoints.length} 项</span>
            </div>
            <div className="space-y-2">
              {(weakPoints.length > 0 ? weakPoints : [
                { id: 1, concept: "高数极限", correct_rate: 45 },
                { id: 2, concept: "英语长难句", correct_rate: 52 },
              ]).slice(0, 4).map((item) => (
                <div key={item.id} className="flex items-center justify-between p-2 rounded-lg bg-surface-container-high/40">
                  <span className="text-xs text-on-surface">{item.concept}</span>
                  <span className="text-[10px] text-error">{item.correct_rate}%</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="col-span-12 lg:col-span-8 space-y-5">
          <div className="glass-card rounded-3xl p-6 border border-outline-variant/10 shadow-xl">
            <div className="flex items-center gap-2 mb-4">
              <span className="material-symbols-outlined text-tertiary" style={{ fontVariationSettings: "'FILL' 1" }}>quiz</span>
              <h3 className="font-headline font-bold text-on-surface">真题练习</h3>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
              {["数一真题", "数二真题", "英一真题", "英二真题"].map((name) => (
                <button key={name} className="p-4 rounded-xl bg-surface-container-high/40 hover:bg-surface-container-high/60 transition-colors text-center cursor-pointer">
                  <span className="material-symbols-outlined text-secondary text-xl mb-1 block">description</span>
                  <p className="text-xs font-bold text-on-surface">{name}</p>
                  <p className="text-[9px] text-outline">近10年</p>
                </button>
              ))}
            </div>
            <div className="bg-surface-container-high/40 rounded-xl p-4">
              <p className="text-[10px] font-label font-bold uppercase tracking-widest text-outline mb-2">今日推荐</p>
              <p className="text-sm text-on-surface mb-3">2024年数学一真题 - 第18题（线性代数）</p>
              <div className="flex gap-2">
                <button className="flex-1 bg-primary text-on-primary font-bold py-2 rounded-xl text-sm hover:scale-[1.01] active:scale-95 transition-all">
                  开始练习
                </button>
                <button className="px-4 bg-surface-container-high text-secondary font-bold py-2 rounded-xl text-sm hover:text-primary transition-colors border border-outline-variant/10">
                  查看解析
                </button>
              </div>
            </div>
          </div>

          <div className="glass-card rounded-3xl p-6 border border-outline-variant/10 shadow-xl">
            <div className="flex items-center gap-2 mb-4">
              <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>psychology</span>
              <h3 className="font-headline font-bold text-on-surface">AI 答疑</h3>
            </div>
            <div className="space-y-3">
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                rows={3}
                className="w-full bg-surface-container-lowest rounded-xl px-4 py-3 text-sm text-on-surface placeholder:text-outline outline-none border border-outline-variant/30 focus:border-primary transition-colors resize-none"
                placeholder="输入你的问题，AI 会结合你的资料给出解答..."
              />
              <button className="w-full bg-primary text-on-primary font-bold py-2.5 rounded-xl text-sm hover:scale-[1.01] active:scale-95 transition-all">
                提问
              </button>
            </div>
            {answer && (
              <div className="mt-4 bg-surface-container-high/40 rounded-xl p-4">
                <p className="text-sm text-on-surface">{answer}</p>
              </div>
            )}
          </div>

          <div className="glass-card rounded-3xl p-6 border border-outline-variant/10 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-secondary">event_note</span>
                <h3 className="font-headline font-bold text-on-surface">复习计划</h3>
              </div>
              <span className="text-[10px] font-label text-outline">{reviewTasks.length} 项待完成</span>
            </div>
            <div className="space-y-2">
              {(reviewTasks.length > 0 ? reviewTasks : [
                { id: 1, concept: "高数极限复习", due_at: "2024-01-15" },
                { id: 2, concept: "英语阅读理解", due_at: "2024-01-16" },
              ]).slice(0, 5).map((task) => (
                <div key={task.id} className="flex items-center justify-between p-3 rounded-xl bg-surface-container-high/40 hover:bg-surface-container-high/60 transition-colors cursor-pointer">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-surface-container-highest flex items-center justify-center">
                      <span className="material-symbols-outlined text-xs text-secondary">task_alt</span>
                    </div>
                    <div>
                      <p className="text-xs font-bold text-on-surface">{task.concept}</p>
                      <p className="text-[9px] text-outline">{task.due_at}</p>
                    </div>
                  </div>
                  <button className="text-[10px] bg-tertiary/10 text-tertiary px-3 py-1 rounded-full font-bold hover:bg-tertiary hover:text-on-tertiary transition-all">
                    完成
                  </button>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </WorkspaceFrame>
  );
}
