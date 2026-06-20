import React, { useState, useEffect, useRef } from "react";
import { validateImageFile } from "../lib/file-validation";

interface UploadCardProps {
  onFileSelected: (file: File | null) => void;
  selectedFile: File | null;
}

export function UploadCard({ onFileSelected, selectedFile }: UploadCardProps) {
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (selectedFile) {
      const url = URL.createObjectURL(selectedFile);
      const timer = setTimeout(() => {
        setPreviewUrl(url);
        setError(null);
      }, 0);
      return () => {
        clearTimeout(timer);
        URL.revokeObjectURL(url);
      };
    } else {
      const timer = setTimeout(() => {
        setPreviewUrl(null);
      }, 0);
      return () => clearTimeout(timer);
    }
  }, [selectedFile]);

  const processFile = (file: File) => {
    const res = validateImageFile(file);
    if (res.valid) {
      setError(null);
      onFileSelected(file);
    } else {
      setError(res.error || "Invalid file");
      onFileSelected(null);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      processFile(file);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      processFile(file);
    }
  };

  const handleClear = () => {
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
    setError(null);
    onFileSelected(null);
  };

  // Helper to format bytes
  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  return (
    <div className="bg-white dark:bg-zinc-950 border border-slate-200 dark:border-zinc-800 rounded-lg p-5 shadow-sm space-y-4">
      <div>
        <h2 className="text-base font-semibold text-slate-900 dark:text-white">
          Step 2: Upload Candidate Photograph
        </h2>
        <p className="text-xs text-slate-500 dark:text-zinc-400 mt-0.5">
          Select a frontal portrait image. Supported: JPEG, PNG, WebP. Max: 5 MB.
        </p>
      </div>

      {!selectedFile ? (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`flex flex-col items-center justify-center border-2 border-dashed rounded-lg p-8 bg-slate-50 dark:bg-zinc-900 transition-all ${
            dragOver
              ? "border-indigo-500 bg-indigo-50/20 dark:border-indigo-400 dark:bg-indigo-950/10"
              : "border-slate-200 dark:border-zinc-800"
          }`}
        >
          <svg
            className="w-10 h-10 text-slate-400 dark:text-zinc-500 mb-3"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
          <label
            htmlFor="image-file-input"
            className="cursor-pointer bg-white dark:bg-zinc-800 border border-slate-200 dark:border-zinc-700 hover:bg-slate-50 dark:hover:bg-zinc-750 text-slate-800 dark:text-white font-semibold text-xs py-2 px-4 rounded shadow-sm transition-colors"
          >
            Choose Image
          </label>
          <input
            id="image-file-input"
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={handleInputChange}
            className="hidden"
          />
          <p className="text-[10px] text-slate-400 dark:text-zinc-500 mt-2">
            or drag and drop file here
          </p>
        </div>
      ) : (
        <div className="border border-slate-200 dark:border-zinc-800 rounded-lg p-3 bg-slate-50 dark:bg-zinc-900 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            {previewUrl && (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={previewUrl}
                alt="Original preview"
                className="w-16 h-16 object-cover rounded border border-slate-200 dark:border-zinc-800 bg-white"
              />
            )}
            <div className="min-w-0">
              <p className="text-xs font-semibold text-slate-850 dark:text-white truncate">
                {selectedFile.name}
              </p>
              <p className="text-[10px] text-slate-500 dark:text-zinc-400 space-x-2 mt-0.5">
                <span>{formatBytes(selectedFile.size)}</span>
                <span>•</span>
                <span className="uppercase">{selectedFile.type.split("/")[1]}</span>
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleClear}
            className="p-1 text-slate-400 hover:text-slate-600 dark:text-zinc-500 dark:hover:text-zinc-350 transition-colors"
            title="Remove photo"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
          </button>
        </div>
      )}

      {error && (
        <div className="text-xs text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/20 border border-rose-100 dark:border-rose-900/30 rounded p-2.5">
          {error}
        </div>
      )}
    </div>
  );
}
