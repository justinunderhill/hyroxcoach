import { authenticatedFetch } from "@/lib/auth/client";

export type MediaPurpose = "workout_evidence" | "meal_photo" | "measurement" | "other";
export type MediaEntityType = "workout" | "meal" | "measurement";
export type ExtractionType = "workout" | "meal";

type UploadIntentResponse = {
  media_asset: { id: string };
  upload_url: string;
  upload_headers: Record<string, string>;
};

export type MediaItem = {
  media_asset: { id: string; mime_type: string; created_at: string };
  entity_type: MediaEntityType;
  entity_id: string;
  view_url: string;
};

export type ExtractionResult = {
  id: string;
  media_asset_id: string;
  extraction_type: ExtractionType;
  model_name: string;
  status: "succeeded" | "failed";
  confidence: number | null;
  extracted_data: Record<string, unknown>;
  user_confirmed: boolean;
  confirmed_data: Record<string, unknown> | null;
  error_message: string | null;
  created_at: string;
  confirmed_at: string | null;
};

async function errorMessage(response: Response, fallback: string): Promise<string> {
  const body = await response.json().catch(() => null);
  const message = body?.error?.message;
  return typeof message === "string" ? message : fallback;
}

/** Uploads a file to storage and returns the created media asset id, unlinked to any entity yet. */
export async function uploadMediaAsset(file: File, purpose: MediaPurpose): Promise<string> {
  const intentResponse = await authenticatedFetch("/api/media/upload-intent", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ purpose, mime_type: file.type, size_bytes: file.size }),
  });
  if (!intentResponse.ok) {
    throw new Error(await errorMessage(intentResponse, "The photo could not be uploaded."));
  }

  const intent: UploadIntentResponse = await intentResponse.json();
  const putResponse = await fetch(intent.upload_url, {
    method: "PUT",
    headers: intent.upload_headers,
    body: file,
  });
  if (!putResponse.ok) {
    throw new Error("The photo could not be uploaded.");
  }

  return intent.media_asset.id;
}

/** Attaches an already-uploaded media asset to an owned entity. Safe to call more than once. */
export async function linkMedia(
  mediaAssetId: string,
  entityType: MediaEntityType,
  entityId: string,
): Promise<void> {
  const response = await authenticatedFetch(`/api/media/${mediaAssetId}/link`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ entity_type: entityType, entity_id: entityId }),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "The photo could not be attached."));
  }
}

/** Requests synchronous AI extraction for an already-uploaded media asset. */
export async function requestExtraction(
  mediaAssetId: string,
  extractionType: ExtractionType,
): Promise<ExtractionResult> {
  const response = await authenticatedFetch(`/api/media/${mediaAssetId}/extract`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ extraction_type: extractionType }),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "The photo could not be analyzed."));
  }
  return response.json();
}

/** Records the user's reviewed/corrected extraction values. Never creates a workout/meal itself. */
export async function confirmExtraction(
  mediaAssetId: string,
  extractionResultId: string,
  confirmedData: Record<string, unknown>,
): Promise<void> {
  const response = await authenticatedFetch(`/api/media/${mediaAssetId}/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      extraction_result_id: extractionResultId,
      confirmed_data: confirmedData,
    }),
  });
  if (!response.ok) {
    throw new Error(await errorMessage(response, "The correction could not be saved."));
  }
}

/** Batch-fetches media for a set of entities of the same type. */
export async function listMedia(
  entityType: MediaEntityType,
  entityIds: string[],
  signal?: AbortSignal,
): Promise<MediaItem[]> {
  if (entityIds.length === 0) return [];

  const params = new URLSearchParams({
    entity_type: entityType,
    entity_ids: entityIds.join(","),
  });
  const response = await authenticatedFetch(`/api/media?${params.toString()}`, { signal });
  if (!response.ok) throw new Error("Media could not be loaded.");
  return response.json();
}
