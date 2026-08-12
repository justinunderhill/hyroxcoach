"use client";

import { useRef } from "react";

import { StepsForm } from "@/components/steps-form";
import { StepsSummary, StepsSummaryHandle } from "@/components/steps-summary";

export function StepsClient() {
  const summaryRef = useRef<StepsSummaryHandle>(null);

  return (
    <div className="space-y-8">
      <StepsSummary ref={summaryRef} />
      <div className="rounded-3xl border border-stone-200 bg-white p-6">
        <StepsForm onSaved={() => summaryRef.current?.refresh()} />
      </div>
    </div>
  );
}
