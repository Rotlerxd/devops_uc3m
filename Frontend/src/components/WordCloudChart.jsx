import React, { useEffect, useState, useRef } from 'react';
import cloud from 'd3-cloud';

export default function WordCloudChart({ words }) {
  const [cloudWords, setCloudWords] = useState([]);
  const containerRef = useRef(null);

  useEffect(() => {
    if (!words || words.length === 0 || !containerRef.current) return;

    const width = containerRef.current.offsetWidth || 400;
    const height = 300;

    const layout = cloud()
      .size([width, height])
      .words(words.map(d => ({ text: d.text, size: 10 + d.value * 6 })))
      .padding(5)
      .rotate(() => (~~(Math.random() * 2) * 90))
      .font("Impact")
      .fontSize(d => d.size)
      .on("end", setCloudWords);

    layout.start();
  }, [words]);

  return (
    <div ref={containerRef} style={{ width: '100%', height: '300px', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
      <svg width="100%" height="300">
        <g transform={`translate(${containerRef.current?.offsetWidth / 2 || 200}, 150)`}>
          {cloudWords.map((w, i) => (
            <text
              key={i}
              style={{
                fontSize: `${w.size}px`,
                fontFamily: 'Impact',
                fill: ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'][i % 5]
              }}
              textAnchor="middle"
              transform={`translate(${w.x},${w.y}) rotate(${w.rotate})`}
            >
              {w.text}
            </text>
          ))}
        </g>
      </svg>
    </div>
  );
}