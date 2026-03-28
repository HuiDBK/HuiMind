"use client";

import { useState } from "react";

import { useMvpData } from "@/hooks/use-mvp-data";
import { WorkspaceFrame } from "@/components/workspace-frame";

const subjectOptions = [
  { value: "xingce", label: "行测", icon: "quiz", progress: 68 },
  { value: "shenlun", label: "申论", icon: "edit_document", progress: 55 },
  { value: "mianshi", label: "面试", icon: "record_voice_over", progress: 40 },
];

const shenlunTopics = [
  { id: 1, title: "基层治理创新", difficulty: "medium", attempts: 3 },
  { id: 2, title: "数字政府建设", difficulty: "hard", attempts: 1 },
  { id: 3, title: "乡村振兴战略", difficulty: "easy", attempts: 5 },
];

export default function GongkaoPage() {
  const { documents, weakPoints, reviewTasks } = useMvpData("gongkao");
  const [selectedSubject, setSelectedSubject] = useState("xingce");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");

  const totalProgress = Math.round(subjectOptions.reduce((acc, s) => acc + s.progress, 0) / subjectOptions.length);

  return (
    <WorkspaceFrame badge="考公备考" title="考公备考场景" subtitle="行测刷题、申论批改、面试模拟，助你成功上岸。">
      <div className="grid grid-cols-12 gap-6">
        <section className="col-span-12 lg:col-span-4 space-y-5">
          <div className="glass-card rounded-3xl p-5 border border-outline-variant/10 shadow-xl">
            <div className="flex items-center gap-2 mb-4">
              <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>account_balance</span>
              <h3 className="font-headline font-bold text-on-surface">备考进度</h3>
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
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-headline font-bold text-on-surface text-sm">薄弱知识点</h3>
              <span className="text-[10px] text-error font-bold">{weakPoints.length} 项</span>
            </div>
            <div className="space-y-2">
              {(weakPoints.length > 0 ? weakPoints : [
                { id: 1, concept: "数量关系", correct_rate: 42 },
                { id: 2, concept: "申论对策题", correct_rate: 55 },
              ]).slice(0, 4).map((item) => (
                <div key={item.id} className="flex items-center justify-between p-2 rounded-lg bg-surface-container-high/40">
                  <span className="text-xs text-on-surface">{item.concept}</span>
                  <span className="text-[10px] text-error">{item.correct_rate}%</span>
                </div>
              ))}
            </div>
          </div>

          <div className="glass-card rounded-3xl p-5 border border-outline-variant/10 shadow-xl">
            <div className="flex items-center gap-2 mb-3">
              <span className="material-symbols-outlined text-secondary">newspaper</span>
              <h3 className="font-headline font-bold text-on-surface text-sm">时政热点</h3>
            </div>
            <div className="space-y-2">
              {[
                { title: "2024年中央一号文件", date: "2024-01" },
                { title: "二十大报告核心考点", date: "2023-10" },
              ].map((item, i) => (
                <div key={i} className="p-3 rounded-xl bg-surface-container-high/40 hover:bg-surface-container-high/60 transition-colors cursor-pointer">
                  <p className="text-xs font-bold text-on-surface">{item.title}</p>
                  <p className="text-[9px] text-outline">{item.date}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="col-span-12 lg:col-span-8 space-y-5">
          <div className="glass-card rounded-3xl p-6 border border-outline-variant/10 shadow-xl">
            <div className="flex items-center gap-2 mb-4">
              <span className="material-symbols-outlined text-tertiary" style={{ fontVariationSettings: "'FILL' 1" }}>quiz</span>
              <h3 className="font-headline font-bold text-on-surface">行测刷题</h3>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
              {[
                { name: "言语理解", count: 120 },
                { name: "数量关系", count: 80 },
                { name: "判断推理", count: 150 },
                { name: "资料分析", count: 60 },
                { name: "常识判断", count: 200 },
              ].map((type) => (
                <button key={type.name} className="p-4 rounded-xl bg-surface-container-high/40 hover:bg-surface-container-high/60 transition-colors text-center cursor-pointer">
                  <p className="text-xs font-bold text-on-surface mb-1">{type.name}</p>
                  <p className="text-[10px] text-outline">{type.count} 题</p>
                </button>
              ))}
            </div>
            <div className="bg-surface-container-high/40 rounded-xl p-4">
              <p className="text-[10px] font-label font-bold uppercase tracking-widest text-outline mb-2">今日推荐</p>
              <p className="text-sm text-on-surface mb-3">数量关系 - 工程问题专项训练</p>
              <div className="flex gap-2">
                <button className="flex-1 bg-primary text-on-primary font-bold py-2 rounded-xl text-sm hover:scale-[1.01] active:scale-95 transition-all">
                  开始练习
                </button>
                <button className="px-4 bg-surface-container-high text-secondary font-bold py-2 rounded-xl text-sm hover:text-primary transition-colors border border-outline-variant/10">
                  错题回顾
                </button>
              </div>
            </div>
          </div>

          <div className="glass-card rounded-3xl p-6 border border-outline-variant/10 shadow-xl">
            <div className="flex items-center gap-2 mb-4">
              <span className="material-symbols-outlined text-secondary" style={{ fontVariationSettings: "'FILL' 1" }}>edit_document</span>
              <h3 className="font-headline font-bold text-on-surface">申论批改</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
              {shenlunTopics.map((topic) => (
                <div key={topic.id} className="p-4 rounded-xl bg-surface-container-high/40 hover:bg-surface-container-high/60 transition-colors cursor-pointer">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-xs font-bold text-on-surface">{topic.title}</p>
                    <span className={`text-[9px] px-2 py-0.5 rounded-full ${
                      topic.difficulty === "easy" ? "bg-tertiary/10 text-tertiary" :
                      topic.difficulty === "medium" ? "bg-secondary/10 text-secondary" :
                      "bg-error/10 text-error"
                    }`}>
                      {topic.difficulty === "easy" ? "简单" : topic.difficulty === "medium" ? "中等" : "困难"}
                    </span>
                  </div>
                  <p className="text-[10px] text-outline">已练习 {topic.attempts} 次</p>
                </div>
              ))}
            </div>
            <div className="bg-surface-container-lowest rounded-xl p-4">
              <textarea
                className="w-full bg-transparent border-none outline-none text-sm text-on-surface placeholder:text-outline resize-none"
                rows={4}
                placeholder="粘贴你的申论文章，AI 将给出评分和修改建议..."
              />
              <div className="flex justify-end mt-2">
                <button className="bg-primary text-on-primary font-bold px-4 py-2 rounded-xl text-sm hover:scale-[1.01] active:scale-95 transition-all">
                  提交批改
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
                { id: 1, concept: "数量关系错题复习", due_at: "2024-01-15" },
                { id: 2, concept: "申论范文背诵", due_at: "2024-01-16" },
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
