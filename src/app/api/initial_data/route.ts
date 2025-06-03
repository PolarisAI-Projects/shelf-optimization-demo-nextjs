import { NextResponse } from "next/server";

export async function GET() {
  try {
    // FastAPIサーバーのURLを環境変数から取得（デフォルトはlocalhost:8000）
    const apiUrl = process.env.FASTAPI_URL || "http://localhost:8000";

    const response = await fetch(`${apiUrl}/api/initial_data`);

    if (!response.ok) {
      throw new Error(
        `FastAPI server responded with status: ${response.status}`
      );
    }

    const data = await response.json();

    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching initial data:", error);
    return NextResponse.json(
      { error: "Failed to fetch initial data" },
      { status: 500 }
    );
  }
}
