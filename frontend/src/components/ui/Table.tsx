import React from 'react';

interface TableProps {
  headers: string[];
  rows: React.ReactNode[][];
  onRowClick?: (rowIndex: number) => void;
  className?: string;
}

export function Table({
  headers,
  rows,
  onRowClick,
  className = '',
}: TableProps) {
  return (
    <div className={`overflow-x-auto rounded-lg border border-slate-800 ${className}`}>
      <table className="w-full text-left text-sm text-slate-300">
        <thead className="bg-slate-950/70 border-b border-slate-800 text-xs uppercase tracking-wider text-slate-400">
          <tr>
            {headers.map((header, index) => (
              <th key={index} className="py-3 px-4 font-semibold">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/60 bg-slate-900/40">
          {rows.map((row, rowIndex) => (
            <tr
              key={rowIndex}
              onClick={() => onRowClick && onRowClick(rowIndex)}
              className={`transition-colors ${
                onRowClick
                  ? 'cursor-pointer hover:bg-slate-800/60'
                  : 'hover:bg-slate-800/40'
              }`}
            >
              {row.map((cell, cellIndex) => (
                <td key={cellIndex} className="py-3 px-4 whitespace-nowrap">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
