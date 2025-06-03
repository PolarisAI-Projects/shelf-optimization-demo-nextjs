'use client'; // このコンポーネントがクライアントサイドで動作することを示す

import { useState, useEffect } from 'react';

// データ型を定義
type Position = { [key: string]: any };
type BaseInfo = { 台番号: number, [key: string]: any };

export default function Home() {
  const [positionData, setPositionData] = useState<Position[]>([]);
  const [baseInfo, setBaseInfo] = useState<BaseInfo[]>([]);
  const [score, setScore] = useState<number>(0);
  const [iterations, setIterations] = useState<number>(500);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [imageUrl, setImageUrl] = useState<string>(''); // 表示する画像のURLを管理

  // 初期データをロードする関数
  const loadInitialData = async () => {
    setIsLoading(true);
    const res = await fetch('/api/initial_data');
    const data = await res.json();
    setPositionData(data.position);
    setScore(data.score);
    setBaseInfo(data.base_info);
    setIsLoading(false);
  };

  // ページロード時に初期データを取得
  useEffect(() => {
    loadInitialData();
  }, []);

  // 最適化を実行する関数
  const handleOptimize = async () => {
    setIsLoading(true);
    const res = await fetch('/api/optimize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ position: positionData, iterations: iterations }),
    });
    const data = await res.json();
    setPositionData(data.position);
    setScore(data.score);
    setIsLoading(false);
  };
  
  // 台を選択して画像を表示する関数
  const handleVisualize = async (daibanId: number) => {
    const res = await fetch('/api/visualize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ position: positionData, daiban_id: daibanId }),
    });
    if (res.ok) {
        const imageBlob = await res.blob();
        // 既存のURLを破棄してメモリリークを防ぐ
        if (imageUrl) URL.revokeObjectURL(imageUrl);
        const newImageUrl = URL.createObjectURL(imageBlob);
        setImageUrl(newImageUrl);
    }
  };


  return (
    <main className="container mx-auto p-4 md:p-8 bg-gray-50 min-h-screen">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">棚割り最適化デモ</h1>

      {/* 操作パネル */}
      <div className="bg-white p-4 rounded-lg shadow-md mb-8 flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2">
          <label htmlFor="iterations" className="font-semibold text-gray-700">試行回数:</label>
          <input
            type="number"
            id="iterations"
            value={iterations}
            onChange={(e) => setIterations(Number(e.target.value))}
            className="border-gray-300 rounded-md shadow-sm w-24 p-2"
          />
        </div>
        <button
          onClick={handleOptimize}
          disabled={isLoading}
          className="bg-blue-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
        >
          {isLoading ? '実行中...' : `${iterations}回 最適化を実行`}
        </button>
        <button
          onClick={loadInitialData}
          disabled={isLoading}
          className="bg-gray-500 text-white font-bold py-2 px-4 rounded-lg hover:bg-gray-600 disabled:bg-gray-400"
        >
          リセット
        </button>
        <div className="ml-auto text-right">
          <p className="text-gray-600">現在のレイアウトスコア</p>
          <p className="text-2xl font-bold text-blue-600">{score.toFixed(0)}</p>
        </div>
      </div>

      {/* 可視化エリア */}
      <div>
        <h2 className="text-2xl font-bold text-gray-800 mb-4">現在の棚レイアウト</h2>
        <div className="mb-4">
          <p className="font-semibold mb-2">表示する台を選択してください:</p>
          <div className="flex flex-wrap gap-2">
            {baseInfo.map((base) => (
              <button
                key={base.台番号}
                onClick={() => handleVisualize(base.台番号)}
                className="bg-white border border-gray-300 py-2 px-4 rounded-md hover:bg-gray-100"
              >
                台番号: {base.台番号}
              </button>
            ))}
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow-inner min-h-[200px] flex items-center justify-center">
          {imageUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={imageUrl} alt="棚レイアウト" className="max-w-full" />
          ) : (
            <p className="text-gray-500">上のボタンから表示したい台を選択してください。</p>
          )}
        </div>
      </div>
    </main>
  );
}
