/**
 * Device fingerprinting utility for creating unique device identifiers
 * This creates a semi-persistent identifier based on browser characteristics
 */

export function generateDeviceId(): string {
  // Get browser characteristics
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  ctx!.textBaseline = "top";
  ctx!.font = "14px Arial";
  ctx!.fillText("Device fingerprint", 2, 2);
  const canvasFingerprint = canvas.toDataURL();

  const characteristics = [
    navigator.userAgent,
    navigator.language,
    screen.width + "x" + screen.height,
    screen.colorDepth,
    new Date().getTimezoneOffset(),
    navigator.platform,
    navigator.cookieEnabled,
    canvasFingerprint.slice(-50), // Last 50 chars of canvas fingerprint
  ];

  // Create a simple hash
  const fingerprint = characteristics.join("|");
  let hash = 0;
  for (let i = 0; i < fingerprint.length; i++) {
    const char = fingerprint.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash = hash & hash; // Convert to 32-bit integer
  }

  // Convert to positive hex string
  const deviceId = Math.abs(hash).toString(16);
  return `device_${deviceId}`;
}

export function getOrCreateDeviceId(): string {
  const storageKey = "eve_device_id";

  // Try to get existing device ID from localStorage
  let deviceId = localStorage.getItem(storageKey);

  if (!deviceId) {
    // Generate new device ID
    deviceId = generateDeviceId();
    localStorage.setItem(storageKey, deviceId);
  }

  return deviceId;
}

export function clearDeviceId(): void {
  localStorage.removeItem("eve_device_id");
}
