"use client";

import { completeReviewTask } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import { useMvpData } from "@/hooks/use-mvp-data";
import { WorkspaceFrame } from "@/components/workspace-frame";

export default function ProgressPage() {
  const { dashboard, weakPoints, reviewTasks, reload } = useMvpData("general");
  const retentionBars = [40, 55, 48, 70, 66, 85, 80, 92];

  async function handleComplete(taskId: number) {
    await completeReviewTask(taskId, "mastered");
    await reload();
  }

  return (
    <WorkspaceFrame
      badge="复习进度"
      title="复习进度"
      subtitle="把记忆保持率、复习日历、薄弱知识点和今日任务放进同一个节奏面板。"
    >
      <div className="grid grid-cols-12 gap-6">

        {/* Retention chart — col 8 */}
        <section className="col-span-12 lg:col-span-8">
          <div className="glass-card rounded-3xl p-6 border border-outline-variant/10 shadow-xl relative overflow-hidden">
            <div className="absolute top-0 right-0 p-6 opacity-5 pointer-events-none">
              <span className="material-symbols-outlined text-[120px] text-primary">auto_graph</span>
            </div>
            <div className="flex justify-between items-end mb-6 relative z-10">
              <div>
                <h2 className="text-xl font-headline font-bold text-on-surface">记忆保持率</h2>
                <p className="text-on-surface-variant text-sm">近 30 天的长期记忆稳定趋势</p>
              </div>
              <div className="text-right">
                <span className="text-4xl font-headline font-bold text-tertiary">92%</span>
                <p className="text-[10px] text-tertiary uppercase tracking-widest font-label font-bold">本周 +4.2%</p>
              </div>
            </div>
            <div className="h-44 w-full flex items-end gap-1.5 relative overflow-hidden group">
              <div className="absolute inset-0 bg-gradient-to-t from-primary/5 to-transparent pointer-events-none" />
              {retentionBars.map((value, i) => (
                <div key={i} className="flex-1 flex flex-col items-center gap-1">
                  <div
                    className={`w-full rounded-t-lg transition-all ${
                      i === retentionBars.length - 1
                        ? "bg-primary/40 ring-2 ring-primary/60 shadow-[0_0_12px_rgba(186,158,255,0.3)]"
                        : "bg-surface-container-highest group-hover:bg-primary/20"
                    }`}
                    style={{ height: `${value}%` }}
                  />
                  <span className="text-[9px] text-outline font-label">W{i + 1}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Spaced repetition alert — col 4 */}
        <section className="col-span-12 lg:col-span-4 space-y-4">
          <div className="glass-card rounded-3xl p-5 border border-error/20 shadow-xl">
            <div className="flex items-center gap-2 mb-3">
              <span className="material-symbols-outlined text-error text-base" style={{ fontVariationSettings: "'FILL' 1" }}>warning</span>
              <h3 className="font-headline font-bold text-on-surface text-sm">间隔复习提醒</h3>
            </div>
            <p className="text-xs text-on-surface-variant leading-relaxed">
              {reviewTasks.length || 4} 个知识点正在进入遗忘窗口，建议今天完成复习。
            </p>
          </div>

          <div className="glass-card rounded-3xl p-5 border border-outline-variant/10 shadow-xl space-y-3">
            <span className="text-[10px] font-label font-bold uppercase tracking-widest text-outline">主题保持率</span>
            {(dashboard?.quick_actions ?? ["上传资料", "开始提问", "复习任务"]).map((item, i) => (
              <div key={item} className="space-y-1">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-on-surface">{item}</span>
                  <span className="text-xs font-bold text-primary">{72 + i * 9}%</span>
                </div>
                <div className="h-1.5 w-full bg-surface-container-lowest rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-primary to-tertiary rounded-full"
                    style={{ width: `${72 + i * 9}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Review calendar — col 6 */}
        <section className="col-span-12 lg:col-span-6">
          <div className="glass-card rounded-3xl p-6 border border-outline-variant/10 shadow-xl">
            <div className="flex items-center gap-2 mb-5">
              <span className="material-symbols-outlined text-primary">event_note</span>
              <h3 className="font-headline font-bold text-on-surface">计划复习日历</h3>
            </div>
            <div className="grid grid-cols-7 gap-1.5 text-center text-[10px] font-label font-bold text-on-surface-variant mb-3">
              {["一", "二", "三", "四", "五", "六", "日"].map((d) => (
                <span key={d}>{d}</span>
              ))}
            </div>
            <div className="grid grid-cols-7 gap-1.5">
              {Array.from({ length: 14 }).map((_, i) => {
                const hasTask = i < reviewTasks.length;
                return (
                  <div
                    key={i}
                    className={`rounded-xl p-2 text-center cursor-pointer transition-all ${
                      hasTask
                        ? "bg-primary/20 border border-primary/30 hover:bg-primary/30"
                        : "bg-surface-container-high/40 border border-outline-variant/10 hover:bg-surface-container-high/60"
                    }`}
                  >
                    <p className={`text-xs font-bold ${hasTask ? "text-primary" : "text-on-surface"}`}>{i + 17}</p>
                    <p className={`text-[8px] font-label mt-0.5 ${hasTask ? "text-primary/70" : "text-outline"}`}>
                      {hasTask ? "复习" : "空闲"}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* Weakest concepts — col 6 */}
        <section className="col-span-12 lg:col-span-6">
          <div className="glass-card rounded-3xl p-6 border border-outline-variant/10 shadow-xl">
            <div className="flex items-center gap-2 mb-5">
              <span className="material-symbols-outlined text-error">psychology</span>
              <h3 className="font-headline font-bold text-on-surface">最薄弱知识点</h3>
            </div>
            <div className="space-y-3">
              {weakPoints.map((item, i) => (
                <div key={item.id} className="space-y-1.5">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="text-xs font-bold text-on-surface">{item.concept}</p>
                      <p className="text-[10px] text-outline">{item.source_type} · {item.correct_rate}% 正确率</p>
                    </div>
                    <span className="text-xs font-bold text-error">{item.correct_rate}%</span>
                  </div>
                  <div className="h-1.5 w-full bg-surface-container-lowest rounded-full overflow-hidden">
                    <div
                      className="h-full bg-error/60 rounded-full"
                      style={{ width: `${55 + i * 12}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Today's review tasks — col 12 */}
        <section className="col-span-12">
          <div className="glass-card rounded-3xl p-6 border border-outline-variant/10 shadow-xl">
            <div className="flex items-center justify-between mb-5">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-tertiary" style={{ fontVariationSettings: "'FILL' 1" }}>task_alt</span>
                <h3 className="font-headline font-bold text-on-surface">今日复习任务</h3>
              </div>
              <span className="text-[10px] font-label font-bold uppercase tracking-widest text-outline">执行队列</span>
            </div>
            <div className="space-y-2">
              {reviewTasks.map((task) => (
                <div key={task.id} className="flex items-center justify-between p-3 rounded-xl bg-surface-container-high/40 hover:bg-surface-container-high/60 transition-colors group">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-surface-container-highest flex items-center justify-center">
                      <span className="material-symbols-outlined text-xs text-primary">psychology</span>
                    </div>
                    <div>
                      <p className="text-xs font-bold text-on-surface">{task.concept}</p>
                      <p className="text-[10px] text-outline">{formatDateTime(task.due_at)}</p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleComplete(task.id)}
                    className="text-[10px] font-label font-bold uppercase tracking-widest px-3 py-1.5 rounded-full bg-tertiary/10 text-tertiary border border-tertiary/20 hover:bg-tertiary hover:text-on-tertiary transition-all"
                  >
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
