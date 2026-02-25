import { ReactNode } from 'react';

interface PanelProps {
  children: ReactNode;
  title?: string;
  className?: string;
  headerRight?: ReactNode;
  noPadding?: boolean;
}

export function Panel({ children, title, className = '', headerRight, noPadding = false }: PanelProps) {
  return (
    <div className={`bg-[#12121a] border border-[#27272a] rounded-lg flex flex-col overflow-hidden ${className}`}>
      {title && (
        <div className="flex items-center justify-between px-4 py-2 border-b border-[#27272a] flex-shrink-0">
          <span className="text-xs font-medium uppercase tracking-widest text-zinc-400">{title}</span>
          {headerRight && <div>{headerRight}</div>}
        </div>
      )}
      <div className={`flex-1 overflow-hidden ${noPadding ? '' : 'p-2'}`}>
        {children}
      </div>
    </div>
  );
}
