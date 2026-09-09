import type { GalleryCategory, GalleryItem } from "@/types";

export const galleryFilters: { id: GalleryCategory | "all"; label: string }[] = [
  { id: "all", label: "All work" },
  { id: "before-after", label: "Before / After" },
  { id: "ceramic", label: "Ceramic Coating" },
  { id: "ppf", label: "Paint Protection Film" },
  { id: "interior", label: "Interior" },
  { id: "correction", label: "Paint Correction" },
];

export const galleryItems: GalleryItem[] = [
  {
    id: "g-01",
    title: "Three-stage correction, split panel",
    vehicle: "Audi RS6 — Nardo Grey",
    category: "before-after",
    image: "/media/gallery/g-01.svg",
    span: "wide",
  },
  { id: "g-02", title: "10-year coating, week one", vehicle: "Porsche 911 GT3 — Jet Black", category: "ceramic", image: "/media/gallery/g-02.svg" },
  { id: "g-03", title: "Full body film, bonnet edge wrap", vehicle: "BMW M4 Competition", category: "ppf", image: "/media/gallery/g-03.svg" },
  { id: "g-04", title: "Cabin reset after 140,000 km", vehicle: "Range Rover Sport", category: "interior", image: "/media/gallery/g-04.svg" },
  { id: "g-05", title: "Two-stage correction, finished", vehicle: "Mercedes-AMG E63 S", category: "correction", image: "/media/gallery/g-05.svg", span: "wide" },
  { id: "g-06", title: "Beading after 14 months", vehicle: "Tesla Model 3 — Solid Black", category: "ceramic", image: "/media/gallery/g-06.svg" },
  { id: "g-07", title: "Front impact package", vehicle: "Porsche Taycan Turbo", category: "ppf", image: "/media/gallery/g-07.svg" },
  { id: "g-08", title: "Black Nappa, cleaned and sealed", vehicle: "Audi Q8 — Valcona", category: "interior", image: "/media/gallery/g-08.svg" },
  { id: "g-09", title: "Swirl removal, split test panel", vehicle: "Volkswagen Golf R", category: "before-after", image: "/media/gallery/g-09.svg" },
  { id: "g-10", title: "Coating handover, studio lighting", vehicle: "Land Rover Defender 110", category: "ceramic", image: "/media/gallery/g-10.svg", span: "wide" },
  { id: "g-11", title: "Wheels off, barrels coated", vehicle: "BMW M5 — Forged 20″", category: "ceramic", image: "/media/gallery/g-11.svg" },
  { id: "g-12", title: "Nano-ceramic film, full vehicle", vehicle: "Mercedes-Benz S-Class", category: "interior", image: "/media/gallery/g-12.svg" },
  { id: "g-13", title: "Shoulder line after refinement", vehicle: "Porsche Panamera GTS", category: "correction", image: "/media/gallery/g-13.svg", span: "wide" },
  { id: "g-14", title: "Lens restoration and UV seal", vehicle: "Audi A6 — 12 years old", category: "correction", image: "/media/gallery/g-14.svg" },
  { id: "g-15", title: "Cognac leather, protected", vehicle: "BMW 8 Series Gran Coupé", category: "interior", image: "/media/gallery/g-15.svg" },
  { id: "g-16", title: "Enhancement polish, dark metallic", vehicle: "Škoda Superb — Business fleet", category: "before-after", image: "/media/gallery/g-16.svg" },
];
