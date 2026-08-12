"use client";

import { useRef } from "react";

import { CindyHistory, CindyHistoryHandle } from "@/components/cindy-history";
import { CindyTimer } from "@/components/cindy-timer";

export function CindyClient() {
  const historyRef = useRef<CindyHistoryHandle>(null);

  return (
    <div className="space-y-8">
      <CindyTimer onCompleted={() => historyRef.current?.refresh()} />
      <CindyHistory ref={historyRef} />
    </div>
  );
}
