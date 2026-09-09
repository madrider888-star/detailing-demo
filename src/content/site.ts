import type { NavItem } from "@/types";

export const site = {
  name: "Apex Detailing",
  legalName: "Apex Detailing Studio",
  tagline: "Paint protection & appearance studio",
  description:
    "Apex Detailing is a paint protection and appearance studio in Odessa. Ceramic coatings, paint protection film, paint correction and interior restoration for enthusiast and collector vehicles.",
  url: "https://apexdetailing.demo",
  locale: "en_US",
  phone: "+380 48 700 21 40",
  phoneHref: "+380487002140",
  email: "hello@apexdetailing.demo",
  address: {
    street: "14 Prymorska Street, Bay 3",
    city: "Odessa",
    region: "Odesa Oblast",
    postalCode: "65014",
    country: "Ukraine",
  },
  hours: [
    { days: "Monday – Friday", time: "09:00 – 20:00" },
    { days: "Saturday", time: "10:00 – 18:00" },
    { days: "Sunday", time: "By appointment" },
  ],
  social: [
    { label: "Instagram", href: "https://instagram.com" },
    { label: "YouTube", href: "https://youtube.com" },
    { label: "Telegram", href: "https://telegram.org" },
  ],
  stats: [
    { value: "11", label: "Years in the trade" },
    { value: "2 400+", label: "Vehicles finished" },
    { value: "6", label: "Climate-controlled bays" },
    { value: "10 yr", label: "Longest coating warranty" },
  ],
} as const;

export const mainNav: NavItem[] = [
  { label: "Services", href: "/services" },
  { label: "Pricing", href: "/pricing" },
  { label: "Gallery", href: "/gallery" },
  { label: "About", href: "/about" },
  { label: "Contact", href: "/contact" },
];

export const footerNav: { title: string; items: NavItem[] }[] = [
  {
    title: "Studio",
    items: [
      { label: "About the studio", href: "/about" },
      { label: "Gallery", href: "/gallery" },
      { label: "Pricing", href: "/pricing" },
      { label: "Book an appointment", href: "/contact" },
    ],
  },
  {
    title: "Protection",
    items: [
      { label: "Ceramic Coating", href: "/services/ceramic-coating" },
      { label: "Paint Protection Film", href: "/services/paint-protection-film" },
      { label: "Full Body PPF", href: "/services/full-body-ppf" },
      { label: "Wheel Protection", href: "/services/wheel-protection" },
    ],
  },
  {
    title: "Detailing",
    items: [
      { label: "Paint Correction", href: "/services/paint-correction" },
      { label: "Interior Detailing", href: "/services/interior-detailing" },
      { label: "Full Detailing", href: "/services/full-detailing" },
      { label: "Window Tinting", href: "/services/window-tinting" },
    ],
  },
];
