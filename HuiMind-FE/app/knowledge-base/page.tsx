"use client";

import { useMemo, useState, useRef } from "react";

import { uploadFile, createDocumentFromFile } from "@/lib/api";
import { useMvpData } from "@/hooks/use-mvp-data";
import { WorkspaceFrame } from "@/components/workspace-frame";
import type { SceneId } from "@/lib/types";

const sceneOptions: { value: SceneId; label: string; icon: string; description: string }[] = [
  { value: "general", label: "通用学习", icon: "school", description: "适用于各类学习场景" },
  { value: "career", label: "求职助手", icon: "work", description: "简历、面试、职业规划" },
  { value: "kaoyan", label: "考研备考", icon: "auto_stories", description: "专业课、公共课复习" },
  { value: "gongkao", label: "考公备考", icon: "account_balance", description: "行测、申论、面试" },
];

const docTypeOptions = [
  { value: "note", label: "学习笔记", icon: "edit_note" },
  { value: "material", label: "参考资料", icon: "menu_book" },
  { value: "resume", label: "简历", icon: "description" },
  { value: "jd", label: "岗位描述", icon: "work_outline" },
  { value: "exam", label: "真题试卷", icon: "quiz" },
];

export default function KnowledgeBasePage() {
  const [selectedScene, setSelectedScene] = useState<SceneId>("general");
  const { documents, reload, loading } = useMvpData(selectedScene);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadForm, setUploadForm] = useState({ doc_type: "note", source_url: "" });
  const [searchQuery, setSearchQuery] = useState("");
  const [uploading, setUploading] = useState(false);
  const [filterType, setFilterType] = useState<string>("all");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const filteredDocuments = useMemo(() => {
    let result = documents;
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (doc) => doc.filename.toLowerCase().includes(query) || doc.summary?.toLowerCase().includes(query)
      );
    }
    if (filterType !== "all") {
      result = result.filter((doc) => doc.doc_type === filterType);
    }
    return result;
  }, [documents, searchQuery, filterType]);

  async function handleUpload(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedFile) return;

    setUploading(true);
    try {
      const uploaded = await uploadFile({ scene_id: selectedScene, file: selectedFile });
      await createDocumentFromFile({
        scene_id: selectedScene,
        doc_type: uploadForm.doc_type,
        file_id: uploaded.file_id,
        oss_key: uploaded.oss_key,
      });
      setSelectedFile(null);
      setUploadForm({ doc_type: "note", source_url: "" });
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      await reload();
    } finally {
      setUploading(false);
    }
  }

  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  }

  return (
    <WorkspaceFrame badge="" title="" subtitle="" hidePageHeader={true}>
      <div className="grid grid-cols-12 gap-6">
        {/* 场景选择 */}
        <div className="col-span-12 mb-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-headline font-bold text-on-surface flex items-center gap-2">
              <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>folder_open</span>
              选择场景
            </h3>
            <span className="text-sm text-outline">当前：{sceneOptions.find(s => s.value === selectedScene)?.label}</span>
          </div>
          <div className="bg-surface-container-high/40 rounded-2xl p-3 border border-outline-variant/20">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {sceneOptions.map((scene) => {
                const active = selectedScene === scene.value;
                return (
                  <button
                    key={scene.value}
                    type="button"
                    onClick={() => setSelectedScene(scene.value)}
                    className={`flex flex-col items-center gap-2 p-3 rounded-xl transition-all ${active
                      ? "bg-primary/10 border border-primary/20"
                      : "hover:bg-surface-container-highest/60 border border-transparent hover:border-outline-variant/30"
                      }`}
                  >
                    <span
                      className={`material-symbols-outlined text-lg ${active ? "text-primary" : "text-outline"}`}
                      style={active ? { fontVariationSettings: "'FILL' 1" } : {}}
                    >
                      {scene.icon}
                    </span>
                    <p className={`text-sm font-bold ${active ? "text-primary" : "text-on-surface"}`}>{scene.label}</p>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        <section className="col-span-12 lg:col-span-4 space-y-4">
          <div className="glass-card rounded-3xl p-5 border border-outline-variant/10 shadow-xl">
            <div className="flex items-center gap-2 mb-4">
              <span className="material-symbols-outlined text-tertiary" style={{ fontVariationSettings: "'FILL' 1" }}>upload_file</span>
              <h3 className="font-headline font-bold text-on-surface">上传资料</h3>
            </div>
            <form className="space-y-3" onSubmit={handleUpload}>
              <div 
                className="border-2 border-dashed border-outline-variant/20 rounded-2xl p-4 hover:bg-primary/5 transition-colors text-center cursor-pointer"
                onClick={() => fileInputRef.current?.click()}
              >
                <div className="w-12 h-12 rounded-full bg-surface-container-high flex items-center justify-center mx-auto mb-2">
                  <span className="material-symbols-outlined text-primary text-xl">cloud_upload</span>
                </div>
                {selectedFile ? (
                  <p className="text-xs text-primary font-bold">{selectedFile.name}</p>
                ) : (
                  <p className="text-xs text-outline">点击选择文件（PDF、TXT、Markdown）</p>
                )}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.txt,.md,.markdown"
                  onChange={handleFileChange}
                  className="hidden"
                />
              </div>
              <select
                value={uploadForm.doc_type}
                onChange={(e) => setUploadForm({ ...uploadForm, doc_type: e.target.value })}
                className="w-full bg-surface-container-lowest rounded-xl px-4 py-2.5 text-sm text-on-surface outline-none border border-outline-variant/30 focus:border-primary transition-colors"
              >
                {docTypeOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
              <button
                type="submit"
                disabled={uploading || !selectedFile}
                className="w-full bg-gradient-to-r from-primary to-secondary text-on-primary font-bold py-2.5 rounded-xl text-sm hover:scale-[1.01] active:scale-95 transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>upload_file</span>
                {uploading ? "上传中..." : "上传资料"}
              </button>
            </form>
          </div>

          <div className="glass-card rounded-3xl p-5 border border-outline-variant/10 shadow-xl">
            <div className="flex items-center gap-2 mb-4">
              <span className="material-symbols-outlined text-secondary">info</span>
              <h3 className="font-headline font-bold text-on-surface">使用提示</h3>
            </div>
            <div className="space-y-3">
              <div className="bg-surface-container-high/40 rounded-xl p-3">
                <span className="material-symbols-outlined text-primary text-sm mb-1 block">upload_file</span>
                <p className="text-xs font-bold text-on-surface mb-1">上传资料</p>
                <p className="text-[10px] text-outline">支持 PDF、TXT、Markdown 格式，或直接粘贴 URL</p>
              </div>
              <div className="bg-surface-container-high/40 rounded-xl p-3">
                <span className="material-symbols-outlined text-secondary text-sm mb-1 block">category</span>
                <p className="text-xs font-bold text-on-surface mb-1">场景分类</p>
                <p className="text-[10px] text-outline">选择对应场景，让 AI 更精准地理解你的学习目标</p>
              </div>
              <div className="bg-surface-container-high/40 rounded-xl p-3">
                <span className="material-symbols-outlined text-tertiary text-sm mb-1 block">psychology</span>
                <p className="text-xs font-bold text-on-surface mb-1">智能问答</p>
                <p className="text-[10px] text-outline">上传后可在学习中枢向 AI 提问，获取精准回答</p>
              </div>
            </div>
          </div>
        </section>

        <section className="col-span-12 lg:col-span-8">
          <div className="glass-card rounded-3xl p-5 border border-outline-variant/10 shadow-xl">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex-1 flex items-center bg-surface-container-lowest rounded-xl px-4 py-2 border border-outline-variant/30">
                <span className="material-symbols-outlined text-sm text-secondary mr-2">search</span>
                <input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="flex-1 bg-transparent border-none outline-none text-sm text-on-surface placeholder:text-outline"
                  placeholder="搜索文件名或摘要..."
                />
              </div>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="bg-surface-container-lowest rounded-xl px-4 py-2 text-sm text-on-surface outline-none border border-outline-variant/30"
              >
                <option value="all">全部类型</option>
                {docTypeOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            {loading ? (
              <div className="flex items-center justify-center py-8">
                <span className="material-symbols-outlined text-primary text-3xl animate-pulse">hourglass_empty</span>
              </div>
            ) : filteredDocuments.length === 0 ? (
              <div className="text-center py-8">
                <span className="material-symbols-outlined text-outline text-4xl mb-3 block">folder_off</span>
                <p className="text-sm text-outline">暂无资料，点击左侧上传</p>
              </div>
            ) : (
              <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
                {filteredDocuments.map((doc) => (
                  <div
                    key={doc.id}
                    className="flex items-center gap-3 p-4 rounded-xl bg-surface-container-high/40 hover:bg-surface-container-high/60 transition-colors cursor-pointer group"
                  >
                    <div className="w-10 h-10 rounded-lg bg-surface-container-highest flex items-center justify-center flex-shrink-0">
                      <span className="material-symbols-outlined text-secondary">
                        {docTypeOptions.find((t) => t.value === doc.doc_type)?.icon || "description"}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="text-sm font-bold text-on-surface truncate">{doc.filename}</p>
                        <span
                          className={`text-[9px] px-2 py-0.5 rounded-full ${
                            doc.status === "ready"
                              ? "bg-tertiary/10 text-tertiary"
                              : doc.status === "processing"
                                ? "bg-secondary/10 text-secondary"
                                : "bg-error/10 text-error"
                          }`}
                        >
                          {doc.status === "ready" ? "已就绪" : doc.status === "processing" ? "处理中" : "待处理"}
                        </span>
                      </div>
                      <p className="text-[11px] text-outline truncate">{doc.summary || "暂无摘要"}</p>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <span className="text-[9px] bg-surface-container-highest px-2 py-0.5 rounded-full text-outline">
                        {docTypeOptions.find((t) => t.value === doc.doc_type)?.label || doc.doc_type}
                      </span>
                      <span className="material-symbols-outlined text-outline group-hover:text-primary transition-colors">
                        chevron_right
                      </span>
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
