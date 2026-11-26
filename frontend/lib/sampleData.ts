import { ResearchResult } from "./types";

export const SAMPLE_RESEARCH_RESULT: ResearchResult = {
  query: "Best 13-14 inch lightweight laptops for engineering students in 2026",
  summary:
    "Cross-source analysis synthesized from technical teardowns, real-world battery endurance tests, and multi-core developer compiling benchmarks across NotebookCheck, The Verge, and AnandTech. Evaluated based on processor capability, thermal throttling, keyboard ergonomics for long coding sessions, port flexibility, and real-world battery longevity.",
  durationSeconds: 6.4,
  createdAt: "2026-11-26T18:30:00.000Z",
  criteria: [
    "Processor & Memory",
    "Battery Longevity",
    "Display & Portability",
    "Keyboard & Connectivity",
    "Price Range",
  ],
  items: [
    {
      id: "macbook-air-m3",
      name: "Apple MacBook Air 13\" (M3)",
      criteriaValues: {
        "Processor & Memory": "Apple M3 (8-core CPU, 10-core GPU), 16GB Unified RAM",
        "Battery Longevity": "15-18 hours real-world coding/web browsing",
        "Display & Portability": "13.6\" Liquid Retina 500 nits, 1.24 kg (2.73 lbs)",
        "Keyboard & Connectivity": "Magic Keyboard, 2x Thunderbolt 4 / USB4, MagSafe 3",
        "Price Range": "$1,099 - $1,299",
      },
      pros: [
        "Unmatched battery efficiency and completely silent fanless operation",
        "Industry-leading single-core compiler speed and snappy UNIX terminal environment",
        "Rigid, premium aluminum unibody build with exceptional longevity",
      ],
      cons: [
        "Limited to 2 external displays only with laptop lid closed",
        "Requires virtual machine or remote server for Windows-exclusive x86 CAD packages",
      ],
      url: "https://www.apple.com/macbook-air",
    },
    {
      id: "dell-xps-13",
      name: "Dell XPS 13 (Intel Core Ultra)",
      criteriaValues: {
        "Processor & Memory": "Intel Core Ultra 7 155H, 16GB LPDDR5x RAM",
        "Battery Longevity": "10-12 hours real-world endurance",
        "Display & Portability": "13.4\" FHD+ InfinityEdge 500 nits, 1.19 kg (2.62 lbs)",
        "Keyboard & Connectivity": "Capacitive touch function row, 2x Thunderbolt 4",
        "Price Range": "$1,149 - $1,399",
      },
      pros: [
        "Extremely compact footprint with virtually borderless InfinityEdge display",
        "Native x86/Windows compatibility for legacy engineering and simulation tools",
        "Bright 500-nit outdoor-readable display with excellent color accuracy",
      ],
      cons: [
        "Capacitive function keys lack physical feedback for IDE keyboard shortcuts",
        "No dedicated 3.5mm headphone jack or legacy USB-A ports",
      ],
      url: "https://www.dell.com/en-us/shop/dell-laptops/xps-13",
    },
    {
      id: "thinkpad-x1-carbon",
      name: "Lenovo ThinkPad X1 Carbon Gen 12",
      criteriaValues: {
        "Processor & Memory": "Intel Core Ultra 7 165U, 32GB LPDDR5x RAM",
        "Battery Longevity": "11-13 hours real-world endurance",
        "Display & Portability": "14.0\" 2.8K OLED 120Hz 400 nits, 1.12 kg (2.47 lbs)",
        "Keyboard & Connectivity": "Class-leading tactile keyboard, 2x TB4, 2x USB-A, HDMI 2.1",
        "Price Range": "$1,450 - $1,750",
      },
      pros: [
        "Best-in-class tactile keyboard feedback and legendary TrackPoint ergonomics",
        "Comprehensive port layout including full-size HDMI 2.1 and USB-A without dongles",
        "MIL-STD 810H certified carbon-fiber durability with ultralight 1.12 kg weight",
      ],
      cons: [
        "Higher price-to-specification ratio compared to consumer alternatives",
        "OLED display option consumes higher battery during bright white code editors",
      ],
      url: "https://www.lenovo.com/thinkpad/x1-carbon",
    },
  ],
  recommendation: {
    winner: "Apple MacBook Air 13\" (M3)",
    reasoning:
      "The MacBook Air M3 earns the top overall recommendation for engineering students due to its unbeatable combination of sustained battery life (easily surviving full days of campus lectures without a charger), silent thermal profile, and best-in-class single-threaded compilation performance on modern web/software dev stacks. For students whose engineering coursework mandates native x86 Windows CAD (such as SolidWorks or Autodesk Inventor), the Lenovo ThinkPad X1 Carbon Gen 12 is the definitive runner-up recommendation thanks to its superior ergonomics, full I/O port selection, and military-grade durability.",
    keyStrengths: [
      "16-hour real-world battery endurance eliminates charger anxiety on campus",
      "Fastest single-core compiling speed among sub-1.3kg ultrabooks",
      "Robust UNIX terminal shell environment out of the box",
    ],
    sourceLinks: [
      {
        title: "The Verge: M3 MacBook Air in-depth college developer review",
        url: "https://www.theverge.com/reviews/macbook-air-m3-review",
      },
      {
        title: "NotebookCheck: Dell XPS 13 thermal and battery endurance benchmarks",
        url: "https://www.notebookcheck.net/dell-xps-13-plus-analysis",
      },
      {
        title: "AnandTech: Lenovo ThinkPad X1 Carbon Gen 12 architecture review",
        url: "https://www.anandtech.com/show/thinkpad-x1-carbon-gen-12",
      },
    ],
  },
  sources: [
    {
      url: "https://www.theverge.com/reviews/macbook-air-m3-review",
      hostname: "theverge.com",
      status: "success",
      title: "The Verge - M3 MacBook Air Review",
    },
    {
      url: "https://www.notebookcheck.net/dell-xps-13-plus-analysis",
      hostname: "notebookcheck.net",
      status: "success",
      title: "NotebookCheck - Dell XPS Benchmarks",
    },
    {
      url: "https://www.anandtech.com/show/thinkpad-x1-carbon-gen-12",
      hostname: "anandtech.com",
      status: "success",
      title: "AnandTech - ThinkPad Architecture Review",
    },
  ],
};
