import { authenticatedFetch } from "@/lib/auth/client";

export type MediaPurpose = "workout_evidence" | "meal_photo" | "measurement" | "other";
export type MediaEntityType = "workout" | "meal" | "measurement";

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

/** Requests a presigned upload target, then PUTs the file directly to storage. */
export async function uploadMedia(
  file: File,
  options: { purpose: MediaPurpose; entityType: MediaEntityType; entityId: string },
): Promise<void> {
  const intentResponse = await authenticatedFetch("/api/media/upload-intent", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      purpose: options.purpose,
      mime_type: file.type,
      size_bytes: file.size,
      entity_type: options.entityType,
      entity_id: options.entityId,
    }),
  });

  if (!intentResponse.ok) {
    const body = await intentResponse.json().catch(() => null);
    const message = body?.error?.message;
    throw new Error(typeof message === "string" ? message : "The photo could not be uploaded.");
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
