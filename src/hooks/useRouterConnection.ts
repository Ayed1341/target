/**
 * useRouterConnection - Advanced Router Connection Hook
 * Manages authentication, signal monitoring, and command routing
 * Developer: عايد عريبي (Ayed Oraybi)
 */

import { useState, useCallback, useRef, useEffect } from "react";
import {
  createRouterAPI,
  HuaweiRouterAPI,
  ZteRouterAPI,
  RouterAPI,
} from "../api/routerApi";
import {
  RouterCredentials,
  SignalData,
  ConnectedDevice,
  CellTower,
  BandInfo,
  SpeedTestResult,
  SignalHistoryEntry,
} from "../types";

export interface RouterConnectionState {
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;
  signalData: SignalData | null;
  connectedDevices: ConnectedDevice[];
  cellTowers: CellTower[];
  supportedBands: BandInfo[];
  signalHistory: SignalHistoryEntry[];
  lastSpeedTest: SpeedTestResult | null;
  lastUpdate: Date | null;
  deviceInfo: Record<string, string>;
  authMethod: string;
}

export function useRouterConnection() {
  const apiRef = useRef<RouterAPI | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [state, setState] = useState<RouterConnectionState>({
    isConnected: false,
    isLoading: false,
    error: null,
    signalData: null,
    connectedDevices: [],
    cellTowers: [],
    supportedBands: [],
    signalHistory: [],
    lastSpeedTest: null,
    lastUpdate: null,
    deviceInfo: {},
    authMethod: "",
  });

  const setPartial = (partial: Partial<RouterConnectionState>) =>
    setState((prev) => ({ ...prev, ...partial }));

  const connect = useCallback(async (credentials: RouterCredentials): Promise<boolean> => {
    setPartial({ isLoading: true, error: null });

    try {
      const api = createRouterAPI(credentials);
      const authResult = await api.authenticate();

      if (!authResult.success) {
        setPartial({ isLoading: false, error: authResult.error || "فشل الاتصال - تحقق من العنوان وكلمة المرور" });
        return false;
      }

      apiRef.current = api;

      // Fetch initial data in parallel
      const [signalData, devices, bands, deviceInfo] = await Promise.allSettled([
        api.getSignalMetrics(),
        api.getConnectedDevices(),
        api.getSupportedBands(),
        api.getDeviceInfo(),
      ]);

      const signal = signalData.status === "fulfilled" ? signalData.value : null;
      const devs = devices.status === "fulfilled" ? devices.value : [];
      const bds = bands.status === "fulfilled" ? bands.value : [];
      const info = deviceInfo.status === "fulfilled" ? deviceInfo.value : {};

      const histEntry: SignalHistoryEntry | null = signal
        ? {
            time: new Date().toLocaleTimeString("ar-EG"),
            rsrp: signal.rsrp,
            rsrq: signal.rsrq,
            sinr: signal.sinr,
            band: signal.band,
          }
        : null;

      setPartial({
        isConnected: true,
        isLoading: false,
        signalData: signal,
        connectedDevices: devs,
        supportedBands: bds,
        deviceInfo: info,
        signalHistory: histEntry ? [histEntry] : [],
        lastUpdate: new Date(),
        authMethod: authResult.authMethod || "unknown",
        error: null,
      });

      // Start polling
      startPolling();
      return true;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "حدث خطأ غير متوقع أثناء الاتصال";
      setPartial({ isLoading: false, error: msg });
      return false;
    }
  }, []);

  const startPolling = useCallback(() => {
    if (pollingRef.current) clearInterval(pollingRef.current);
    pollingRef.current = setInterval(async () => {
      if (!apiRef.current) return;
      try {
        const signal = await apiRef.current.getSignalMetrics();
        if (signal) {
          const histEntry: SignalHistoryEntry = {
            time: new Date().toLocaleTimeString("ar-EG"),
            rsrp: signal.rsrp,
            rsrq: signal.rsrq,
            sinr: signal.sinr,
            band: signal.band,
          };
          setState((prev) => ({
            ...prev,
            signalData: signal,
            lastUpdate: new Date(),
            signalHistory: [...prev.signalHistory.slice(-59), histEntry],
          }));
        }
      } catch {
        // ignore polling errors
      }
    }, 4000);
  }, []);

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);

  const disconnect = useCallback(() => {
    stopPolling();
    if (apiRef.current) {
      apiRef.current.disconnect();
      apiRef.current = null;
    }
    setState({
      isConnected: false,
      isLoading: false,
      error: null,
      signalData: null,
      connectedDevices: [],
      cellTowers: [],
      supportedBands: [],
      signalHistory: [],
      lastSpeedTest: null,
      lastUpdate: null,
      deviceInfo: {},
      authMethod: "",
    });
  }, [stopPolling]);

  const scanCellTowers = useCallback(async (): Promise<boolean> => {
    if (!apiRef.current) return false;
    setPartial({ isLoading: true });
    const towers = await apiRef.current.getCellTowers();
    setPartial({ cellTowers: towers, isLoading: false });
    return towers.length > 0;
  }, []);

  const refreshDevices = useCallback(async (): Promise<boolean> => {
    if (!apiRef.current) return false;
    setPartial({ isLoading: true });
    const devices = await apiRef.current.getConnectedDevices();
    setPartial({ connectedDevices: devices, isLoading: false });
    return true;
  }, []);

  const lockBand = useCallback(async (bandHex: string, is5g = false): Promise<boolean> => {
    if (!apiRef.current) return false;
    setPartial({ isLoading: true, error: null });
    const result = is5g
      ? await apiRef.current.lock5gBand(bandHex)
      : await apiRef.current.lockLteBand(bandHex);
    setPartial({ isLoading: false });
    return result;
  }, []);

  const lockCell = useCallback(async (pci: number, earfcn: number): Promise<boolean> => {
    if (!apiRef.current) return false;
    setPartial({ isLoading: true, error: null });
    const result = await apiRef.current.lockCell(pci, earfcn);
    setPartial({ isLoading: false });
    return result;
  }, []);

  const setNetworkMode = useCallback(
    async (mode: "4g_only" | "5g_nsa" | "5g_sa" | "auto"): Promise<boolean> => {
      if (!apiRef.current) return false;
      setPartial({ isLoading: true, error: null });
      const result = await apiRef.current.setNetworkMode(mode);
      setPartial({ isLoading: false });
      return result;
    },
    []
  );

  const setAntennaMode = useCallback(async (mode: "0" | "1" | "2"): Promise<boolean> => {
    if (!apiRef.current) return false;
    setPartial({ isLoading: true, error: null });
    const result = await apiRef.current.setAntennaMode(mode);
    setPartial({ isLoading: false });
    return result;
  }, []);

  const reboot = useCallback(async (): Promise<boolean> => {
    if (!apiRef.current) return false;
    setPartial({ isLoading: true, error: null });
    const result = await apiRef.current.reboot();
    if (result) {
      stopPolling();
      setPartial({ isLoading: false, isConnected: false });
    } else {
      setPartial({ isLoading: false });
    }
    return result;
  }, [stopPolling]);

  const runSpeedTest = useCallback(async (): Promise<SpeedTestResult | null> => {
    if (!apiRef.current) return null;
    setPartial({ isLoading: true, error: null });
    const result = await apiRef.current.runSpeedTest();
    setPartial({ lastSpeedTest: result, isLoading: false });
    return result;
  }, []);

  const findBestBand = useCallback(async (): Promise<BandInfo | null> => {
    if (!state.supportedBands.length) return null;
    const current = state.signalData;
    if (!current) return null;
    const activeBands = state.supportedBands.filter((b) => b.isActive);
    if (!activeBands.length) return state.supportedBands[0];
    // Return the band with highest frequency as heuristic for best speed
    return activeBands.sort((a, b) => b.dlFreqMHz - a.dlFreqMHz)[0];
  }, [state.supportedBands, state.signalData]);

  const unlockAllBands = useCallback(async (): Promise<boolean> => {
    if (!apiRef.current) return false;
    setPartial({ isLoading: true, error: null });
    const result = await (apiRef.current as any).unlockAllBands?.() ?? false;
    setPartial({ isLoading: false });
    return result;
  }, []);

  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, [stopPolling]);

  return {
    ...state,
    connect,
    disconnect,
    scanCellTowers,
    refreshDevices,
    lockBand,
    lockCell,
    setNetworkMode,
    setAntennaMode,
    reboot,
    runSpeedTest,
    findBestBand,
    unlockAllBands,
    startPolling,
    stopPolling,
  };
}
