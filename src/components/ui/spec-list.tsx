import { cn } from "@/lib/utils";

/** Ticked list used for "what's included" blocks. */
export function SpecList({
  items,
  className,
  dense = false,
}: {
  items: string[];
  className?: string;
  dense?: boolean;
}) {
  return (
    <ul className={cn("space-y-3", dense && "space-y-2.5", className)}>
      {items.map((item) => (
        <li key={item} className="flex gap-3 text-chalk-300">
          <svg
            viewBox="0 0 16 16"
            fill="none"
            aria-hidden="true"
            className="mt-[7px] h-3 w-3 shrink-0 text-accent"
          >
            <path
              d="M3 8.4 6.2 11.5 13 4.5"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <span className={cn("leading-relaxed", dense ? "text-[13.5px]" : "text-[15px]")}>
            {item}
          </span>
        </li>
      ))}
    </ul>
  );
}
