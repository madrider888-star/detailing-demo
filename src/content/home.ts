import type { ComparisonPair, FaqItem, ProcessStep } from "@/types";

export const differentiators = [
  {
    title: "Measured, not guessed",
    description:
      "Paint depth is read across 24 points before a machine touches the car. You get the readings in writing, and we stop before the clear coat is compromised.",
    metric: "24-point paint depth report",
  },
  {
    title: "Six climate-controlled bays",
    description:
      "Filtered, positive-pressure rooms held at 21°C. Dust does not land in a coating and film does not cure against contamination.",
    metric: "21°C · filtered · positive pressure",
  },
  {
    title: "One car per technician",
    description:
      "No rotation, no handovers halfway through a correction. The person who reads your paint is the person who finishes it.",
    metric: "Named technician on every job",
  },
  {
    title: "Warranties you can call in",
    description:
      "Coatings are registered with the manufacturer and serviced annually in-house. The paperwork travels with the car when you sell it.",
    metric: "Up to 10 years, transferable",
  },
];

export const materials = [
  {
    name: "SiO₂ coating systems",
    detail:
      "Three, five and ten-year silica systems, each matched to how the car is actually used rather than sold as a single tier.",
    spec: "9H · 90° contact angle",
  },
  {
    name: "TPU protection film",
    detail:
      "190-micron thermoplastic urethane with an elastomeric self-healing top coat and a ten-year non-yellowing warranty.",
    spec: "190 µm · self-healing",
  },
  {
    name: "Nano-ceramic window film",
    detail:
      "Non-metallic construction that rejects infrared heat without interfering with GPS, keyless entry or mobile signal.",
    spec: "99% UV · IR selective",
  },
  {
    name: "Rupes & Flex machines",
    detail:
      "Calibrated dual-action and forced-rotation polishers with pad inventories replaced on a fixed schedule, not when they wear out.",
    spec: "15 mm & 21 mm throw",
  },
  {
    name: "Deionised water plant",
    detail:
      "Every final rinse runs through a two-stage deionisation column, so nothing dries onto the paint and leaves minerals behind.",
    spec: "0 TDS final rinse",
  },
  {
    name: "Inspection lighting",
    detail:
      "Colour-matched LED, halogen and swirl-finder lamps. Defects that hide under one light source do not hide under three.",
    spec: "3 light sources · CRI 96",
  },
];

export const studioProcess: ProcessStep[] = [
  {
    title: "Consultation",
    description:
      "We look at the car with you under proper lighting, listen to how you use it, and recommend the smallest job that gets the result.",
    duration: "Day 0",
  },
  {
    title: "Assessment & report",
    description:
      "Paint depth readings, defect mapping and photographs. You approve a written scope before anything starts.",
    duration: "Day 1",
  },
  {
    title: "Decontamination",
    description:
      "Chemical and mechanical decontamination until the surface is genuinely clean — the step most shops shorten.",
    duration: "Day 1",
  },
  {
    title: "Correction or installation",
    description:
      "Machine polishing to the agreed target, or film installation with wrapped edges, in a filtered bay.",
    duration: "Days 2 – 5",
  },
  {
    title: "Protection & cure",
    description:
      "Coatings applied, levelled and cured under infrared. Film cures for 48 hours before it is inspected.",
    duration: "Day 5",
  },
  {
    title: "Handover",
    description:
      "A walkaround under studio lighting, your warranty documents, an aftercare kit and a maintenance schedule.",
    duration: "Day 6",
  },
];

export const comparisons: ComparisonPair[] = [
  {
    id: "paint",
    title: "Two-stage correction",
    description:
      "Eleven years of automatic car washes had left the clear coat hazed with swirls. Two correction stages later the reflection is sharp enough to read.",
    vehicle: "Mercedes-AMG E63 S — Obsidian Black",
    before: "/media/compare/paint-before.svg",
    after: "/media/compare/paint-after.svg",
  },
  {
    id: "coupe",
    title: "Correction + 10-year coating",
    description:
      "Delivered new with dealer-inflicted wash marks across the flanks. Corrected, then coated so the finish survives the owner's weekly wash.",
    vehicle: "Porsche 911 GT3 — Jet Black Metallic",
    before: "/media/compare/coupe-before.svg",
    after: "/media/compare/coupe-after.svg",
  },
  {
    id: "suv",
    title: "Enhancement polish + PPF",
    description:
      "A daily-driven SUV with motorway chipping and oxidised flat panels. Corrected, filmed on the impact zones, then coated throughout.",
    vehicle: "Land Rover Defender 110 — Santorini Black",
    before: "/media/compare/suv-before.svg",
    after: "/media/compare/suv-after.svg",
  },
];

export const homeFaq: FaqItem[] = [
  {
    question: "How far in advance should I book?",
    answer:
      "Detailing work usually has availability within a week. Coating and film installations are scheduled two to three weeks out because the bay is held for the full job.",
  },
  {
    question: "Do you work on new cars straight from the dealer?",
    answer:
      "Frequently, and it is the ideal time. New paint still needs correction — transport film, dealer washes and lot storage leave marks that are much easier to remove before they set.",
  },
  {
    question: "Can I stay while the work is done?",
    answer:
      "You are welcome for the intake walkaround and the handover. During the work the bays are sealed and filtered, so viewing happens through the glass.",
  },
  {
    question: "What happens if I am not happy with the result?",
    answer:
      "Tell us at handover. We re-inspect together under studio lighting and, if the finish does not match the agreed scope, we put it back in the bay at our cost.",
  },
  {
    question: "Do you offer collection and delivery?",
    answer:
      "Yes, within Odessa and the surrounding region. Enclosed transport can be arranged for longer distances or for vehicles that should not be driven.",
  },
  {
    question: "Is the warranty transferable if I sell the car?",
    answer:
      "Coating warranties transfer to the new owner provided the annual inspection record is up to date. The service file goes with the vehicle.",
  },
];
