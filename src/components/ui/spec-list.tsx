import { cn } from "@/lib/utils";

interface SpecListProps {
  items: string[];
  className?: string;
  /** Compact variant used inside cards. */
  dense?: boolean;
}

function Tick() {
  return (
    <svg viewBox="0 0 16 16" fill="none" aria-hidden="true" className="mt-[7px] h-3 w-3 shrink-0">
      <path
        d="M3 8.4 6.2 11.5 13 4.5"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function SpecList({ items, className, dense = false }: SpecListProps) {
  return (
    <ul className={cn("space-y-3", dense && "space-y-2.5", className)}>
      {items.map((item) => (
        <li key={item} className="flex gap-3 text-mist-300">
          <span className="text-brass-500">
            <Tick />
          </span>
          <span className={cn("leading-relaxed", dense ? "text-[13.5px]" : "text-[15px]")}>
            {item}
          </span>
        </li>
      ))}
    </ul>
  );
}
