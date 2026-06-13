export interface DetectedObject {
  id: string;
  name: string;
  category: string;
  size: string;
  description: string;
  confidence: number;
  toolsFound: string[];
  hideCameraStatus: string; // e.g. "No Threat Detected", "Suspected Camera", "Metallic Shell", "Signal Emission"
  extraDetails: { key: string; value: string }[];
  scannedAt: string;
  source: "local_db" | "gemini_api" | "internet_fallback";
  imageUrl: string;
  boundingBox?: { x: number; y: number; w: number; h: number };
  
  // Extended localized fields
  weight?: string;
  brand?: string;
  modelNumber?: string;
  estimatedPrice?: string;
  buyLink?: string;
  translationResult?: {
    originalText: string;
    targetLang: string;
    translatedText: string;
  };
}

export type ScanCategory =
  | "Spy & Covert Gear"
  | "TV & Room Equipment"
  | "Objects & Tools"
  | "Animals & Creatures"
  | "Humans & Action"
  | "Auto Detect";

export interface PresetScenario {
  id: string;
  name: string;
  category: Exclude<ScanCategory, "Auto Detect">;
  size: string;
  description: string;
  confidence: number;
  toolsFound: string[];
  hideCameraStatus: string;
  extraDetails: { key: string; value: string }[];
  imageUrl: string; // Reference icon name or built-in canvas drawing helper
  boundingBox: { x: number; y: number; w: number; h: number };
}
