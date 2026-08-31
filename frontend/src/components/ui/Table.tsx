interface TableProps {
  headers: string[];
  rows: React.ReactNode[][];
  className?: string;
}

export function Table({ headers, rows, className = '' }: TableProps) {
  return (
    <div className={`overflow-x-auto ${className}`}>
      <table className="w-full text-left">
        <thead>
          <tr className="border-b border-soc-panelLight">
            {headers.map((header, index) => (
              <th key={index} className="py-3 px-4 text-sm font-semibold text-gray-300">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={rowIndex} className="border-b border-soc-panelLight hover:bg-soc-panelLight">
              {row.map((cell, cellIndex) => (
                <td key={cellIndex} className="py-3 px-4 text-sm">
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
