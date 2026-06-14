"use client";

import { useEffect, useState } from "react";
import { testBackend } from "@/lib/api";

export default function Home() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    testBackend().then(setData);
  }, []);

  return (
    <div className="p-10">
      <h1>R.E.I Interface</h1>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}