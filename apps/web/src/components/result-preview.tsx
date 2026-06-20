import React, { useState, useEffect } from "react";
import { getOutputBlob, deleteJob } from "../lib/api-client";

interface ResultPreviewProps {
  jobId: string;
  outputFilename: string | null;
  onDelete: () => void;
  outputUrl: string | null;
}

export function ResultPreview({
  jobId,
  outputFilename,
  onDelete,
  outputUrl,
}: ResultPreviewProps) {
  const [downloadBlobUrl, setDownloadBlobUrl] = useState<string | null>(null);
  const [previewBlobUrl, setPreviewBlobUrl] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isDeleted, setIsDeleted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch the output image to display in preview and revoke on cleanup
  useEffect(() => {
    let active = true;
    let localPreviewUrl: string | null = null;

    async function loadOutputPreview() {
      // We only load preview if an outputUrl is available
      if (!outputUrl) return;

      try {
        const blob = await getOutputBlob(jobId);
        if (!active) return;
        localPreviewUrl = URL.createObjectURL(blob);
        setPreviewBlobUrl(localPreviewUrl);
      } catch (err) {
        if (active) {
          const error = err as Error;
          setError(error.message || "Failed to load output image preview");
        }
      }
    }

    loadOutputPreview();

    return () => {
      active = false;
      if (localPreviewUrl) {
        URL.revokeObjectURL(localPreviewUrl);
      }
    };
  }, [jobId, outputUrl]);

  // Clean up any temporary download URLs on unmount
  useEffect(() => {
    return () => {
      if (downloadBlobUrl) {
        URL.revokeObjectURL(downloadBlobUrl);
      }
    };
  }, [downloadBlobUrl]);

  const handleDownload = async () => {
    try {
      setError(null);
      const blob = await getOutputBlob(jobId);
      const url = URL.createObjectURL(blob);
      setDownloadBlobUrl(url);

      const a = document.createElement("a");
      a.href = url;
      a.download = outputFilename || "exam_photo.jpg";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);

      // Clean up download URL immediately
      URL.revokeObjectURL(url);
      setDownloadBlobUrl(null);
    } catch (err) {
      const error = err as Error;
      setError(error.message || "Failed to download processed photo.");
    }
  };

  const handleDelete = async () => {
    setIsDeleting(true);
    setError(null);
    try {
      await deleteJob(jobId);

      // Explicitly revoke preview URL
      if (previewBlobUrl) {
        URL.revokeObjectURL(previewBlobUrl);
        setPreviewBlobUrl(null);
      }
      if (downloadBlobUrl) {
        URL.revokeObjectURL(downloadBlobUrl);
        setDownloadBlobUrl(null);
      }

      setIsDeleted(true);
      onDelete();
    } catch (err) {
      const error = err as Error;
      setError(error.message || "Failed to delete job assets.");
    } finally {
      setIsDeleting(false);
    }
  };

  if (isDeleted) {
    return (
      <div className="bg-slate-50 dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 rounded-lg p-5 shadow-sm text-center space-y-2">
        <div className="text-emerald-500 flex justify-center" aria-hidden="true">
          <svg
            className="w-10 h-10"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>
        <p className="text-sm font-semibold text-slate-800 dark:text-white">
          Job Assets Deleted Successfully
        </p>
        <p className="text-xs text-slate-500 dark:text-zinc-400">
          All temporary candidate files have been securely wiped from both backend storage and local memory.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-zinc-950 border border-slate-200 dark:border-zinc-800 rounded-lg p-5 shadow-sm space-y-4">
      <div>
        <h2 className="text-base font-semibold text-slate-900 dark:text-white">
          Step 4: Output Preview & Actions
        </h2>
        <p className="text-xs text-slate-500 dark:text-zinc-400 mt-0.5">
          Review formatted candidate photograph and download if valid.
        </p>
      </div>

      <div className="flex flex-col items-center justify-center border border-slate-150 dark:border-zinc-850 rounded-lg p-4 bg-slate-50 dark:bg-zinc-900">
        {previewBlobUrl ? (
          <div className="space-y-2 text-center">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={previewBlobUrl}
              alt="Compliance formatted output"
              className="max-h-64 object-contain rounded border border-slate-200 dark:border-zinc-800 shadow-sm bg-white"
            />
            {outputFilename && (
              <p className="text-[10px] font-mono text-slate-550 dark:text-zinc-405 truncate max-w-xs mx-auto">
                {outputFilename}
              </p>
            )}
          </div>
        ) : (
          <div className="py-8 text-slate-400 dark:text-zinc-500 text-xs text-center space-y-1">
            {error ? (
              <p className="text-rose-600 dark:text-rose-455">{error}</p>
            ) : !outputUrl ? (
              <p>Output image not available (invalid output rejected by rule configuration).</p>
            ) : (
              <p>Loading processed candidate preview...</p>
            )}
          </div>
        )}
      </div>

      {error && !previewBlobUrl && (
        <div className="text-xs text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/20 border border-rose-100 dark:border-rose-900/30 rounded p-2.5">
          {error}
        </div>
      )}

      <div className="flex flex-col sm:flex-row gap-3 pt-2">
        {outputUrl && (
          <button
            type="button"
            onClick={handleDownload}
            disabled={isDeleting}
            className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs py-2.5 px-4 rounded shadow-sm transition-colors focus:ring-2 focus:ring-indigo-500/20 outline-none flex items-center justify-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
              />
            </svg>
            Download Processed Photo
          </button>
        )}
        <button
          type="button"
          onClick={handleDelete}
          disabled={isDeleting}
          className="flex-1 bg-white hover:bg-slate-50 dark:bg-zinc-900 dark:hover:bg-zinc-800 border border-slate-200 dark:border-zinc-700 text-slate-700 dark:text-zinc-300 font-semibold text-xs py-2.5 px-4 rounded shadow-sm transition-colors focus:ring-2 focus:ring-slate-500/20 outline-none flex items-center justify-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isDeleting ? (
            <span>Deleting Assets...</span>
          ) : (
            <>
              <svg
                className="w-4 h-4 text-rose-550 dark:text-rose-455"
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
              Delete Job & Files
            </>
          )}
        </button>
      </div>
    </div>
  );
}
