"use client";

import { useMemo, useState, useRef } from "react";
import { useRouter } from "next/navigation";

import { uploadFile, createDocumentFromFile } from "@/lib/api";
import { useMvpData } from "@/hooks/use-mvp-data";
import type { SceneId } from "@/lib/types";

const sceneOptions: { value: SceneId; label: string; icon: string }[] = [
  { value: "general", label: "通用", icon: "school" },
  { value: "career", label: "求职", icon: "work" },
  { value: "kaoyan", label: "考研", icon: "auto_stories" },
  { value: "gongkao", label: "考公", icon: "account_balance" },
];

const docTypeOptions = [
  { value: "note", label: "学习笔记", icon: "edit_note" },
  { value: "material", label: "参考资料", icon: "menu_book" },
  { value: "resume", label: "简历", icon: "description" },
  { value: "jd", label: "岗位描述", icon: "work_outline" },
  { value: "exam", label: "真题试卷", icon: "quiz" },
];

export default function KnowledgeBasePage() {
  const router = useRouter();
  const [selectedScene, setSelectedScene] = useState<SceneId>("general");
  const { documents, reload, loading } = useMvpData(selectedScene);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadForm, setUploadForm] = useState({ doc_type: "note", source_url: "" });
  const [searchQuery, setSearchQuery] = useState("");
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const filteredDocuments = useMemo(() => {
    if (!searchQuery) return documents;
    const query = searchQuery.toLowerCase();
    return documents.filter(
      (doc) => doc.filename.toLowerCase().includes(query) || doc.summary?.toLowerCase().includes(query)
    );
  }, [documents, searchQuery]);

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
    <div className="min-h-screen bg-surface">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-surface/80 backdrop-blur-xl border-b border-outline-variant/10">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => router.push("/")}
              className="w-10 h-10 rounded-xl bg-surface-container-high/60 flex items-center justify-center hover:bg-primary/10 transition-colors"
            >
              <span className="material-symbols-outlined text-secondary">arrow_back</span>
            </button>
            <div>
              <h1 className="text-lg font-headline font-bold text-on-surface">知识库</h1>
              <p className="text-[10px] text-outline">上传和管理学习资料</p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => router.push("/profile")}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold bg-surface-container-high/60 text-secondary hover:text-primary hover:bg-primary/10 transition-colors border border-outline-variant/10"
          >
            <span className="material-symbols-outlined text-base">person</span>
            我的
          </button>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-6">
        {/* Scene Tabs */}
        <div className="flex items-center gap-2 mb-6 overflow-x-auto pb-2">
          {sceneOptions.map((scene) => {
            const isActive = selectedScene === scene.value;
            return (
              <button
                key={scene.value}
                type="button"
                onClick={() => setSelectedScene(scene.value)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-bold whitespace-nowrap transition-all ${
                  isActive
                    ? "bg-primary text-on-primary shadow-lg shadow-primary/20"
                    : "bg-surface-container-high/60 text-secondary hover:text-primary hover:bg-primary/10 border border-outline-variant/10"
                }`}
              >
                <span className="material-symbols-outlined text-base" style={isActive ? { fontVariationSettings: "'FILL' 1" } : {}}>
                  {scene.icon}
                </span>
                {scene.label}
              </button>
            );
          })}
        </div>

        <div className="grid grid-cols-12 gap-6">
          {/* Upload Section */}
          <section className="col-span-12 lg:col-span-4">
            <div className="glass-card rounded-3xl border border-outline-variant/10 p-5">
              <div className="flex items-center gap-2 mb-4">
                <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>upload_file</span>
                <h3 className="font-headline font-bold text-on-surface">上传资料</h3>
              </div>
              <form className="space-y-3" onSubmit={handleUpload}>
                <div
                  className="border-2 border-dashed border-outline-variant/20 rounded-2xl p-6 hover:bg-primary/5 transition-colors text-center cursor-pointer"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <div className="w-12 h-12 rounded-full bg-surface-container-high flex items-center justify-center mx-auto mb-2">
                    <span className="material-symbols-outlined text-primary text-xl">cloud_upload</span>
                  </div>
                  {selectedFile ? (
                    <p className="text-xs text-primary font-bold">{selectedFile.name}</p>
                  ) : (
                    <p className="text-xs text-outline">点击选择文件</p>
                  )}
                  <p className="text-[10px] text-outline mt-1">PDF、TXT、Markdown</p>
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
                  className="w-full bg-primary text-on-primary font-bold py-2.5 rounded-xl text-sm hover:scale-[1.01] active:scale-95 transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  <span className="material-symbols-outlined text-base">upload</span>
                  {uploading ? "上传中..." : "上传"}
                </button>
              </form>
            </div>
          </section>

          {/* Document List */}
          <section className="col-span-12 lg:col-span-8">
            <div className="glass-card rounded-3xl border border-outline-variant/10 p-5">
              <div className="flex items-center gap-3 mb-4">
                <div className="flex-1 flex items-center bg-surface-container-lowest rounded-xl px-4 py-2 border border-outline-variant/30">
                  <span className="material-symbols-outlined text-sm text-secondary mr-2">search</span>
                  <input
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="flex-1 bg-transparent border-none outline-none text-sm text-on-surface placeholder:text-outline"
                    placeholder="搜索文件..."
                  />
                </div>
                <span className="text-xs text-outline">{filteredDocuments.length} 份资料</span>
              </div>

              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <span className="material-symbols-outlined text-primary text-3xl animate-pulse">hourglass_empty</span>
                </div>
              ) : filteredDocuments.length === 0 ? (
                <div className="text-center py-12">
                  <span className="material-symbols-outlined text-outline text-4xl mb-3 block">folder_off</span>
                  <p className="text-sm text-outline">暂无资料</p>
                  <p className="text-xs text-outline mt-1">上传你的第一份资料开始学习</p>
                </div>
              ) : (
                <div className="space-y-2 max-h-[500px] overflow-y-auto">
                  {filteredDocuments.map((doc) => (
                    <div
                      key={doc.id}
                      className="flex items-center gap-3 p-3 rounded-xl bg-surface-container-high/40 hover:bg-surface-container-high/60 transition-colors"
                    >
                      <div className="w-10 h-10 rounded-lg bg-surface-container-highest flex items-center justify-center flex-shrink-0">
                        <span className="material-symbols-outlined text-secondary text-lg">
                          {docTypeOptions.find((t) => t.value === doc.doc_type)?.icon || "description"}
                        </span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-bold text-on-surface truncate">{doc.filename}</p>
                          <span
                            className={`text-[9px] px-2 py-0.5 rounded-full flex-shrink-0 ${
                              doc.status === "ready"
                                ? "bg-tertiary/10 text-tertiary"
                                : doc.status === "processing"
                                  ? "bg-secondary/10 text-secondary"
                                  : "bg-error/10 text-error"
                            }`}
                          >
                            {doc.status === "ready" ? "就绪" : doc.status === "processing" ? "处理中" : "待处理"}
                          </span>
                        </div>
                        <p className="text-[11px] text-outline truncate mt-0.5">{doc.summary || "暂无摘要"}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
