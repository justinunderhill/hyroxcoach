"use client";

import { useRef } from "react";

import { MeasurementFeed, MeasurementFeedHandle } from "@/components/measurement-feed";
import { MeasurementForm } from "@/components/measurement-form";

export function MeasurementsClient() {
  const feedRef = useRef<MeasurementFeedHandle>(null);

  return (
    <div className="space-y-10">
      <MeasurementForm onLogged={() => feedRef.current?.refresh()} />
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-stone-400">History</p>
        <div className="mt-3">
          <MeasurementFeed ref={feedRef} />
        </div>
      </div>
    </div>
  );
}
