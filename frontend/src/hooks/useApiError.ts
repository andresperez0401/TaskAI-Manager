import { useState } from "react";

export function useApiError() {
  const [error, setError] = useState("");

  function capture(err: unknown) {
    setError(err instanceof Error ? err.message : "Unexpected error");
  }

  return { error, setError, capture };
}
