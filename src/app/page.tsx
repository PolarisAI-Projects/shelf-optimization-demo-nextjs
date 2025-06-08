'use client'; // このコンポーネントがクライアントサイドで動作することを示す

import { useState, useEffect } from 'react';
import CombinedShelfVisualization from './components/ShelfVisualization';

// データ型を定義
type Position = {
  商品コード: string;
  台番号: number;
  棚段番号: number;
  棚位置: number;
  フェース数: number;
  [key: string]: string | number;
};

type BaseInfo = { 
  台番号: number;
  フェイス数: number;
  [key: string]: string | number;
};

interface LayoutData {
  daiban_id: number;
  max_width: number;
  shelves: Array<{
    tandan: number;
    items: Array<{
      start_pos: number;
      face_count: number;
      attribute: string;
      color: string;
    }>;
    empty_space?: {
      start_pos: number;
      width: number;
    };
  }>;
}

export default function Home() {
  const [positionData, setPositionData] = useState<Position[]>([]);
  const [baseInfo, setBaseInfo] = useState<BaseInfo[]>([]);
  const [score, setScore] = useState<number>(0);
  const [iterations, setIterations] = useState<number>(500);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [allLayoutData, setAllLayoutData] = useState<LayoutData[]>([]);

  // 初期データをロードする関数
  const loadInitialData = async () => {
    setIsLoading(true);
    const res = await fetch('/api/initial_data');
    const data = await res.json();
    setPositionData(data.position);
    setScore(data.score);
    setBaseInfo(data.base_info);
    
    // 全ての台のレイアウトデータを取得
    await fetchAllLayoutData(data.position);
    
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
    
    // 全ての台のレイアウトデータを更新
    await fetchAllLayoutData(data.position);
    
    setIsLoading(false);
  };
  
  // 全ての台のレイアウトデータを取得する関数
  const fetchAllLayoutData = async (posData: Position[]) => {
    try {
      if (baseInfo.length === 0) return;
      
      const layoutPromises = baseInfo.map(async (base) => {
        const res = await fetch('/api/layout_data', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ position: posData, daiban_id: base.台番号 }),
        });
        
        if (res.ok) {
          return await res.json();
        } else {
          console.error(`台番号 ${base.台番号} のレイアウトデータの取得に失敗しました`);
          return null;
        }
      });
      
      const results = await Promise.all(layoutPromises);
      const validResults = results.filter(result => result !== null);
      setAllLayoutData(validResults);
    } catch (error) {
      console.error('レイアウトデータの取得中にエラーが発生しました:', error);
      setAllLayoutData([]);
    }
  };

  // baseInfoが更新されたときに全てのレイアウトデータを取得
  useEffect(() => {
    if (baseInfo.length > 0 && positionData.length > 0) {
      fetchAllLayoutData(positionData);
    }
  }, [baseInfo]);

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
          {isLoading ? '実行中...' : '最適化を実行'}
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
        
        <div className="bg-gray-100 p-4 rounded-lg shadow-inner">
          <CombinedShelfVisualization allLayoutData={allLayoutData} />
        </div>
      </div>
    </main>
  );
}
