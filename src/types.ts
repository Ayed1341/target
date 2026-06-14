// Router Manager - Types Module
// Developer: عايد عريبي (Ayed Oraybi)

export interface RouterCredentials {
  ip: string;
  username: string;
  password: string;
  brand: "huawei" | "zte";
}

export interface RouterAuthResponse {
  success: boolean;
  token?: string;
  sessionId?: string;
  authMethod?: string;
  error?: string;
}

export interface SignalData {
  rsrp: number;
  rsrq: number;
  sinr: number;
  cellId: string;
  pci: number;
  band: string;
  earfcn: number;
  arfcn: number;
  dlFreq: number;
  ulFreq: number;
  bandwidth: string;
  networkType: string;
  mcc: string;
  mnc: string;
  lac: string;
  plmn: string;
  temperature: number;
  uplinkSpeed: number;
  downlinkSpeed: number;
  ca: CAInfo | null;
}

export interface CAInfo {
  enabled: boolean;
  primaryBand: string;
  secondaryBands: string[];
  aggregatedBandwidth: number;
}

export interface CellTower {
  cellId: string;
  pci: number;
  band: string;
  earfcn: number;
  rsrp: number;
  rsrq: number;
  sinr: number;
  distance?: number;
  isServing: boolean;
}

export interface BandInfo {
  bandNumber: number;
  name: string;
  dlFreqMHz: number;
  ulFreqMHz: number;
  bandwidth: string;
  technology: "LTE" | "NR";
  hexCode: string;
  isActive: boolean;
  isLocked: boolean;
  signalStrength?: number;
}

export interface SpeedTestResult {
  downloadMbps: number;
  uploadMbps: number;
  pingMs: number;
  jitterMs: number;
  timestamp: Date;
}

export interface SignalHistoryEntry {
  time: string;
  rsrp: number;
  rsrq: number;
  sinr: number;
  band: string;
}

export interface DiagnosticsReport {
  timestamp: string;
  routerIp: string;
  routerBrand: string;
  signalData: SignalData | null;
  connectedDevices: ConnectedDevice[];
  bandHistory: SignalHistoryEntry[];
  speedTest: SpeedTestResult | null;
  activeBands: string[];
  cellTowers: CellTower[];
}

export interface ConnectedDevice {
  ip: string;
  mac: string;
  hostname: string;
  connectionType: "wifi" | "lan" | "unknown";
  signalStrength?: number;
  leaseTime?: string;
}

export interface RouterFeature {
  id: number;
  title: string;
  category: "signal" | "bands" | "hardware" | "network" | "admin" | "tools";
  desc: string;
  technicalCommand: string;
  interfaceMethod: "GET" | "POST" | "AT_COMMAND" | "UNIFIED_API";
}

export interface SubnetClient {
  ip: string;
  mac: string;
  device: string;
  status: "safe" | "conflict";
  type: string;
}

export type AppTab =
  | "dashboard"
  | "bands"
  | "cells"
  | "signal"
  | "network"
  | "devices"
  | "speed"
  | "history"
  | "export"
  | "commands";
