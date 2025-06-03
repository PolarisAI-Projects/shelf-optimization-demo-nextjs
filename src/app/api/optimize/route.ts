import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    // FastAPIサーバーのURLを環境変数から取得（デフォルトはlocalhost:8000）
    const apiUrl = process.env.FASTAPI_URL || "http://localhost:8000";

    const body = await request.json();

    const response = await fetch(`${apiUrl}/api/optimize`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(
        `FastAPI server responded with status: ${response.status}`
      );
    }

    const data = await response.json();

    return NextResponse.json(data);
  } catch (error) {
    console.error("Error optimizing:", error);
    return NextResponse.json({ error: "Failed to optimize" }, { status: 500 });
  }
}
