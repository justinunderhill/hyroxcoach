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
    <div className="rounded-2xl border border-dashed border-line-strong bg-surface p-4">
      <label className="block text-sm font-semibold text-ink">
        {label}
        <input
          accept="image/jpeg,image/png,image/webp,image/heic"
          capture="environment"
          className="mt-2 block w-full text-sm text-muted file:mr-3 file:min-h-11 file:rounded-xl file:border-0 file:bg-lime/10 file:px-4 file:text-sm file:font-semibold file:text-lime"
          onChange={handleFileChange}
          type="file"
        />
      </label>

      {state.status === "uploading" ? <p className="mt-2 text-xs text-muted">Uploading…</p> : null}
      {state.status === "extracting" ? (
        <p className="mt-2 text-xs text-muted">Reading the photo…</p>
      ) : null}
      {state.status === "failed" ? (
        <p className="mt-2 text-xs text-red">{state.message} The photo is still attached — fill in the details manually.</p>
      ) : null}

      {readyOrApplied ? (
        <div className="mt-3 rounded-xl bg-surface p-3">
          <p className="text-sm text-ink">{summarize(state.result.extracted_data)}</p>
          {confidence !== null ? (
            <p className="mt-1 text-xs text-faint">Confidence: {Math.round(confidence * 100)}%</p>
          ) : null}
          {uncertaintyNotes.length > 0 ? (
            <ul className="mt-1 list-disc pl-4 text-xs text-faint">
              {uncertaintyNotes.map((note) => (
                <li key={note}>{note}</li>
              ))}
            </ul>
          ) : null}
          {state.status === "ready" ? (
            <button
              className="mt-2 min-h-9 rounded-xl bg-lime px-3 text-xs font-bold text-lime-ink"
              onClick={handleApply}
              type="button"
            >
              Use these values
            </button>
          ) : (
            <p className="mt-2 text-xs font-semibold text-lime">
              Applied — review the fields below before saving.
            </p>
          )}
        </div>
      ) : null}
    </div>
  );
}
