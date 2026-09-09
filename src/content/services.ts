import type { Service, ServiceCategory } from "@/types";

export const categoryLabels: Record<ServiceCategory, string> = {
  protection: "Protection",
  ppf: "Paint Protection Film",
  correction: "Paint Correction",
  exterior: "Exterior",
  interior: "Interior",
  tinting: "Glass & Tinting",
};

export const services: Service[] = [
  {
    slug: "ceramic-coating",
    title: "Ceramic Coating",
    tagline: "Nine-layer SiO₂ protection",
    category: "protection",
    summary:
      "A cross-linked silica coating applied over corrected paint. Deeper gloss, chemical resistance and a surface that stays clean between washes.",
    intro: [
      "A ceramic coating is not a wax and it is not a substitute for correction. It is a semi-permanent layer of silicon dioxide that bonds to the clear coat and gives it a harder, slicker, far more chemically stable surface.",
      "Every coating we install starts with measurement. We read film build across the panel with a paint depth gauge, correct the defects the paint can safely give up, then decontaminate and panel-wipe before a single drop of product is applied.",
    ],
    priceFrom: 690,
    duration: "3 – 4 days",
    warranty: "Up to 10 years",
    image: "/media/service/ceramic-coating.svg",
    popular: true,
    highlights: ["9H hardness", "Hydrophobic surface", "UV & chemical resistance"],
    includes: [
      "Two-bucket decontamination wash and iron fallout removal",
      "Mechanical and chemical tar and fallout removal",
      "One to three-stage machine polish depending on package",
      "Paint depth measurement report on 24 points",
      "Coating applied to paint, glass, wheels and exhaust tips",
      "24-hour infrared curing in a sealed, filtered bay",
      "Aftercare kit and a maintenance schedule",
    ],
    benefits: [
      {
        title: "Gloss that survives washing",
        description:
          "The coating carries the reflection, not a sacrificial wax layer, so the finish you collect is the finish you keep for years.",
      },
      {
        title: "Chemical resistance",
        description:
          "Bird etching, tree sap, road salt and industrial fallout sit on top of the coating instead of attacking the clear coat.",
      },
      {
        title: "Half the wash time",
        description:
          "A hydrophobic surface releases dirt under low pressure. Most owners report contact washing takes around half as long.",
      },
      {
        title: "Documented warranty",
        description:
          "Registered with the manufacturer, backed by an annual inspection and a written service record for your vehicle.",
      },
    ],
    process: [
      {
        title: "Intake & paint reading",
        description:
          "Vehicle is photographed under inspection lighting and film build is measured across every panel.",
        duration: "2 h",
      },
      {
        title: "Decontamination",
        description: "Foam pre-wash, contact wash, iron dissolver, tar removal and mechanical clay.",
        duration: "4 h",
      },
      {
        title: "Correction",
        description: "Compounding and refining passes until defect removal targets are met on each panel.",
        duration: "1 – 2 days",
      },
      {
        title: "Coating & cure",
        description: "Panel wipe, coating application, levelling, then infrared cure in a sealed bay.",
        duration: "24 h",
      },
      {
        title: "Handover",
        description: "Inspection walkaround, warranty registration and aftercare briefing with the owner.",
        duration: "45 min",
      },
    ],
    faq: [
      {
        question: "Does a coating make the car scratch-proof?",
        answer:
          "No. A coating raises surface hardness and resists chemical etching, but it will not stop a stone chip or a careless wash mitt. For impact protection you want paint protection film.",
      },
      {
        question: "How long does the car stay with you?",
        answer:
          "Three to four days for a single-stage package, up to a week if the paint needs multi-stage correction. We agree the schedule before the car is booked in.",
      },
      {
        question: "How do I wash it afterwards?",
        answer:
          "pH-neutral shampoo, two-bucket method, no automatic brush washes. We supply the shampoo, a drying towel and written instructions at handover.",
      },
    ],
  },
  {
    slug: "paint-protection-film",
    title: "Paint Protection Film",
    tagline: "Self-healing urethane armour",
    category: "ppf",
    summary:
      "Optically clear urethane film cut to your vehicle and wrapped around the edges. Stops stone chips before they reach the clear coat.",
    intro: [
      "Paint protection film is a 190-micron thermoplastic urethane laminate with an elastomeric top coat. It absorbs impact energy that would otherwise chip your paint, and light swirls self-heal with heat.",
      "We install with wrapped edges wherever the panel allows, so there is no visible film line on the bonnet leading edge, the mirror caps or the door cups.",
    ],
    priceFrom: 1200,
    duration: "2 – 5 days",
    warranty: "10 years against yellowing",
    image: "/media/service/paint-protection-film.svg",
    popular: true,
    highlights: ["Self-healing top coat", "Wrapped edges", "Non-yellowing"],
    includes: [
      "Plotter-cut patterns verified against your exact model and trim",
      "Panel removal where required for wrapped edges",
      "Full decontamination and light polish before installation",
      "Installation in a filtered, positive-pressure bay",
      "Edge sealing and 48-hour cure",
      "Ceramic top coat over the film",
    ],
    benefits: [
      {
        title: "Impact absorption",
        description:
          "The urethane layer deforms and recovers, dispersing the energy of gravel strikes that would otherwise chip paint.",
      },
      {
        title: "Self-healing",
        description:
          "Fine wash marks disappear with sun exposure or warm water because the top coat returns to its moulded shape.",
      },
      {
        title: "Invisible when installed properly",
        description:
          "Wrapped edges, no stretched corners and no lifted seams. From two metres away you should not be able to tell it is there.",
      },
      {
        title: "Reversible",
        description:
          "Film can be removed by a trained installer without damaging factory paint, which matters at resale.",
      },
    ],
    process: [
      { title: "Coverage planning", description: "We walk the car with you and agree exactly which panels and edges are covered.", duration: "1 h" },
      { title: "Preparation", description: "Decontamination, light machine polish and solvent wipe of every bonding surface.", duration: "6 h" },
      { title: "Installation", description: "Patterns are laid, wrapped and squeegeed panel by panel with trim removed as needed.", duration: "1 – 3 days" },
      { title: "Cure & inspection", description: "48 hours of controlled cure, then an edge-by-edge inspection under raking light.", duration: "48 h" },
    ],
    faq: [
      {
        question: "Which panels should I cover first?",
        answer:
          "Front bumper, bonnet, front fenders, mirror caps and headlights take the vast majority of road damage. That package covers roughly 90% of typical chip locations.",
      },
      {
        question: "Will the film yellow?",
        answer:
          "The films we install are non-yellowing and carry a ten-year manufacturer warranty. Older PVC-based films yellowed; modern TPU does not.",
      },
      {
        question: "Can I coat over the film?",
        answer:
          "Yes, and we recommend it. A ceramic top coat over PPF adds slickness and makes bug and tar removal far easier.",
      },
    ],
  },
  {
    slug: "full-body-ppf",
    title: "Full Body PPF",
    tagline: "Every painted panel covered",
    category: "ppf",
    summary:
      "Complete film coverage on every painted surface, including door jambs where specified. The definitive protection package for a new or collector car.",
    intro: [
      "Full body coverage is the only way to keep a car's paint in delivery condition. Every painted panel is filmed, edges wrapped, and the finish is left visually indistinguishable from bare paint.",
      "This is a week of bench work. Bumpers come off, badges come off, lights come out where necessary. The result is a car with no visible film lines from any normal viewing angle.",
    ],
    priceFrom: 3400,
    duration: "5 – 7 days",
    warranty: "10 years against yellowing",
    image: "/media/service/full-body-ppf.svg",
    popular: true,
    highlights: ["Every painted panel", "Panels removed for wrapping", "Gloss or satin finish"],
    includes: [
      "Full disassembly of bumpers, lamps, handles and badges as required",
      "Multi-stage paint correction before installation",
      "Film on every painted exterior panel",
      "Wrapped edges on all accessible panel perimeters",
      "Ceramic coating over the entire film surface",
      "Photographic record of the installation for your file",
    ],
    benefits: [
      {
        title: "Resale value protected",
        description: "Factory paint stays factory. Removal at sale reveals a panel set with no chips and no swirl history.",
      },
      {
        title: "Uniform finish",
        description: "Because every panel is filmed, there is no gloss mismatch between covered and uncovered areas.",
      },
      {
        title: "Satin option",
        description: "A satin film changes the entire character of the car while still protecting it underneath.",
      },
      {
        title: "One shop, one warranty",
        description: "Prep, install and coating are done in-house, so there is a single point of accountability.",
      },
    ],
    process: [
      { title: "Booking & template check", description: "We verify plotter patterns against your VIN and order film in advance.", duration: "1 week ahead" },
      { title: "Disassembly", description: "Bumpers, lamps, handles, badges and trim are removed and logged.", duration: "1 day" },
      { title: "Correction", description: "Multi-stage polish so the paint under the film is finished, not merely clean.", duration: "1 – 2 days" },
      { title: "Installation", description: "Panel-by-panel install with wrapped edges, working from the roof down.", duration: "3 days" },
      { title: "Reassembly & cure", description: "Everything goes back with new clips where needed, then the film cures.", duration: "1 day" },
    ],
    faq: [
      {
        question: "Do you cover door jambs?",
        answer: "They can be covered on request. It adds roughly a day of labour and is most commonly requested on collector cars.",
      },
      {
        question: "How long before I can wash it?",
        answer: "Seven days. The adhesive continues to bond during the first week and edges should not be pressure-washed in that window.",
      },
      {
        question: "Can film be installed over repainted panels?",
        answer:
          "Only if the refinish is fully cured and properly adhered. We test suspicious panels and will tell you honestly if a panel is not a safe candidate.",
      },
    ],
  },
  {
    slug: "partial-ppf",
    title: "Partial PPF",
    tagline: "Coverage where the damage happens",
    category: "ppf",
    summary:
      "Targeted film on the panels that take road impact — front end, mirrors, door cups and sills. The efficient way to protect a daily driver.",
    intro: [
      "Most stone damage lands in a predictable set of places. Partial coverage puts film exactly there and leaves the rest of the car untouched, which keeps the cost proportionate to the risk.",
      "We offer three standard coverage sets and will happily build a custom one after walking the car with you.",
    ],
    priceFrom: 980,
    duration: "2 days",
    warranty: "10 years against yellowing",
    image: "/media/service/partial-ppf.svg",
    highlights: ["Front-end packages", "Door cups & sills", "Custom coverage maps"],
    includes: [
      "Front bumper, partial or full bonnet and front fenders",
      "Mirror caps and headlight units",
      "Door cup and door edge protection",
      "Rocker panel and loading-edge film where specified",
      "Decontamination and light polish of covered panels",
      "Edge sealing and inspection",
    ],
    benefits: [
      {
        title: "Right-sized investment",
        description: "You protect roughly 90% of typical chip locations for a fraction of full-body cost.",
      },
      {
        title: "Upgradeable",
        description: "Coverage can be extended later panel by panel without redoing the existing film.",
      },
      { title: "Fast turnaround", description: "Most partial packages are collected within two working days." },
      {
        title: "Pairs with coating",
        description: "Uncovered panels get a ceramic coating so the whole car behaves the same way in the wash.",
      },
    ],
    process: [
      { title: "Coverage walkaround", description: "We map the panels together and quote the exact set.", duration: "30 min" },
      { title: "Prep", description: "Decontamination and a light polish on the panels being covered.", duration: "3 h" },
      { title: "Install", description: "Patterns laid and wrapped, trim removed where an edge demands it.", duration: "1 day" },
      { title: "Cure & check", description: "Overnight cure followed by a raking-light inspection.", duration: "12 h" },
    ],
    faq: [
      {
        question: "Will I see the film line on the bonnet?",
        answer:
          "On a partial bonnet, yes — there is a horizontal transition. Many owners choose a full bonnet for that reason. We will show you both on a demo panel.",
      },
      {
        question: "Is partial film enough for motorway driving?",
        answer: "For chip protection, yes. Heavy motorway users often add the A-pillars and roof leading edge.",
      },
      {
        question: "Can I add a coating on top?",
        answer: "Yes. We coat the film and the remaining paint in the same visit so the car washes uniformly.",
      },
    ],
  },
  {
    slug: "paint-correction",
    title: "Paint Correction",
    tagline: "Measured defect removal",
    category: "correction",
    summary:
      "Machine polishing that removes swirls, holograms and oxidation from the clear coat, with paint depth measured before every pass.",
    intro: [
      "Correction is the difference between a clean car and a finished one. Swirl marks scatter light, which is why dark paint looks flat and grey in the sun even after a wash.",
      "We work to a target, not to exhaustion. Film build is measured, a test section establishes the least aggressive combination that hits the target, and we document what was removed.",
    ],
    priceFrom: 450,
    duration: "1 – 3 days",
    image: "/media/service/paint-correction.svg",
    popular: true,
    highlights: ["Depth-gauge measured", "Single to three-stage", "Documented results"],
    includes: [
      "Full decontamination wash and mechanical clay",
      "Paint depth measurement across 24 points",
      "Test-section calibration before full correction",
      "Compounding and refining passes as required",
      "Trim and glass masked, panel gaps taped",
      "IPA panel wipe and inspection under three light sources",
      "Protective sealant or coating upgrade at handover",
    ],
    benefits: [
      {
        title: "Depth returns",
        description: "Removing scatter lets the eye read the base coat again. Dark colours gain the most.",
      },
      {
        title: "Safe by measurement",
        description: "We know how much clear coat there is before we touch it, and we stop before the paint is compromised.",
      },
      {
        title: "The right base for coating",
        description: "A coating locks in whatever is underneath it — correction first is the only sensible order.",
      },
      {
        title: "Honest reporting",
        description: "If a panel cannot safely reach 100%, we say so and agree a realistic target with you.",
      },
    ],
    process: [
      { title: "Assessment", description: "Inspection under LED, halogen and natural light plus depth readings.", duration: "1 h" },
      { title: "Decontamination", description: "The paint is chemically and mechanically clean before any pad touches it.", duration: "4 h" },
      { title: "Test section", description: "We find the least aggressive pad and compound combination that hits the target.", duration: "45 min" },
      { title: "Correction passes", description: "Compounding then refining, panel by panel, checked between each stage.", duration: "1 – 3 days" },
      { title: "Protection", description: "The corrected finish is sealed or coated so it lasts.", duration: "3 h" },
    ],
    faq: [
      {
        question: "What is the difference between one, two and three stages?",
        answer:
          "Stages are correction passes. One stage lifts light swirls and adds gloss, two removes the majority of defects, three targets near-total removal on paint that can safely give it.",
      },
      {
        question: "Can every scratch be polished out?",
        answer:
          "Only defects inside the clear coat. If your fingernail catches in the scratch, it is likely through the clear and needs paint, not polish.",
      },
      {
        question: "How long will the result last?",
        answer:
          "The correction is permanent — the removed clear coat does not come back. How long it looks corrected depends on your wash habits and whether it is protected.",
      },
    ],
  },
  {
    slug: "interior-detailing",
    title: "Interior Detailing",
    tagline: "Deep clean, then protect",
    category: "interior",
    summary:
      "Full cabin extraction, steam sanitising and surface protection. Every trim, vent and seam brought back and sealed against wear.",
    intro: [
      "Interiors take the hardest daily use in the car and get the least attention. We strip the cabin back, clean every surface by the method that surface actually needs, then protect it.",
      "Seats out where required, carpets hot-water extracted, leather cleaned with pH-appropriate chemistry, plastics cleaned rather than dressed with silicone.",
    ],
    priceFrom: 260,
    duration: "6 – 10 hours",
    image: "/media/service/interior-detailing.svg",
    popular: true,
    highlights: ["Hot-water extraction", "Steam sanitising", "No greasy dressings"],
    includes: [
      "Complete removal of loose items and mats, logged and returned",
      "Compressed-air and vacuum pass through every seam and rail",
      "Hot-water extraction of carpets and fabric seats",
      "Steam sanitising of vents, switchgear and hard surfaces",
      "Leather cleaned and conditioned with pH-balanced products",
      "Glass cleaned inside including the top of the windscreen",
      "Fabric and leather protection applied",
    ],
    benefits: [
      { title: "Odour removed at the source", description: "Extraction and steam remove what causes odour rather than masking it with fragrance." },
      { title: "Matte, factory-correct finish", description: "No shine, no slippery steering wheel, no dashboard glare in the windscreen." },
      { title: "Protected against the next spill", description: "Fabric and leather sealants give you time to react before a stain sets." },
      { title: "Allergen reduction", description: "Deep extraction lifts dust and dander out of carpet fibres and headliner." },
    ],
    process: [
      { title: "Strip out", description: "Mats, seat rails and boot floor cleared; loose items bagged and labelled.", duration: "1 h" },
      { title: "Dry pass", description: "Compressed air and vacuum from headliner down through every seam.", duration: "1 h" },
      { title: "Wet work", description: "Extraction on fabric, controlled chemistry on leather and hard trim.", duration: "3 – 5 h" },
      { title: "Steam & detail", description: "Vents, switches, badges, seat rails and every hard-to-reach edge.", duration: "2 h" },
      { title: "Protect & dry", description: "Fabric and leather protection, forced-air dry, final glass.", duration: "2 h" },
    ],
    faq: [
      {
        question: "Will the car be wet when I collect it?",
        answer: "No. Everything is force-dried in a heated bay. If the weather makes drying slow we keep the car overnight rather than hand it back damp.",
      },
      { question: "Do you remove pet hair?", answer: "Yes, with rubber pile brushes and extraction. Heavy pet hair adds two to three hours and we will quote it after seeing the car." },
      {
        question: "Can you fix a cigarette smell?",
        answer:
          "Usually. It requires extraction, headliner treatment, cabin filter replacement and ozone. We assess first — long-term smoking in a light interior is not always fully reversible.",
      },
    ],
  },
  {
    slug: "exterior-detailing",
    title: "Exterior Detailing",
    tagline: "A properly finished wash",
    category: "exterior",
    summary:
      "Decontamination wash, wheel faces and barrels, glass, trim and a durable sealant. The maintenance standard between larger jobs.",
    intro: [
      "This is what a wash should be. Touchless pre-wash, contact wash with clean media, wheels done inside and out, and a sealant that actually lasts a season.",
      "It is also the right service to keep a coated or filmed car in condition between annual inspections.",
    ],
    priceFrom: 180,
    duration: "4 – 6 hours",
    image: "/media/service/exterior-detailing.svg",
    highlights: ["Touchless pre-wash", "Wheels off optional", "6-month sealant"],
    includes: [
      "Citrus pre-soak and snow foam dwell",
      "Wheel faces, barrels, arches and calipers",
      "Two-bucket contact wash with clean microfibre media",
      "Iron fallout removal and tar spotting",
      "Filtered deionised rinse and forced-air dry",
      "Glass polish and water-repellent treatment",
      "Trim restoration and durable paint sealant",
    ],
    benefits: [
      { title: "No new swirls", description: "Clean media, correct lubrication and a straight-line technique — the wash itself stops causing damage." },
      { title: "Wheels done properly", description: "Barrels and arches are where brake dust hides. We clean them, not just the faces." },
      { title: "Spot-free drying", description: "Deionised final rinse and filtered air means no mineral spotting on dark paint." },
      { title: "Season-long protection", description: "The sealant we use holds beading and gloss for roughly six months of daily use." },
    ],
    process: [
      { title: "Pre-wash", description: "Citrus pre-soak, snow foam dwell and a pressure rinse to remove loose grit.", duration: "45 min" },
      { title: "Wheels & arches", description: "Dedicated chemistry and brushes, faces and barrels, calipers included.", duration: "1 h" },
      { title: "Contact wash", description: "Two-bucket method with grit guards and fresh mitts per section.", duration: "1 h" },
      { title: "Decontaminate", description: "Iron fallout dissolver and tar removal, rinsed and dried.", duration: "1 h" },
      { title: "Protect", description: "Sealant, glass treatment, trim dressing and tyres.", duration: "1 – 2 h" },
    ],
    faq: [
      { question: "How often should I book this?", answer: "Every six to eight weeks for a daily driver, or twice a year on a coated car alongside your own maintenance washes." },
      { question: "Do you take the wheels off?", answer: "On request. Wheels-off cleaning adds about ninety minutes and is worth it once a year." },
      { question: "Is this enough before a coating?", answer: "It is the first half. A coating also needs correction — otherwise you seal the swirls in." },
    ],
  },
  {
    slug: "full-detailing",
    title: "Full Detailing",
    tagline: "Inside and out, in one booking",
    category: "exterior",
    summary:
      "Our complete reset: exterior decontamination and enhancement polish, plus a full interior deep clean and protection.",
    intro: [
      "The full detail combines our exterior and interior programmes into a single booking, with an enhancement polish that lifts gloss without a multi-day correction schedule.",
      "It is the service most owners choose before selling a car, after buying a used one, or once a year to reset the whole vehicle.",
    ],
    priceFrom: 540,
    duration: "1 – 2 days",
    image: "/media/service/full-detailing.svg",
    popular: true,
    highlights: ["Exterior + interior", "One-stage enhancement", "12-month protection"],
    includes: [
      "Everything in Exterior Detailing",
      "Everything in Interior Detailing",
      "Single-stage enhancement polish on all painted panels",
      "Engine bay clean and dress",
      "Door, boot and bonnet shuts cleaned and sealed",
      "12-month paint sealant or coating upgrade",
      "Pre-handover inspection under studio lighting",
    ],
    benefits: [
      { title: "One booking, one price", description: "No coordinating separate visits — the car goes in once and comes out finished." },
      { title: "Visible gloss gain", description: "The enhancement stage removes light swirling and adds noticeable depth to dark colours." },
      { title: "Sale-ready presentation", description: "Shuts, engine bay and jambs are done, which is exactly what buyers open first." },
      { title: "Upgrade path", description: "Add a ceramic coating at booking and we schedule the extra correction time up front." },
    ],
    process: [
      { title: "Intake", description: "Walkaround, photos and an agreed scope with the owner.", duration: "30 min" },
      { title: "Exterior programme", description: "Decontamination, wheels, enhancement polish and protection.", duration: "1 day" },
      { title: "Interior programme", description: "Extraction, steam, leather care and protection.", duration: "6 – 10 h" },
      { title: "Shuts & engine bay", description: "Jambs, hinges and the engine bay cleaned and lightly dressed.", duration: "2 h" },
      { title: "Final inspection", description: "Studio lighting check, then handover with aftercare notes.", duration: "45 min" },
    ],
    faq: [
      { question: "Is this the same as correction?", answer: "No. It includes a single enhancement stage. Full correction is a separate, longer service and can be added on." },
      { question: "Can you do it in one day?", answer: "On a small, well-kept car, yes. Larger or heavily used vehicles need two days for the interior to dry properly." },
      { question: "Do you clean the engine bay?", answer: "Yes — controlled steam and chemistry, sensitive components covered, and a matte dressing rather than a wet-look shine." },
    ],
  },
  {
    slug: "window-tinting",
    title: "Window Tinting",
    tagline: "Ceramic film, computer cut",
    category: "tinting",
    summary:
      "Nano-ceramic film that blocks heat and UV without blocking signal. Plotter-cut, heat-shrunk and installed with no visible edges.",
    intro: [
      "Cheap dyed film turns purple and cooks your interior anyway. Nano-ceramic film rejects infrared heat by construction, not by darkness, so you can run a legal shade and still feel the difference.",
      "Every window is plotter-cut to your model, heat-shrunk on the outside of the glass, then installed from the inside in a filtered bay.",
    ],
    priceFrom: 290,
    duration: "4 – 6 hours",
    warranty: "Lifetime against bubbling & fade",
    image: "/media/service/window-tinting.svg",
    highlights: ["99% UV rejection", "Signal-transparent", "Legal shades available"],
    includes: [
      "Consultation on legal shade limits for your vehicle",
      "Plotter-cut patterns for every window",
      "Deep glass cleaning and rubber seal preparation",
      "Heat-shrink forming on curved glass",
      "Installation in a filtered, dust-controlled bay",
      "Windscreen strip and sunroof film on request",
      "Care instructions and cure schedule",
    ],
    benefits: [
      { title: "Real heat rejection", description: "Ceramic film blocks the infrared band, which is what you actually feel on your arm in traffic." },
      { title: "Interior preservation", description: "99% UV rejection slows the fading and cracking that ruins leather and dashboards." },
      { title: "No signal interference", description: "Non-metallic construction leaves GPS, keyless entry and mobile signal untouched." },
      { title: "Glare control", description: "Noticeably easier night driving and less squinting into low winter sun." },
    ],
    process: [
      { title: "Shade selection", description: "We show samples on your own glass and confirm what is road-legal.", duration: "30 min" },
      { title: "Glass preparation", description: "Full clean, seal preparation and removal of any existing film.", duration: "1 – 2 h" },
      { title: "Shaping", description: "Film is heat-shrunk to the curvature of each window on the outside of the glass.", duration: "1 h" },
      { title: "Installation", description: "Applied from inside, squeegeed and edge-tucked under the seals.", duration: "2 h" },
      { title: "Cure", description: "Windows stay closed for 48 hours while the mounting solution evaporates.", duration: "48 h" },
    ],
    faq: [
      { question: "How dark can I legally go?", answer: "Limits differ by window and by country. We will tell you exactly what is permitted for your vehicle before we cut anything." },
      { question: "Why does it look hazy at first?", answer: "That is trapped mounting solution and it clears within a few days as the film cures. Do not roll the windows down for 48 hours." },
      { question: "Can you remove old film?", answer: "Yes. Removal, adhesive cleanup and rear-screen heating element care are quoted separately after inspection." },
    ],
  },
  {
    slug: "wheel-protection",
    title: "Wheel Protection",
    tagline: "Coated faces, barrels and calipers",
    category: "protection",
    summary:
      "Wheels off, cleaned inside and out, then coated with a high-temperature ceramic so brake dust rinses away instead of baking on.",
    intro: [
      "Wheels get the harshest treatment on the car: 200°C brake dust, road salt and aggressive cleaners. A high-temperature coating changes how that dust behaves.",
      "We remove all four wheels, clean and decontaminate faces and barrels, then coat both sides plus the calipers.",
    ],
    priceFrom: 220,
    duration: "1 day",
    warranty: "2 years",
    image: "/media/service/wheel-protection.svg",
    highlights: ["Wheels removed", "Barrels coated", "Caliper coating included"],
    includes: [
      "All four wheels removed and torqued to specification on refit",
      "Faces, barrels and inner rims decontaminated",
      "Iron fallout and tar removal",
      "Light machine polish on painted or diamond-cut faces",
      "High-temperature ceramic coating, faces and barrels",
      "Caliper cleaning and coating",
      "Arch liners cleaned and dressed",
    ],
    benefits: [
      { title: "Brake dust rinses off", description: "Coated wheels release baked dust under a pressure rinse instead of needing aggressive acids." },
      { title: "Barrel protection", description: "The inner barrel is where corrosion starts. Coating it is the difference between five years and fifteen." },
      { title: "Gentler chemistry forever", description: "Once coated, wheels only need pH-neutral shampoo, which protects the finish long term." },
      { title: "Calipers included", description: "Coated calipers stay legible and clean rather than turning brown after one winter." },
    ],
    process: [
      { title: "Removal", description: "Wheels off, hubs protected, TPMS handled with care.", duration: "45 min" },
      { title: "Deep clean", description: "Faces and barrels chemically and mechanically decontaminated.", duration: "3 h" },
      { title: "Polish", description: "Light machine polish where the finish allows it.", duration: "2 h" },
      { title: "Coat & cure", description: "High-temperature ceramic applied both sides, cured under lamps.", duration: "4 h" },
      { title: "Refit", description: "Torqued to manufacturer specification and re-checked before handover.", duration: "45 min" },
    ],
    faq: [
      { question: "Does this work on diamond-cut wheels?", answer: "Yes, and it is particularly worthwhile — diamond-cut lacquer is fragile and coating slows the corrosion that lifts it." },
      { question: "What about curb damage?", answer: "Coating does not repair kerb rash. We work with a refurbisher and can arrange repair before coating." },
      { question: "How do I clean them afterwards?", answer: "pH-neutral wheel shampoo and a soft brush. Avoid acidic cleaners entirely — they shorten the coating's life." },
    ],
  },
  {
    slug: "leather-protection",
    title: "Leather Protection",
    tagline: "Cleaned, fed and sealed",
    category: "interior",
    summary:
      "Deep leather cleaning followed by a breathable protective coating that resists dye transfer, body oils and UV cracking.",
    intro: [
      "Modern automotive leather is pigmented and finished, so it does not need feeding with grease — it needs the finish cleaned and then protected.",
      "We clean with pH-appropriate chemistry and soft brushes, then apply a breathable protective layer that stops denim dye transfer and slows the cracking that comes from UV and body oils.",
    ],
    priceFrom: 190,
    duration: "4 hours",
    warranty: "18 months",
    image: "/media/service/leather-protection.svg",
    highlights: ["Dye-transfer resistant", "Breathable coating", "Matte factory finish"],
    includes: [
      "Vacuum and compressed-air pass through all seams and perforations",
      "pH-appropriate leather cleaning with soft brush agitation",
      "Bolster and seat-entry focus where wear concentrates",
      "Steering wheel, gear selector and door cards included",
      "Breathable protective coating applied and levelled",
      "Matte, factory-correct finish with no slip",
    ],
    benefits: [
      { title: "No more blue bolsters", description: "The coating creates a barrier that stops denim dye migrating into light-coloured leather." },
      { title: "Slower ageing", description: "UV and body oils are what crack leather. A sealed surface slows both." },
      { title: "Easier cleaning", description: "Spills sit on the coating and wipe away instead of soaking into the finish." },
      { title: "Correct feel", description: "Matte and grippy, exactly as it left the factory — no greasy shine on the steering wheel." },
    ],
    process: [
      { title: "Assessment", description: "We check for wear-through, cracking and previous re-dye work before cleaning.", duration: "20 min" },
      { title: "Clean", description: "Controlled chemistry and soft brushes, seam by seam, perforations protected.", duration: "2 h" },
      { title: "Dry & inspect", description: "Forced-air dry and a second inspection under strong light.", duration: "30 min" },
      { title: "Protect", description: "Coating applied in thin layers, levelled and cured.", duration: "1 h" },
    ],
    faq: [
      { question: "Will it change the colour?", answer: "No. The coating is clear and matte. Cleaning often makes leather look darker simply because the surface is finally clean." },
      { question: "Can you repair cracks?", answer: "Light surface cracking can be improved. Structural cracking and wear-through need re-dye or retrim, which we can arrange." },
      { question: "Does it work on Alcantara?", answer: "Alcantara needs a different fabric-specific protector. We treat it in the same visit at no extra charge." },
    ],
  },
  {
    slug: "headlight-restoration",
    title: "Headlight Restoration",
    tagline: "Optical clarity, UV sealed",
    category: "exterior",
    summary:
      "Oxidised polycarbonate wet-sanded back to clarity and re-sealed with a UV-stable coating so the yellowing does not return in six months.",
    intro: [
      "Headlight lenses are polycarbonate with a factory UV hard coat. When that coat fails, the plastic underneath oxidises, scatters light and turns yellow.",
      "Polishing alone removes the damage but also removes what is left of the protection. The lens must be re-sealed, or it will be yellow again within a season.",
    ],
    priceFrom: 120,
    duration: "3 hours",
    warranty: "3 years",
    image: "/media/service/headlight-restoration.svg",
    highlights: ["Wet-sanded", "UV hard coat re-applied", "Measurable light output gain"],
    includes: [
      "Masking of surrounding paint and trim",
      "Progressive wet sanding from 800 to 3000 grit",
      "Machine polish to full optical clarity",
      "Solvent wipe and surface preparation",
      "UV-stable hard coat or ceramic seal applied",
      "Controlled cure and inspection",
    ],
    benefits: [
      { title: "Safer night driving", description: "A clear lens projects the beam pattern the designer intended instead of scattering it." },
      { title: "The car looks years younger", description: "Yellow lenses age a car faster than almost anything else visible from the front." },
      { title: "It stays clear", description: "The re-applied UV coat is what makes the repair last. Without it, oxidation returns quickly." },
      { title: "Cheaper than replacement", description: "A fraction of the cost of a modern LED or matrix headlight unit." },
    ],
    process: [
      { title: "Mask", description: "Surrounding paint, trim and seals fully protected.", duration: "20 min" },
      { title: "Sand", description: "Progressive wet sanding until oxidation and crazing are gone.", duration: "1 h" },
      { title: "Polish", description: "Machine refinement to full optical clarity.", duration: "45 min" },
      { title: "Seal & cure", description: "UV-stable coating applied and cured under controlled heat.", duration: "1 h" },
    ],
    faq: [
      { question: "How long does it last?", answer: "Three years on the coating we use, and we re-treat under warranty if it fails earlier." },
      { question: "Can you fix internal condensation?", answer: "That is a seal or vent failure inside the unit. Restoration will not fix it — the unit needs resealing, which we can quote separately." },
      { question: "What about cracked lenses?", answer: "Cracks cannot be sanded out. We will tell you at inspection if the unit needs replacement instead." },
    ],
  },
];

export const popularServices = services.filter((service) => service.popular);

export function getService(slug: string): Service | undefined {
  return services.find((service) => service.slug === slug);
}

export function getRelatedServices(slug: string, limit = 3): Service[] {
  const current = getService(slug);
  if (!current) return services.slice(0, limit);
  const sameCategory = services.filter(
    (service) => service.slug !== slug && service.category === current.category,
  );
  const rest = services.filter(
    (service) => service.slug !== slug && service.category !== current.category,
  );
  return [...sameCategory, ...rest].slice(0, limit);
}
