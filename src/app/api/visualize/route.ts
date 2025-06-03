import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    // FastAPIサーバーのURLを環境変数から取得（デフォルトはlocalhost:8000）
    const apiUrl = process.env.FASTAPI_URL || "http://localhost:8000";

    const body = await request.json();

    const response = await fetch(`${apiUrl}/api/visualize`, {
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

    // 画像レスポンスをそのまま返す
    const imageBlob = await response.blob();

    return new NextResponse(imageBlob, {
      headers: {
        "Content-Type": "image/png",
      },
    });
  } catch (error) {
    console.error("Error visualizing:", error);
    return NextResponse.json({ error: "Failed to visualize" }, { status: 500 });
  }
}
