import { Layer, Line, Stage } from "react-konva";

export function KonvaStroke({
  points,
  guide,
  brushSize,
}: {
  points: [number, number][];
  guide: boolean;
  brushSize: number;
}) {
  return (
    <Stage
      className="konva-layer"
      width={100}
      height={100}
      listening={false}
      style={{ position: "absolute", inset: 0, width: "100%", height: "100%", zIndex: 3, pointerEvents: "none" }}
    >
      <Layer>
        {points.length > 1 && (
          <Line
            points={points.flat()}
            closed={false}
            stroke={guide ? "#ffc857" : "#ff6b6b"}
            strokeWidth={guide ? 1.2 : Math.max(1.5, brushSize / 18)}
            lineCap="round"
            lineJoin="round"
          />
        )}
      </Layer>
    </Stage>
  );
}
