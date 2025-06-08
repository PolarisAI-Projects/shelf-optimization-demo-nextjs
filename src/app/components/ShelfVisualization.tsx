import React from 'react';

interface Item {
  start_pos: number;
  face_count: number;
  attribute: string;
  color: string;
}

interface EmptySpace {
  start_pos: number;
  width: number;
}

interface Shelf {
  tandan: number;
  items: Item[];
  empty_space?: EmptySpace;
}

interface LayoutData {
  daiban_id: number;
  max_width: number;
  shelves: Shelf[];
}

interface CombinedShelfVisualizationProps {
  allLayoutData: LayoutData[];
}

const CombinedShelfVisualization: React.FC<CombinedShelfVisualizationProps> = ({ allLayoutData }) => {
  if (!allLayoutData || allLayoutData.length === 0) {
    return (
      <div className="bg-white p-4 rounded-lg shadow-lg">
        <p className="text-gray-500">レイアウトデータがありません</p>
      </div>
    );
  }

  // 画面幅に基づく動的サイズ計算（より余裕を持たせる）
  const containerWidth = typeof window !== 'undefined' ? Math.min(window.innerWidth * 0.85, 1200) : 1000; // より控えめに85%、最大1200px
  const totalFaces = allLayoutData.reduce((sum, layout) => sum + layout.max_width, 0);
  const marginX = 60;
  const marginY = 70; // マージンを増やして台番号とフェース位置番号の間隔を確保
  const daiGap = 80; // 台間の間隔を大きく
  
  // 動的なセルサイズ計算
  const availableWidth = containerWidth - marginX * 2 - daiGap * (allLayoutData.length - 1);
  const cellWidth = Math.max(Math.floor(availableWidth / totalFaces), 40); // 最小40px
  const cellHeight = Math.max(cellWidth * 0.8, 55); // 縦横比を調整、最小55px
  
  // 全体の幅を計算
  const svgWidth = totalFaces * cellWidth + marginX * 2 + daiGap * (allLayoutData.length - 1);
  const maxShelves = Math.max(...allLayoutData.map(layout => layout.shelves.length));
  const svgHeight = maxShelves * cellHeight + marginY * 2;

  // 商品色に応じたテキスト色を決定
  const getTextColor = (backgroundColor: string) => {
    switch (backgroundColor) {
      case '#15803d': // お茶（深い緑茶色）
        return '#ffffff'; // 白
      case '#5d2f0a': // コーヒー（より黒っぽいコーヒーブラウン）
        return '#ffffff'; // 白
      default:
        return '#000000'; // デフォルトは黒
    }
  };

  // セルサイズに基づくフォントサイズを計算（2倍に拡大）
  const baseFontSize = Math.max(Math.floor(cellWidth / 3), 16); // 最小16px（以前の2倍）
  const smallFontSize = Math.max(Math.floor(cellWidth / 4), 12); // 最小12px（以前の1.5倍）

  // 各台のX位置を計算
  let currentXOffset = marginX;
  const daiOffsets = allLayoutData.map((layout) => {
    const offset = currentXOffset;
    currentXOffset += layout.max_width * cellWidth + daiGap;
    return offset;
  });

  return (
    <div className="bg-white p-4 rounded-lg shadow-lg">
      <h3 className="text-xl font-bold text-gray-800 mb-4">統合棚レイアウト</h3>
      
      {/* レスポンシブなSVGコンテナ */}
      <div className="w-full overflow-x-auto border border-gray-200 rounded bg-gray-50">
        <div className="min-w-fit p-2">
          <svg 
            width={svgWidth} 
            height={svgHeight} 
            className="bg-white shadow-sm"
            viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          >
            {allLayoutData.map((layoutData, daiIndex) => {
              const { daiban_id, max_width, shelves } = layoutData;
              const xOffset = daiOffsets[daiIndex];
              
              return (
                <g key={`dai-${daiban_id}`}>
                  {/* 台の境界線 */}
                  <rect
                    x={xOffset - 8}
                    y={marginY - 8}
                    width={max_width * cellWidth + 16}
                    height={maxShelves * cellHeight + 16}
                    fill="none"
                    stroke="#374151"
                    strokeWidth="3"
                    strokeDasharray="10,5"
                    rx="6"
                  />
                  
                  {/* 台番号ラベル */}
                  <text
                    x={xOffset + (max_width * cellWidth) / 2}
                    y={marginY - 35}
                    textAnchor="middle"
                    fontSize={baseFontSize + 4}
                    fontWeight="bold"
                    fill="#1f2937"
                  >
                    台{daiban_id}
                  </text>

                  {/* グリッド線 */}
                  {Array.from({ length: max_width + 1 }, (_, i) => (
                    <line
                      key={`grid-v-${daiIndex}-${i}`}
                      x1={xOffset + i * cellWidth}
                      y1={marginY}
                      x2={xOffset + i * cellWidth}
                      y2={svgHeight - marginY}
                      stroke="#e5e7eb"
                      strokeWidth="0.5"
                    />
                  ))}
                  
                  {Array.from({ length: maxShelves + 1 }, (_, i) => (
                    <line
                      key={`grid-h-${daiIndex}-${i}`}
                      x1={xOffset}
                      y1={marginY + i * cellHeight}
                      x2={xOffset + max_width * cellWidth}
                      y2={marginY + i * cellHeight}
                      stroke="#e5e7eb"
                      strokeWidth="0.5"
                    />
                  ))}

                  {/* 棚段ラベル */}
                  {shelves.map((shelf, shelfIndex) => (
                    <text
                      key={`label-${daiIndex}-${shelf.tandan}`}
                      x={xOffset - 35}
                      y={marginY + shelfIndex * cellHeight + cellHeight / 2}
                      textAnchor="middle"
                      dominantBaseline="central"
                      fontSize={smallFontSize + 2}
                      fontWeight="700"
                      fill="#374151"
                    >
                      {shelf.tandan}段
                    </text>
                  ))}

                  {/* フェース位置番号 */}
                  {Array.from({ length: max_width }, (_, i) => (
                    <text
                      key={`pos-${daiIndex}-${i}`}
                      x={xOffset + i * cellWidth + cellWidth / 2}
                      y={marginY - 15}
                      textAnchor="middle"
                      fontSize={smallFontSize}
                      fontWeight="500"
                      fill="#6b7280"
                    >
                      {i + 1}
                    </text>
                  ))}

                  {/* 商品アイテム */}
                  {shelves.map((shelf, shelfIndex) => (
                    <g key={`shelf-${daiIndex}-${shelf.tandan}`}>
                      {shelf.items.map((item, itemIndex) => (
                        <g key={`item-${daiIndex}-${shelf.tandan}-${itemIndex}`}>
                          {/* 商品の矩形 */}
                          <rect
                            x={xOffset + item.start_pos * cellWidth}
                            y={marginY + shelfIndex * cellHeight}
                            width={item.face_count * cellWidth}
                            height={cellHeight}
                            fill={item.color}
                            stroke="#1f2937"
                            strokeWidth="1.5"
                            opacity="0.95"
                            rx="3"
                          />
                          
                          {/* 商品テキスト（白い帯は削除） */}
                          <text
                            x={xOffset + item.start_pos * cellWidth + (item.face_count * cellWidth) / 2}
                            y={marginY + shelfIndex * cellHeight + cellHeight / 2 - 6}
                            textAnchor="middle"
                            dominantBaseline="central"
                            fontSize={baseFontSize}
                            fontWeight="bold"
                            fill={getTextColor(item.color)}
                          >
                            {item.attribute}
                          </text>
                          
                          {/* フェース数表示 */}
                          <text
                            x={xOffset + item.start_pos * cellWidth + (item.face_count * cellWidth) / 2}
                            y={marginY + shelfIndex * cellHeight + cellHeight / 2 + baseFontSize - 4}
                            textAnchor="middle"
                            dominantBaseline="central"
                            fontSize={smallFontSize}
                            fontWeight="600"
                            fill={getTextColor(item.color)}
                          >
                            ({item.face_count})
                          </text>
                        </g>
                      ))}
                      
                      {/* 空きスペース */}
                      {shelf.empty_space && (
                        <g>
                          <rect
                            x={xOffset + shelf.empty_space.start_pos * cellWidth}
                            y={marginY + shelfIndex * cellHeight}
                            width={shelf.empty_space.width * cellWidth}
                            height={cellHeight}
                            fill="rgba(156, 163, 175, 0.1)"
                            stroke="#9ca3af"
                            strokeWidth="2"
                            strokeDasharray="6,3"
                            rx="3"
                          />
                          
                          <text
                            x={xOffset + shelf.empty_space.start_pos * cellWidth + (shelf.empty_space.width * cellWidth) / 2}
                            y={marginY + shelfIndex * cellHeight + cellHeight / 2}
                            textAnchor="middle"
                            dominantBaseline="central"
                            fontSize={baseFontSize}
                            fontWeight="600"
                            fill="#6b7280"
                          >
                            空き
                          </text>
                        </g>
                      )}
                    </g>
                  ))}
                </g>
              );
            })}
          </svg>
        </div>
      </div>
      
      {/* 凡例（黒文字に変更） */}
      <div className="mt-4 flex flex-wrap gap-4 text-sm font-medium text-black">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded" style={{backgroundColor: '#15803d'}}></div>
          <span>お茶</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded" style={{backgroundColor: '#5d2f0a'}}></div>
          <span>コーヒー</span>
        </div>
      </div>
    </div>
  );
};

export default CombinedShelfVisualization; 
