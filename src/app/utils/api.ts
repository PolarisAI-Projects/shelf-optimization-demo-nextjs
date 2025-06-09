// API base URL configuration
export const getApiBaseUrl = () => {
  // Vercelでデプロイされた場合はVercelのURLを使用
  if (process.env.NEXT_PUBLIC_VERCEL_URL) {
    return `https://${process.env.NEXT_PUBLIC_VERCEL_URL}`;
  }

  // 開発環境では localhost を使用
  if (process.env.NODE_ENV === "development") {
    return "http://localhost:3000";
  }

  // フォールバック：現在のorigin
  return typeof window !== "undefined" ? window.location.origin : "";
};

export const apiCall = async (endpoint: string, options?: RequestInit) => {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}${endpoint}`;

  // FormDataの場合はContent-Typeを設定しない（ブラウザが自動設定）
  const isFormData = options?.body instanceof FormData;
  const headers: HeadersInit = isFormData
    ? {}
    : { "Content-Type": "application/json" };

  return fetch(url, {
    ...options,
    headers: {
      ...headers,
      ...options?.headers,
    },
  });
};
