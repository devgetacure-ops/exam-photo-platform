"use client";

import React, { useState } from "react";
import { PrivacyNotice } from "../components/privacy-notice";
import { RuleSelector } from "../components/rule-selector";
import { UploadCard } from "../components/upload-card";
import { ProcessingStatus } from "../components/processing-status";
import { ValidationReport } from "../components/validation-report";
import { ResultPreview } from "../components/result-preview";
import { processImage, getReport } from "../lib/api-client";
import { ProcessImageResponse, PipelineReport } from "../lib/types";

export default function Home() {
  const [selectedRule, setSelectedRule] = useState<object | null>(null);
  const [selectedRuleName, setSelectedRuleName] = useState<string>("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [allowInvalidOutput, setAllowInvalidOutput] = useState(false);

  const [processingStatus, setProcessingStatus] = useState<
    "idle" | "sending" | "processing" | "succeeded" | "failed" | "error"
  >("idle");
  const [processingMessage, setProcessingMessage] = useState<string>("");

  const [jobResponse, setJobResponse] = useState<ProcessImageResponse | null>(null);
  const [pipelineReport, setPipelineReport] = useState<PipelineReport | null>(null);

  const handleRuleSelected = (rule: object | null, name: string) => {
    setSelectedRule(rule);
    setSelectedRuleName(name);
    // Reset output when rules change
    handleResetOutput();
  };

  const handleFileSelected = (file: File | null) => {
    setSelectedFile(file);
    // Reset output when file changes
    handleResetOutput();
  };

  const handleResetOutput = () => {
    setProcessingStatus("idle");
    setProcessingMessage("");
    setJobResponse(null);
    setPipelineReport(null);
  };

  const handleProcess = async () => {
    if (!selectedFile || !selectedRule) return;

    setProcessingStatus("sending");
    setProcessingMessage("Uploading files and rule configuration...");
    setJobResponse(null);
    setPipelineReport(null);

    try {
      // 1. Process via local API
      const response = await processImage({
        image: selectedFile,
        ruleJson: selectedRule,
        allowInvalidOutput,
      });

      setProcessingStatus("processing");
      setProcessingMessage("Parsing results and running diagnostics...");

      // 2. Fetch compliance report
      const report = await getReport(response.job_id);

      setJobResponse(response);
      setPipelineReport(report);
      setProcessingStatus(report.is_valid ? "succeeded" : "failed");
      setProcessingMessage("");
    } catch (err) {
      const error = err as Error;
      setProcessingStatus("error");
      setProcessingMessage(error.message || "An unexpected error occurred.");
    }
  };

  const handleDeleteCleanup = () => {
    // Clear local memory states on deletion
    setJobResponse(null);
    setPipelineReport(null);
    setProcessingStatus("idle");
    setProcessingMessage("");
  };

  const isFormValid = selectedRule !== null && selectedFile !== null;

  return (
    <div className="flex-1 bg-slate-50 dark:bg-zinc-950 font-sans text-slate-800 dark:text-zinc-200">
      <header className="bg-white dark:bg-zinc-900 border-b border-slate-200 dark:border-zinc-800 py-6 px-4 sm:px-8">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="space-y-0.5">
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">
                Exam Photo Compliance
              </h1>
              <span className="bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-400 border border-indigo-100 dark:border-indigo-900/30 text-[10px] font-semibold px-2 py-0.5 rounded-full">
                Local MVP
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-zinc-400">
              Prepare rule-based exam photos with privacy-first processing.
            </p>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto py-8 px-4 sm:px-8 space-y-8">
        <PrivacyNotice />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
          {/* Left Column: Input Steps */}
          <div className="space-y-6">
            <RuleSelector
              onRuleSelected={handleRuleSelected}
              selectedName={selectedRuleName}
            />

            <UploadCard
              onFileSelected={handleFileSelected}
              selectedFile={selectedFile}
            />

            {isFormValid && (
              <div className="bg-white dark:bg-zinc-950 border border-slate-200 dark:border-zinc-800 rounded-lg p-5 shadow-sm space-y-4">
                <div>
                  <h2 className="text-base font-semibold text-slate-900 dark:text-white">
                    Step 3: Run Processing
                  </h2>
                  <p className="text-xs text-slate-500 dark:text-zinc-400 mt-0.5">
                    Click below to evaluate the photo against selected rules.
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <input
                    id="allow-invalid-checkbox"
                    type="checkbox"
                    checked={allowInvalidOutput}
                    onChange={(e) => setAllowInvalidOutput(e.target.checked)}
                    className="w-4 h-4 rounded text-indigo-650 focus:ring-indigo-500/20 border-slate-300 bg-slate-50 dark:bg-zinc-900 dark:border-zinc-750"
                  />
                  <label
                    htmlFor="allow-invalid-checkbox"
                    className="text-xs font-medium text-slate-700 dark:text-zinc-300 cursor-pointer"
                  >
                    Allow saving output when check fails (Allow Invalid Output)
                  </label>
                </div>

                <button
                  type="button"
                  onClick={handleProcess}
                  disabled={processingStatus === "sending" || processingStatus === "processing"}
                  className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs py-2.5 px-4 rounded shadow-sm transition-colors focus:ring-2 focus:ring-indigo-500/20 outline-none flex items-center justify-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
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
                      d="M14.7 15.3a6 6 0 01-9.4-7.5l-3-3m0 0l-3 3m3-3h12a6 6 0 016 6v3m0 0v6"
                    />
                  </svg>
                  Process Photo
                </button>
              </div>
            )}
          </div>

          {/* Right Column: Status & Reports */}
          <div className="space-y-6">
            <ProcessingStatus status={processingStatus} message={processingMessage} />

            {pipelineReport && jobResponse && (
              <ValidationReport report={pipelineReport} />
            )}

            {jobResponse && (
              <ResultPreview
                jobId={jobResponse.job_id}
                outputFilename={jobResponse.output_filename || null}
                outputUrl={jobResponse.output_url || null}
                onDelete={handleDeleteCleanup}
              />
            )}
          </div>
        </div>
      </main>

      <footer className="bg-white dark:bg-zinc-900 border-t border-slate-200 dark:border-zinc-800 py-6 px-4 mt-12 text-center text-xs text-slate-400 dark:text-zinc-500">
        <p>© 2026 Indian Exam-Photo Compliance Platform. Built for Local MVP & Privacy-First Testing.</p>
      </footer>
    </div>
  );
}
