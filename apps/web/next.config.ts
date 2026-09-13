import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // A phone on the same Wi-Fi opens the dev server by the computer's address.
  // Without this the dev server refuses its own scripts to that address, the
  // page draws but never hydrates, and every button on the phone is dead.
  // Private ranges only, and development only: it has no effect on a build.
  allowedDevOrigins: ["192.168.*.*", "10.*.*.*"],
};

export default nextConfig;
