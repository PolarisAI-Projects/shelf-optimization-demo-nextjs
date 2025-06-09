'use client'; // このコンポーネントがクライアントサイドで動作することを示す

import { useState, useRef } from 'react';
import CombinedShelfVisualization from './components/ShelfVisualization';

// --- データ型定義 ---
type Position = { [key: string]: string | number };
type BaseInfo = { [key:string]: string | number };

interface ShelfItem {
  start_pos: number;
  face_count: number;
  attribute: string;
  color: string;
}

interface Shelf {
  tandan: number;
  items: ShelfItem[];
  empty_space?: {
    start_pos: number;
    width: number;
  };
}

interface LayoutData {
  daiban_id: number;
  max_width: number;
  shelves: Shelf[];
}

// APIレスポンス用の型
interface ApiResponse {
  position?: Position[];
  score?: number;
  base_info?: BaseInfo[];
}

export default function Home() {
  const [positionData, setPositionData] = useState<Position[]>([]);
  const [baseInfo, setBaseInfo] = useState<BaseInfo[]>([]);
  const [score, setScore] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [allLayoutData, setAllLayoutData] = useState<LayoutData[]>([]);
  const [message, setMessage] = useState<string>('デモデータを読み込むか、ファイルをアップロードしてください。');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const updateState = (data: ApiResponse) => {
    setPositionData(data.position || []);
    setScore(data.score || 0);
    setBaseInfo(data.base_info || []);
    if (data.position && data.base_info) {
      fetchAllLayoutData(data.position, data.base_info);
    }
  };

  const handleError = (errorMsg: string) => {
    setMessage(errorMsg);
    setIsLoading(false);
    updateState({}); // Reset state
  };

  const fetchAllLayoutData = async (posData: Position[], bInfo: BaseInfo[]) => {
    try {
      const layoutPromises = bInfo.map(base =>
        fetch('/api/layout_data', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ position: posData, daiban_id: base.台番号 }),
        }).then(res => res.ok ? res.json() : null)
      );
      const results = await Promise.all(layoutPromises);
      setAllLayoutData(results.filter((r): r is LayoutData => r !== null));
    } catch (error) {
      console.error('レイアウトデータの取得エラー:', error);
      setAllLayoutData([]);
    }
  };

  const handleLoadDemo = async () => {
    setIsLoading(true);
    setMessage('デモデータを読み込んでいます...');
    try {
      const res = await fetch('/api/demo_data');
      if (!res.ok) throw new Error('デモデータの読み込みに失敗しました。');
      const data: ApiResponse = await res.json();
      updateState(data);
      setMessage('デモデータを読み込みました。最適化を実行してください。');
    } catch (error) {
      handleError(error instanceof Error ? error.message : '不明なエラーが発生しました。');
    }
    setIsLoading(false);
  };
  
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsLoading(true);
    setMessage('ファイルをアップロードしています...');
    const formData = new FormData();
    formData.append('file', file);

    try {
      const uploadRes = await fetch('/api/upload', { method: 'POST', body: formData });
      if (!uploadRes.ok) {
        const err = await uploadRes.json();
        throw new Error(err.error || 'アップロードに失敗しました。');
      }
      
      setMessage('データを初期化しています...');
      const dataRes = await fetch('/api/initial_data');
      if (!dataRes.ok) throw new Error('アップロード後のデータ取得に失敗しました。');

      const data: ApiResponse = await dataRes.json();
      updateState(data);
      setMessage('アップロード完了。最適化を実行してください。');
    } catch (error) {
      handleError(error instanceof Error ? error.message : '不明なエラーが発生しました。');
    }
    setIsLoading(false);
  };

  const handleOptimize = async () => {
    if (positionData.length === 0) {
      setMessage("最適化するデータがありません。");
      return;
    }
    setIsLoading(true);
    setMessage('最適化を実行中...');
    try {
      const res = await fetch('/api/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ position: positionData }),
      });
      if (!res.ok) throw new Error('最適化リクエストに失敗しました。');
      const data: ApiResponse = await res.json();
      updateState({ ...data, base_info: baseInfo }); // Keep original base_info
      setMessage('最適化が完了しました。');
    } catch (error) {
      handleError(error instanceof Error ? error.message : '不明なエラーが発生しました。');
    }
    setIsLoading(false);
  };

  return (
    <main className="container mx-auto p-4 md:p-8 bg-gray-50 min-h-screen">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">棚割り最適化エンジン</h1>
      
      <div className="bg-white p-4 rounded-lg shadow-md mb-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
          <div className="flex flex-col gap-2 h-full">
            <h2 className="font-bold text-lg text-gray-800 mb-2">1. データを選択</h2>
            <button onClick={handleLoadDemo} disabled={isLoading} className="bg-green-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-green-700 disabled:bg-gray-400 flex-1">
              デモデータで開始
            </button>
            <input type="file" ref={fileInputRef} onChange={handleFileUpload} accept=".xlsx" className="hidden"/>
            <button onClick={() => fileInputRef.current?.click()} disabled={isLoading} className="bg-gray-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-gray-700 disabled:bg-gray-400 flex-1">
              XLSXファイルをアップロード
            </button>
          </div>
          
          <div className="flex flex-col h-full">
            <h2 className="font-bold text-lg text-gray-800 mb-2">2. 最適化を実行</h2>
            <div className="flex-1 flex items-center">
              <button onClick={handleOptimize} disabled={isLoading || positionData.length === 0} className="bg-blue-600 text-white font-bold py-3 px-6 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 w-full">
                最適化を実行
              </button>
            </div>
          </div>

          <div className="text-center p-4 bg-gray-100 rounded-lg h-full flex flex-col justify-center">
            <p className="text-gray-600">レイアウトスコア</p>
            <p className="text-3xl font-bold text-blue-600">{score.toFixed(0)}</p>
            <p className="text-sm text-gray-500 mt-2 h-10">{isLoading ? '処理中...' : message}</p>
          </div>
        </div>
      </div>

      <div>
        <h2 className="text-2xl font-bold text-gray-800 mb-4">棚レイアウト</h2>
        <div className="bg-gray-100 p-4 rounded-lg shadow-inner min-h-[300px] flex items-center justify-center">
          {positionData.length > 0 ? (
            <CombinedShelfVisualization allLayoutData={allLayoutData} />
          ) : (
            <p className="text-gray-500">表示するデータがありません。</p>
          )}
        </div>
      </div>
    </main>
  );
}
