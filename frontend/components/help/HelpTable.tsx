import { ReactNode } from 'react';

interface HelpTableProps {
  headers: string[];
  rows: (string | ReactNode)[][];
}

export default function HelpTable({ headers, rows }: HelpTableProps) {
  return (
    <div className="overflow-x-auto my-4">
      <table className="w-full text-sm font-mono border border-border-default sharp-corners">
        <thead>
          <tr className="bg-bg-surface border-b border-border-default">
            {headers.map((h, i) => (
              <th
                key={i}
                className="text-left px-4 py-2.5 text-text-secondary font-semibold text-xs tracking-wide uppercase"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, ri) => (
            <tr
              key={ri}
              className="border-b border-border-muted last:border-b-0 hover:bg-bg-hover transition-colors"
            >
              {row.map((cell, ci) => (
                <td key={ci} className="px-4 py-2.5 text-text-primary">
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
