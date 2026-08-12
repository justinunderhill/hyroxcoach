"use client";

import { ChangeEvent, useState } from "react";

import {
  ExtractionResult,
  ExtractionType,
  MediaPurpose,
  requestExtraction,
  uploadMediaAsset,
} from "@/lib/media";

type ImportState =
  | { status: "idle" }
  | { status: "uploading" }
  | { status: "extracting" }
  | { status: "ready"; result: ExtractionResult }
  | { status: "applied"; result: ExtractionResult }
  | { status: "failed"; message: string };

type ScreenshotImportProps = {
  purpose: MediaPurpose;
  extractionType: ExtractionType;
  label: string;
  summarize: (data: Record<string, unknown>) => string;
  onMediaUploaded: (mediaAssetId: string) => void;
  onApply: (data: Record<string, unknown>, extractionResultId: string) => void;
};

export function ScreenshotImport({
  purpose,
  extractionType,
  label,
  summarize,
  onMediaUploaded,
  onApply,
}: ScreenshotImportProps) {
  const [state, setState] = useState<ImportState>({ status: "idle" });

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;

    setState({ status: "uploading" });
    try {
      const mediaAssetId = await uploadMediaAsset(file, purpose);
      onMediaUploaded(mediaAssetId);

      setState({ status: "extracting" });
      const result = await requestExtraction(mediaAssetId, extractionType);
      if (result.status !== "succeeded") {
        setState({
          status: "failed",
          message: "The photo could not be read automatically.",
        });
        return;
      }
      setState({ status: "ready", result });
    } catch (error) {
      setState({
        status: "failed",
        message: error instanceof Error ? error.message : "The photo could not be processed.",
      });
    }
  }

  function handleApply() {
    if (state.status !== "ready") return;
    onApply(state.result.extracted_data, state.result.id);
    setState({ status: "applied", result: state.result });
  }

  const readyOrApplied = state.status === "ready" || state.status === "applied";
  const confidence = readyOrApplied ? state.result.confidence : null;
  const uncertaintyNotes = readyOrApplied
    ? ((state.result.extracted_data.uncertainty_notes as string[] | undefined) ?? [])
    : [];

  return (
    <div className="rounded-2xl border border-dashed border-stone-300 bg-[#fbfbf7] p-4">
      <label className="block text-sm font-semibold text-stone-700">
        {label}
        <input
          accept="image/jpeg,image/png,image/webp,image/heic"
          capture="environment"
          className="mt-2 block w-full text-sm text-stone-600 file:mr-3 file:min-h-11 file:rounded-xl file:border-0 file:bg-[#f8ffe4] file:px-4 file:text-sm file:font-semibold file:text-[#567118]"
          onChange={handleFileChange}
          type="file"
        />
      </label>

      {state.status === "uploading" ? <p className="mt-2 text-xs text-stone-500">Uploading…</p> : null}
      {state.status === "extracting" ? (
        <p className="mt-2 text-xs text-stone-500">Reading the photo…</p>
      ) : null}
      {state.status === "failed" ? (
        <p className="mt-2 text-xs text-rose-700">{state.message} The photo is still attached — fill in the details manually.</p>
      ) : null}

      {readyOrApplied ? (
        <div className="mt-3 rounded-xl bg-white p-3">
          <p className="text-sm text-stone-700">{summarize(state.result.extracted_data)}</p>
          {confidence !== null ? (
            <p className="mt-1 text-xs text-stone-400">Confidence: {Math.round(confidence * 100)}%</p>
          ) : null}
          {uncertaintyNotes.length > 0 ? (
            <ul className="mt-1 list-disc pl-4 text-xs text-stone-400">
              {uncertaintyNotes.map((note) => (
                <li key={note}>{note}</li>
              ))}
            </ul>
          ) : null}
          {state.status === "ready" ? (
            <button
              className="mt-2 min-h-9 rounded-xl bg-[#15271e] px-3 text-xs font-bold text-white"
              onClick={handleApply}
              type="button"
            >
              Use these values
            </button>
          ) : (
            <p className="mt-2 text-xs font-semibold text-[#567118]">
              Applied — review the fields below before saving.
            </p>
          )}
        </div>
      ) : null}
    </div>
  );
}
