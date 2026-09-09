import { cn } from "@/lib/utils";
import type { MessagingLink } from "@/types";

export type IconName = MessagingLink["icon"] | "arrow" | "close" | "menu";

const paths: Record<IconName, React.ReactNode> = {
  instagram: (
    <>
      <rect x="3" y="3" width="18" height="18" rx="5" />
      <circle cx="12" cy="12" r="4" />
      <circle cx="17.2" cy="6.8" r="1.1" fill="currentColor" stroke="none" />
    </>
  ),
  telegram: <path d="M21 4.5 2.8 11.4c-.8.3-.8 1.4 0 1.7l4.5 1.5 1.7 5c.2.7 1.1.9 1.6.3l2.4-2.6 4.6 3.4c.6.4 1.4.1 1.6-.6L22.4 5.6c.2-.8-.6-1.4-1.4-1.1Z" />,
  whatsapp: (
    <>
      <path d="M3.5 20.5 4.9 16A8.2 8.2 0 1 1 8 19.1l-4.5 1.4Z" />
      <path d="M9 9.2c.3-.7.6-.7.9-.7h.7c.2 0 .6 0 .8.6l.7 1.7c.1.3 0 .5-.1.7l-.5.6c-.2.2-.3.4-.1.7.6 1 1.5 1.9 2.6 2.4.3.1.5.1.7-.1l.6-.7c.2-.2.4-.3.7-.2l1.7.8c.3.1.5.3.5.6a2 2 0 0 1-1.4 2 4 4 0 0 1-2-.1A9.6 9.6 0 0 1 9.3 13a4 4 0 0 1-.8-2.3c0-.6.2-1.1.5-1.5Z" />
    </>
  ),
  viber: (
    <>
      <path d="M12 2.5c5 0 8 2.6 8 7.2 0 4.5-3 7.1-8 7.1h-.6l-3 3.5c-.4.5-1.2.2-1.2-.5v-3.4C4.9 15.3 4 13 4 9.7 4 5.1 7 2.5 12 2.5Z" />
      <path d="M9.4 7.3c.2-.4.4-.4.6-.4h.5c.2 0 .4 0 .5.4l.5 1.1c.1.2 0 .4-.1.5l-.3.4c-.2.2-.2.3 0 .5.4.7 1 1.3 1.7 1.6.2.1.4.1.5-.1l.4-.4c.1-.2.3-.2.5-.1l1.1.5c.2.1.3.2.3.4a1.4 1.4 0 0 1-.9 1.3 2.6 2.6 0 0 1-1.4 0 6.4 6.4 0 0 1-3.7-3.2 2.7 2.7 0 0 1-.5-1.5c0-.4.1-.8.3-1Z" />
    </>
  ),
  phone: (
    <path d="M6.3 3.5h2.3l1.6 4-2 1.4a11 11 0 0 0 5.4 5.4l1.4-2 4 1.6v2.3c0 1.1-.9 2-2 1.9A15.7 15.7 0 0 1 4.4 5.5c-.1-1.1.8-2 1.9-2Z" />
  ),
  email: (
    <>
      <rect x="2.8" y="5" width="18.4" height="14" rx="2.5" />
      <path d="m4 7 8 5.6L20 7" />
    </>
  ),
  arrow: <path d="M4 12h15M13 6l6 6-6 6" />,
  close: <path d="M6 6l12 12M18 6 6 18" />,
  menu: <path d="M4 8h16M4 16h16" />,
};

export function Icon({ name, className }: { name: IconName; className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={cn("h-5 w-5", className)}
    >
      {paths[name]}
    </svg>
  );
}
